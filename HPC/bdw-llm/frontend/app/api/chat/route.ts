import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export const maxDuration = 60;
export const dynamic = "force-dynamic";

const RESTARTING_MESSAGE =
  "Model is restarting, please wait... The 72B inference worker is cycling through its production window.";

function isConnectionFailure(message: string): boolean {
  return /(Errno 111|Connection refused|ECONNREFUSED|ETIMEDOUT|ENOTFOUND|fetch failed|socket hang up|Connection error to vLLM|upstream connect error|127\.0\.0\.1:8001)/i.test(
    message
  );
}

function restartingResponse(detail: string): NextResponse {
  return NextResponse.json(
    { error: RESTARTING_MESSAGE, detail: detail.slice(0, 500), retryable: true },
    { status: 503, headers: { "Retry-After": "15", "Cache-Control": "no-store" } }
  );
}

// Supabase client instance (server-only)
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
const supabase =
  supabaseUrl && supabaseKey
    ? createClient(supabaseUrl, supabaseKey, {
        auth: { persistSession: false },
      })
    : null;

/**
 * Generate a 384-dimensional dense vector embedding.
 * Queries Hugging Face Serverless API with fallback to deterministic unit vector.
 */
async function getQueryEmbedding(text: string): Promise<number[]> {
  const hfToken = process.env.HF_TOKEN || "";
  const hfEndpoints = [
    "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5/pipeline/feature-extraction",
    "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
    "https://api-inference.huggingface.co/pipeline/feature-extraction/BAAI/bge-small-en-v1.5",
  ];

  if (hfToken) {
    for (const url of hfEndpoints) {
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${hfToken}`,
            "Content-Type": "application/json",
            "x-wait-for-model": "true",
          },
          body: JSON.stringify({ inputs: text }),
          signal: AbortSignal.timeout(4000),
        });

        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            const vec = Array.isArray(data[0]) ? data[0] : data;
            if (vec.length === 384) {
              return vec;
            }
          }
        }
      } catch {
        // Fallback
      }
    }
  }

  return generateDeterministicEmbedding(text, 384);
}

function generateDeterministicEmbedding(text: string, dim = 384): number[] {
  const vec = new Array(dim).fill(0);
  const words = text.toLowerCase().split(/\s+/);
  for (let w = 0; w < words.length; w++) {
    const word = words[w];
    for (let i = 0; i < word.length; i++) {
      const code = word.charCodeAt(i);
      const idx1 = (code * 31 + i * 17 + w * 7) % dim;
      const idx2 = (code * 47 + i * 23 + w * 13) % dim;
      vec[idx1] += Math.sin(code + i);
      vec[idx2] += Math.cos(code - w);
    }
  }
  let norm = 0;
  for (let i = 0; i < dim; i++) {
    norm += vec[i] * vec[i];
  }
  norm = Math.sqrt(norm) || 1.0;
  return vec.map((v) => Number((v / norm).toFixed(6)));
}

/**
 * Knowledge Base lookup via Supabase match_documents RPC.
 */
async function searchKnowledgeBase(query: string): Promise<string> {
  if (!supabase) {
    return "Supabase client is not configured on server.";
  }

  try {
    const queryEmbedding = await getQueryEmbedding(query);
    const { data, error } = await supabase.rpc("match_documents", {
      query_embedding: queryEmbedding,
      match_threshold: 0.0,
      match_count: 3,
    });

    if (error) {
      return `Knowledge base query error: ${error.message}`;
    }

    if (!data || data.length === 0) {
      return "No matching reference documents found in BDW knowledge base.";
    }

    return data
      .map(
        (
          doc: { content: string; similarity: number; metadata: unknown },
          idx: number
        ) =>
          `[Source ${idx + 1} (Score: ${(doc.similarity || 0).toFixed(3)})]:\n${doc.content}`
      )
      .join("\n\n");
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return `Failed retrieving knowledge chunks: ${msg}`;
  }
}

interface ChatMessage {
  role: string;
  content: string;
}

interface UpstreamPayload {
  messages: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  [key: string]: unknown;
}

function isChatMessage(value: unknown): value is ChatMessage {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.role === "string" && typeof candidate.content === "string";
}

/**
 * Call upstream inference gateway with cluster target model resolution.
 */
async function callUpstreamGateway(
  payload: UpstreamPayload,
  stream: boolean
): Promise<Response> {
  const primaryUrl =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://ai.berojgardegreewala.app/v1/chat/completions";
  const apiKey = process.env.BDW_API_KEY || "";

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
  };
  if (apiKey) {
    headers["Authorization"] = `Bearer ${apiKey}`;
  }

  // 1. Resolve target model and endpoint
  let targetModel = payload.model || "Qwen/Qwen2.5-72B-Instruct";
  let endpoint = primaryUrl;

  if (payload.model === "bdw-7b-sft" || payload.model === "bdw-7b-kaggle") {
    targetModel = "bdw-7b-sft";
    const kaggleBase = (process.env.KAGGLE_AI_BASE_URL || "").replace(/\/+$/, "");
    if (kaggleBase) {
      endpoint = `${kaggleBase}/chat/completions`;
    }
    const kaggleKey = process.env.KAGGLE_AI_API_KEY;
    if (kaggleKey) {
      headers["Authorization"] = `Bearer ${kaggleKey}`;
    }
  } else if (!payload.model || payload.model === "Qwen/Qwen2.5-72B-Instruct") {
    try {
      const modelsUrl = primaryUrl.replace(/\/chat\/completions\/?$/, "/models");
      const mRes = await fetch(modelsUrl, {
        headers,
        signal: AbortSignal.timeout(8000),
      });
      if (mRes.ok) {
        const mData = (await mRes.json()) as { data?: Array<{ id?: string }> };
        if (mData.data?.[0]?.id) {
          targetModel = mData.data[0].id;
        }
      }
    } catch {
      // Default to known cluster snapshot path
      targetModel =
        "/home/tutor/3ioip3lt/.cache/huggingface/hub/models--Qwen--Qwen2.5-72B-Instruct/snapshots/495f39366efef23836d0cfae4fbe635880d2be31";
    }
  }

  const res = await fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify({ ...payload, model: targetModel, stream }),
    signal: AbortSignal.timeout(58000),
  });

  return res;
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as Record<string, unknown>;
    const rawMessages = body.messages;
    const model = typeof body.model === "string" ? body.model : undefined;
    const temperature = typeof body.temperature === "number" ? body.temperature : 0.1;
    const max_tokens = typeof body.max_tokens === "number" ? body.max_tokens : 512;
    const stream = Boolean(body.stream);

    if (!Array.isArray(rawMessages)) {
      return NextResponse.json(
        { error: "Invalid request: 'messages' must be an array." },
        { status: 400 }
      );
    }

    const messages = rawMessages.filter(isChatMessage);
    if (messages.length === 0) {
      return NextResponse.json(
        { error: "Invalid request: no valid chat messages supplied." },
        { status: 400 }
      );
    }

    const lastUserMsg = [...messages].reverse().find((message) => message.role === "user");
    const userQuery = lastUserMsg?.content || "";

    // Step 1: Detect if knowledge base RAG retrieval is required
    const isKnowledgeQuery =
      /bdw|berojgardegreewala|knowledge|zero-3|deepspeed|static memory|timing analysis|setup time|hold time|param rudra|cdac|isro|drdo|csir|semiconductor|vlsi|70b/i.test(
        userQuery
      );

    let augmentedMessages: ChatMessage[] = [...messages];

    // If query matches knowledge domain, perform fast Supabase vector RAG search
    if (isKnowledgeQuery && supabase) {
      const ragResults = await searchKnowledgeBase(userQuery);
      const ragContextMessage = {
        role: "system",
        content:
          "You are BerojgarDegreeWala AI, India's deep-tech hardware career and research intelligence model.\n" +
          `[Authoritative BDW Knowledge Base Context]:\n${ragResults}\n\n` +
          "Synthesize the answer accurately incorporating the verified facts above. Provide rigorous mathematical reasoning where applicable.",
      };

      augmentedMessages = [
        ragContextMessage,
        ...messages.filter((message) => message.role !== "system"),
      ];
    }

    // Step 2: Call upstream cluster gateway endpoint
    let upstreamRes: Response;
    try {
      upstreamRes = await callUpstreamGateway(
        {
          messages: augmentedMessages,
          model,
          temperature,
          max_tokens,
        },
        stream
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (isConnectionFailure(msg)) {
        return restartingResponse(msg);
      }
      return NextResponse.json(
        {
          error: `BDW Cluster Gateway error: ${msg}`,
        },
        { status: 503 }
      );
    }

    if (!upstreamRes.ok) {
      const errText = await upstreamRes.text();
      const warmingUp =
        isConnectionFailure(errText) || [502, 503, 504].includes(upstreamRes.status);
      if (warmingUp) {
        return restartingResponse(errText);
      }
      return NextResponse.json(
        { error: `Upstream gateway error (${upstreamRes.status}): ${errText}` },
        { status: upstreamRes.status }
      );
    }

    // Step 3: Return stream or JSON response
    if (stream && upstreamRes.body) {
      return new Response(upstreamRes.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          Connection: "keep-alive",
        },
      });
    }

    const data = await upstreamRes.json();
    return NextResponse.json(data);
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Internal server proxy error";
    if (isConnectionFailure(message)) {
      return restartingResponse(message);
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
