"use client";

import React, { useEffect, useRef, useState } from "react";

type BackendState = "online" | "restarting";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  isError?: boolean;
  errorDetail?: string;
  retryText?: string;
}

interface ParsedContent {
  hasThink: boolean;
  thinkText: string;
  hasTool: boolean;
  toolText: string;
  answerText: string;
}

const QUICK_PROMPTS = [
  {
    title: "Setup timing slack",
    category: "VLSI",
    prompt:
      "Calculate setup timing slack for T_clk=1.25ns, T_skew=0.08ns, T_cq=0.15ns, T_comb=0.85ns, T_setup=0.12ns",
  },
  {
    title: "CMOS dynamic power",
    category: "Low power",
    prompt:
      "Compute dynamic CMOS power for 45 pF switched capacitance at 1.8 GHz with Vdd=0.85V",
  },
  {
    title: "Interconnect delay",
    category: "Units",
    prompt: "Convert an interconnect wire delay of 450 picoseconds into nanoseconds",
  },
  {
    title: "ZeRO-3 memory budget",
    category: "HPC",
    prompt:
      "What is the static memory required per GPU for a 70B model sharded with DeepSpeed ZeRO-3 across 32 GPUs?",
  },
];

const CAPABILITIES = [
  { icon: "brain" as const, title: "Hybrid reasoning", detail: "Visible think traces" },
  { icon: "tool" as const, title: "Tool execution", detail: "Calculators + unit conversions" },
  { icon: "database" as const, title: "RAG memory", detail: "43,469 study chunks" },
  { icon: "cpu" as const, title: "72B frontier", detail: "A100 production worker" },
];

function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function makeWelcome(): Message {
  return {
    id: "welcome-1",
    role: "assistant",
    content:
      "<think>\n1. System initialization complete.\n2. Connected to BDW-72B with hybrid reasoning and tool execution.\n3. Ready for VLSI timing, hardware sizing, power, and research queries.\n</think>\n\nWelcome to **BerojgarDegreeWala AI** — a deep-tech hardware and research intelligence console.\n\nAsk about static timing analysis, semiconductor physics, supercomputing clusters, or mathematical modeling.",
    timestamp: "Ready",
  };
}

function parseAssistantMessage(raw: string): ParsedContent {
  let content = raw;
  let hasThink = false;
  let thinkText = "";
  let hasTool = false;
  let toolText = "";

  const thinkRegex = /<think>([\s\S]*?)(?:<\/think>|$)/i;
  const thinkMatch = content.match(thinkRegex);
  if (thinkMatch) {
    hasThink = true;
    thinkText = thinkMatch[1].trim();
    content = content.replace(thinkRegex, "").trim();
  }

  const toolRegex = /<tool_call>([\s\S]*?)(?:<\/tool_call>|$)/i;
  const toolMatch = content.match(toolRegex);
  if (toolMatch) {
    hasTool = true;
    toolText = toolMatch[1].trim();
    content = content.replace(toolRegex, "").trim();
  }

  content = content
    .replace(/<\|im_end\|>/g, "")
    .replace(/<\/?think>/gi, "")
    .replace(/<\/?tool_call>/gi, "")
    .trim();

  return { hasThink, thinkText, hasTool, toolText, answerText: content };
}

function toolLabel(raw: string) {
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed?.name === "string") return parsed.name;
    if (typeof parsed?.tool === "string") return parsed.tool;
  } catch {
    const match = raw.match(/"name"\s*:\s*"([^"]+)"/);
    if (match?.[1]) return match[1];
  }
  return "tool_call";
}

function isConnectionIssue(message: string) {
  return /(Errno 111|Connection refused|ECONNREFUSED|ETIMEDOUT|fetch failed|socket hang up|127\.0\.0\.1:8001|Model is restarting|Upstream gateway error \(5\d\d\))/i.test(
    message
  );
}

function renderInline(text: string, keyPrefix: string) {
  const tokens = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return tokens.map((token, index) => {
    const key = `${keyPrefix}-${index}`;
    if (token.startsWith("**") && token.endsWith("**")) {
      return (
        <strong key={key} className="font-semibold text-slate-950">
          {token.slice(2, -2)}
        </strong>
      );
    }
    if (token.startsWith("`") && token.endsWith("`")) {
      return (
        <code
          key={key}
          className="rounded-md border border-slate-200 bg-slate-100 px-1.5 py-0.5 font-mono text-[0.82em] text-slate-800"
        >
          {token.slice(1, -1)}
        </code>
      );
    }
    return <React.Fragment key={key}>{token}</React.Fragment>;
  });
}

function RichText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="space-y-1.5">
      {lines.map((line, index) => {
        const key = `line-${index}`;
        if (!line.trim()) return <div key={key} className="h-1" />;

        const bullet = line.match(/^\s*[-*]\s+(.*)$/);
        if (bullet) {
          return (
            <div key={key} className="flex gap-2">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
              <span>{renderInline(bullet[1], key)}</span>
            </div>
          );
        }

        const numbered = line.match(/^\s*(\d+)\.\s+(.*)$/);
        if (numbered) {
          return (
            <div key={key} className="flex gap-2">
              <span className="shrink-0 tabular-nums text-slate-400">{numbered[1]}.</span>
              <span>{renderInline(numbered[2], key)}</span>
            </div>
          );
        }

        return <p key={key}>{renderInline(line, key)}</p>;
      })}
    </div>
  );
}

async function consumeStream(
  response: Response,
  onDelta: (content: string) => void
): Promise<string> {
  if (!response.body) return "";

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let accumulated = "";
  let finished = false;

  const processLine = (line: string) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith(":")) return;

    if (trimmed.startsWith("data:")) {
      const payload = trimmed.slice(5).trim();
      if (payload === "[DONE]") {
        finished = true;
        return;
      }
      try {
        const parsed = JSON.parse(payload);
        const delta = parsed.choices?.[0]?.delta?.content ?? "";
        if (delta) {
          accumulated += delta;
          onDelta(accumulated);
        }
      } catch {
        // A partial SSE frame can appear across reads; the next read completes it.
      }
      return;
    }

    try {
      const parsed = JSON.parse(trimmed);
      const text = parsed.choices?.[0]?.message?.content ?? parsed.content ?? "";
      if (text) {
        accumulated = text;
        onDelta(accumulated);
      }
    } catch {
      // Ignore non-JSON keepalive frames.
    }
  };

  while (!finished) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() ?? "";
    for (const line of lines) processLine(line);
  }

  if (buffer.trim()) processLine(buffer);
  return accumulated;
}

function Icon({
  name,
  className = "h-4 w-4",
}: {
  name:
    | "spark"
    | "brain"
    | "tool"
    | "send"
    | "plus"
    | "trash"
    | "chevron"
    | "alert"
    | "copy"
    | "check"
    | "database"
    | "cpu"
    | "chat";
  className?: string;
}) {
  const paths: Record<string, React.ReactNode> = {
    spark: (
      <>
        <path d="M12 3v3M12 18v3M4.2 7.5l2.6 1.5M17.2 15l2.6 1.5M4.2 16.5l2.6-1.5M17.2 9l2.6-1.5" />
        <circle cx="12" cy="12" r="3.5" />
      </>
    ),
    brain: (
      <>
        <path d="M9.5 4.5a3 3 0 0 0-3 3 3 3 0 0 0-1.5 5.6 3 3 0 0 0 3 5.4h1.5" />
        <path d="M14.5 4.5a3 3 0 0 1 3 3 3 3 0 0 1 1.5 5.6 3 3 0 0 1-3 5.4h-1.5" />
        <path d="M9.5 4.5v15M14.5 4.5v15M7 9.5h2.5M14.5 9.5H17M7 14.5h2.5M14.5 14.5H17" />
      </>
    ),
    tool: (
      <path d="M14.7 6.3a4 4 0 0 0-5 5L4 17l3 3 5.7-5.7a4 4 0 0 0 5-5l-2.4 2.4-2.6-2.6 2.4-2.4Z" />
    ),
    send: (
      <>
        <path d="M22 2 11 13" />
        <path d="M22 2 15 22l-4-9-9-4 20-7Z" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    trash: (
      <>
        <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v5M14 11v5" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    alert: (
      <>
        <path d="M12 9v4M12 17h.01" />
        <path d="M10.3 3.6 2.5 17a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z" />
      </>
    ),
    copy: (
      <>
        <rect x="9" y="9" width="12" height="12" rx="2" />
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
      </>
    ),
    check: <path d="m20 6-11 11-5-5" />,
    database: (
      <>
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
      </>
    ),
    cpu: (
      <>
        <rect x="6" y="6" width="12" height="12" rx="2" />
        <path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3M10 10h4v4h-4z" />
      </>
    ),
    chat: <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z" />,
  };

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

function StatusPill({ state, model }: { state: BackendState; model: string }) {
  const online = state === "online";
  const isKaggle = model === "bdw-7b-sft";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium ${
        online
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-amber-200 bg-amber-50 text-amber-700"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          online ? "bg-emerald-500" : "animate-pulse bg-amber-500"
        }`}
      />
      {isKaggle ? "7B Kaggle active" : (online ? "72B online" : "Model restarting")}
    </span>
  );
}

function Avatar({ role }: { role: "user" | "assistant" }) {
  if (role === "user") {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-200 text-[9px] font-bold uppercase tracking-wide text-slate-600">
        You
      </div>
    );
  }
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-800 text-[9px] font-bold tracking-wide text-white shadow-sm">
      BDW
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(() => [makeWelcome()]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendState, setBackendState] = useState<BackendState>("online");
  const [selectedModel, setSelectedModel] = useState<string>("bdw-7b-sft");
  const [expandedThinks, setExpandedThinks] = useState<Record<string, boolean>>({
    "welcome-1": true,
  });
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const idCounterRef = useRef(0);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "0px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, [input]);

  const toggleThink = (id: string) => {
    setExpandedThinks((previous) => ({ ...previous, [id]: !previous[id] }));
  };

  const newChat = () => {
    if (isLoading) return;
    setMessages([makeWelcome()]);
    setExpandedThinks({ "welcome-1": true });
    setInput("");
    setBackendState("online");
  };

  const copyAnswer = async (message: Message) => {
    const parsed = parseAssistantMessage(message.content);
    const text = parsed.answerText || parsed.thinkText || message.content;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(message.id);
      window.setTimeout(() => setCopiedId(null), 1600);
    } catch {
      // Clipboard access can be blocked by browser permissions.
    }
  };

  const streamCompletion = async (
    history: Message[],
    assistantId: string,
    retryText: string
  ) => {
    const apiMessages = history
      .filter((message) => message.role !== "system" && !message.isError)
      .map((message) => ({ role: message.role, content: message.content }));

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: apiMessages,
          model: selectedModel,
          temperature: 0.1,
          max_tokens: 512,
          stream: true,
        }),
      });

      if (!response.ok) {
        const raw = await response.text();
        let detail = raw;
        try {
          const parsed = JSON.parse(raw);
          detail = parsed.error || parsed.detail || raw;
        } catch {
          // Keep the raw upstream body.
        }
        throw new Error(detail || `Request failed with status ${response.status}`);
      }

      const content = await consumeStream(response, (accumulated) => {
        setMessages((previous) =>
          previous.map((message) =>
            message.id === assistantId ? { ...message, content: accumulated } : message
          )
        );
      });

      if (!content.trim()) {
        throw new Error("The model returned an empty response while warming up.");
      }

      setBackendState("online");
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : "Network error";
      const connectionIssue = isConnectionIssue(detail);
      setBackendState(connectionIssue ? "restarting" : "online");
      setMessages((previous) =>
        previous.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                isError: true,
                errorDetail: detail,
                retryText,
                content: connectionIssue
                  ? (selectedModel === "bdw-7b-sft"
                      ? "The Kaggle 7B inference worker is warming up or connecting. Ensure kaggle_backend.ipynb is running on Kaggle."
                      : "The 72B inference worker is cycling through its production window. Your message is still here — retry in a few seconds.")
                  : detail,
              }
            : message
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend ?? input).trim();
    if (!query || isLoading) return;

    idCounterRef.current += 1;
    const userMessage: Message = {
      id: `user-${idCounterRef.current}`,
      role: "user",
      content: query,
      timestamp: now(),
    };
    idCounterRef.current += 1;
    const assistantId = `assistant-${idCounterRef.current}`;
    const placeholder: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: now(),
    };
    const history = [...messages, userMessage];

    setMessages([...history, placeholder]);
    setExpandedThinks((previous) => ({ ...previous, [assistantId]: true }));
    setInput("");
    setIsLoading(true);
    await streamCompletion(history, assistantId, query);
  };

  const retryMessage = async (message: Message) => {
    if (isLoading || !message.retryText) return;
    const history = messages.filter((entry) => !entry.isError);
    idCounterRef.current += 1;
    const assistantId = `assistant-${idCounterRef.current}`;
    const placeholder: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: now(),
    };

    setMessages([...history, placeholder]);
    setExpandedThinks((previous) => ({ ...previous, [assistantId]: true }));
    setIsLoading(true);
    await streamCompletion(history, assistantId, message.retryText);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="flex h-dvh overflow-hidden bg-slate-50 text-slate-950">
      <aside className="hidden w-72 shrink-0 flex-col border-r border-slate-800/60 bg-slate-950 text-slate-200 lg:flex">
        <div className="border-b border-white/10 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 text-xs font-black tracking-tight text-white shadow-lg shadow-indigo-500/20">
              BDW
            </div>
            <div>
              <p className="text-sm font-semibold tracking-tight text-white">BerojgarDegreeWala</p>
              <p className="text-[10px] uppercase tracking-[0.22em] text-slate-500">AI console</p>
            </div>
          </div>
          <button
            onClick={newChat}
            disabled={isLoading}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-3 py-2.5 text-xs font-semibold text-slate-950 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Icon name="plus" className="h-3.5 w-3.5" />
            New conversation
          </button>
        </div>

        <div className="thin-scrollbar flex-1 space-y-6 overflow-y-auto p-5">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
              Capabilities
            </p>
            <div className="mt-3 space-y-1">
              {CAPABILITIES.map((item) => (
                <div
                  key={item.title}
                  className="flex items-center gap-3 rounded-xl px-2.5 py-2 text-slate-300 transition hover:bg-white/[0.04]"
                >
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-indigo-300">
                    <Icon name={item.icon} className="h-3.5 w-3.5" />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-xs font-medium text-slate-200">{item.title}</span>
                    <span className="block text-[10px] text-slate-500">{item.detail}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
              Quick starts
            </p>
            <div className="mt-3 space-y-2">
              {QUICK_PROMPTS.map((item) => (
                <button
                  key={item.title}
                  onClick={() => void handleSend(item.prompt)}
                  disabled={isLoading}
                  className="group w-full rounded-xl border border-white/[0.06] bg-white/[0.03] p-3 text-left transition hover:border-indigo-400/30 hover:bg-indigo-400/[0.06] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <span className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-slate-200 group-hover:text-white">
                      {item.title}
                    </span>
                    <span className="rounded-full border border-white/10 px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-slate-500">
                      {item.category}
                    </span>
                  </span>
                  <span className="mt-1 line-clamp-2 text-[10px] leading-relaxed text-slate-500">
                    {item.prompt}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 p-5">
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-medium text-slate-300">Inference backend</span>
              <span
                className={`h-2 w-2 rounded-full ${
                  backendState === "online"
                    ? "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.5)]"
                    : "animate-pulse bg-amber-400"
                }`}
              />
            </div>
            <p className="mt-1.5 text-[10px] leading-relaxed text-slate-500">
              {selectedModel === "bdw-7b-sft"
                ? "BerojgarDegreeWala Custom 7B · Kaggle GPU"
                : backendState === "online"
                ? "Qwen2.5-72B · hardware LoRA adapter"
                : "Slurm worker cycling · retry shortly"}
            </p>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
              <div
                className={`h-full rounded-full transition-all ${
                  backendState === "online"
                    ? "w-full bg-emerald-400"
                    : "w-1/3 animate-pulse bg-amber-400"
                }`}
              />
            </div>
          </div>
          <p className="mt-4 text-[10px] text-slate-600">
            Zero-cost cluster inference · A100 80GB
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200/80 bg-white/85 px-4 backdrop-blur-md lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 text-[10px] font-black text-white lg:hidden">
              BDW
            </div>
            <div>
              <p className="hidden text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400 lg:block">
                Workspace
              </p>
              <h1 className="text-sm font-semibold tracking-tight text-slate-950">AI console</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-700 shadow-sm transition hover:border-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              aria-label="Select Model"
            >
              <option value="bdw-7b-sft">BerojgarDegreeWala Custom 7B (Kaggle)</option>
              <option value="Qwen/Qwen2.5-72B-Instruct">BDW Sovereign 72B (Param Rudra)</option>
            </select>
            <StatusPill state={backendState} model={selectedModel} />
            <button
              onClick={newChat}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[10px] font-medium text-slate-500 transition hover:border-slate-300 hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Icon name="trash" className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Clear</span>
            </button>
          </div>
        </header>

        <main className="chat-canvas relative flex-1 overflow-y-auto">
          <div className="relative mx-auto w-full max-w-3xl space-y-7 px-4 py-6 lg:px-8 lg:py-10">
            {messages.map((message) => {
              const isUser = message.role === "user";
              const parsed = isUser ? null : parseAssistantMessage(message.content);
              const isExpanded = expandedThinks[message.id] ?? false;
              const connectionIssue = message.isError
                ? isConnectionIssue(message.errorDetail ?? message.content)
                : false;

              if (isUser) {
                return (
                  <div key={message.id} className="message-in flex items-start justify-end gap-3">
                    <div className="max-w-[85%]">
                      <div className="rounded-2xl rounded-tr-md bg-slate-950 px-5 py-3.5 text-sm leading-relaxed text-white shadow-lg shadow-slate-950/10">
                        <RichText text={message.content} />
                      </div>
                      <div className="mt-1.5 flex justify-end text-[10px] text-slate-400">
                        {message.timestamp}
                      </div>
                    </div>
                    <Avatar role="user" />
                  </div>
                );
              }

              if (!parsed) return null;

              return (
                <div key={message.id} className="message-in flex items-start gap-3">
                  <Avatar role="assistant" />
                  <div className="min-w-0 flex-1">
                    <div
                      className={`rounded-2xl border bg-white/95 p-4 shadow-sm lg:p-5 ${
                        message.isError ? "border-rose-200" : "border-slate-200/80"
                      }`}
                    >
                      {message.isError ? (
                        <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-4">
                          <div className="flex gap-3">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600">
                              <Icon name="alert" className="h-4 w-4" />
                            </span>
                            <div className="min-w-0">
                              <p className="text-sm font-semibold text-rose-950">
                                {connectionIssue
                                  ? "Model is restarting, please wait..."
                                  : "Request could not be completed"}
                              </p>
                              <p className="mt-1 text-xs leading-relaxed text-rose-900/75">
                                {message.content}
                              </p>
                              {message.errorDetail && (
                                <details className="mt-2.5">
                                  <summary className="cursor-pointer text-[10px] font-medium text-rose-700/70">
                                    Technical details
                                  </summary>
                                  <pre className="mt-1.5 max-h-28 overflow-auto rounded-lg border border-rose-200 bg-white/70 p-2 font-mono text-[10px] leading-relaxed text-rose-900/70">
                                    {message.errorDetail}
                                  </pre>
                                </details>
                              )}
                              {message.retryText && (
                                <button
                                  onClick={() => void retryMessage(message)}
                                  disabled={isLoading}
                                  className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-3 py-1.5 text-[10px] font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  <Icon name="spark" className="h-3 w-3" />
                                  Retry request
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <>
                          {parsed.hasThink && (
                            <div className="mb-4 overflow-hidden rounded-xl border border-amber-200/80 bg-amber-50/60">
                              <button
                                onClick={() => toggleThink(message.id)}
                                className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left"
                              >
                                <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                                  <Icon name="brain" className="h-3.5 w-3.5" />
                                </span>
                                <span className="text-xs font-semibold text-amber-950">
                                  Reasoning trace
                                </span>
                                <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-medium text-amber-700">
                                  {parsed.thinkText.split("\n").filter(Boolean).length} lines
                                </span>
                                <Icon
                                  name="chevron"
                                  className={`ml-auto h-3.5 w-3.5 text-amber-600 transition-transform ${
                                    isExpanded ? "rotate-90" : ""
                                  }`}
                                />
                              </button>
                              {isExpanded && (
                                <div className="thin-scrollbar max-h-72 overflow-y-auto border-t border-amber-200/70 bg-amber-50/80 px-3.5 py-3 font-mono text-[11px] leading-relaxed text-amber-950/80 whitespace-pre-wrap">
                                  {parsed.thinkText}
                                </div>
                              )}
                            </div>
                          )}

                          {parsed.hasTool && (
                            <div className="mb-4 overflow-hidden rounded-xl border border-indigo-200 bg-indigo-50/60">
                              <div className="flex items-center gap-2.5 border-b border-indigo-200/70 px-3.5 py-2.5">
                                <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
                                  <Icon name="tool" className="h-3.5 w-3.5" />
                                </span>
                                <span className="text-xs font-semibold text-indigo-950">
                                  Tool call
                                </span>
                                <span className="rounded-full bg-indigo-100 px-2 py-0.5 font-mono text-[9px] font-medium text-indigo-700">
                                  {toolLabel(parsed.toolText)}
                                </span>
                              </div>
                              <pre className="thin-scrollbar overflow-x-auto bg-white/70 p-3 font-mono text-[11px] leading-relaxed text-indigo-950">
                                {parsed.toolText}
                              </pre>
                            </div>
                          )}

                          {parsed.answerText ? (
                            <div className="text-sm leading-relaxed text-slate-800">
                              <RichText text={parsed.answerText} />
                            </div>
                          ) : parsed.hasTool ? (
                            <p className="text-xs italic text-slate-500">
                              Executed the tool payload above.
                            </p>
                          ) : null}
                        </>
                      )}

                      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                        <span className="text-[10px] text-slate-400">{message.timestamp}</span>
                        {!message.isError && (
                          <button
                            onClick={() => void copyAnswer(message)}
                            className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-[10px] font-medium text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                          >
                            <Icon
                              name={copiedId === message.id ? "check" : "copy"}
                              className="h-3 w-3"
                            />
                            {copiedId === message.id ? "Copied" : "Copy"}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="message-in flex items-start gap-3">
                <Avatar role="assistant" />
                <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white/95 px-4 py-3.5 shadow-sm">
                  <div className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:0.15s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:0.3s]" />
                  </div>
                  <span className="text-xs font-medium text-slate-500">
                    Reasoning through the problem...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        <footer className="shrink-0 border-t border-slate-200/80 bg-white/90 px-4 py-4 backdrop-blur-md lg:px-8">
          <div className="mx-auto w-full max-w-3xl">
            {messages.length <= 2 && (
              <div className="thin-scrollbar mb-3 flex gap-2 overflow-x-auto pb-1 lg:hidden">
                {QUICK_PROMPTS.map((item) => (
                  <button
                    key={item.title}
                    onClick={() => void handleSend(item.prompt)}
                    disabled={isLoading}
                    className="shrink-0 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[10px] font-medium text-slate-600 shadow-sm transition hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-50"
                  >
                    {item.title}
                  </button>
                ))}
              </div>
            )}

            <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg shadow-slate-950/[0.04] transition focus-within:border-indigo-300 focus-within:ring-4 focus-within:ring-indigo-500/10">
              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask BDW-72B about VLSI, hardware, power, HPC, or research..."
                aria-label="Message BDW-72B"
                className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm leading-relaxed text-slate-900 outline-none placeholder:text-slate-400"
              />
              <button
                onClick={() => void handleSend()}
                disabled={!input.trim() || isLoading}
                aria-label="Send message"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
              >
                <Icon name="send" className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-2 flex items-center justify-between gap-3 text-[10px] text-slate-400">
              <span>Enter to send · Shift+Enter for a new line</span>
              <span className="hidden sm:inline">Verify critical engineering calculations</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
