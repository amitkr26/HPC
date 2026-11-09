#!/usr/bin/env python3
"""
BDW Phase 9: Production Agentic API Server
=========================================
OpenAI-compatible FastAPI server that intercepts /v1/chat/completions requests
and routes them through BDWAgentLoop for multi-hop tool execution,
dynamic Python code evaluation, and live Supabase RAG lookups.

Endpoints:
  GET  /health
  GET  /v1/models
  POST /v1/chat/completions
"""

import asyncio
import json
import os
import sys
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Ensure root bdw-llm is on path for agentic_skills imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from agentic_skills.agent_loop import BDWAgentLoop

# Configuration
P5_ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
if os.path.isfile(P5_ENV_FILE):
    try:
        with open(P5_ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

P5_API_KEY = os.environ.get("P5_API_KEY", "")
VLLM_BACKEND_URL = os.environ.get("VLLM_BACKEND_URL", "http://127.0.0.1:8001/v1")
HOST = "0.0.0.0"
PORT = 8000

app = FastAPI(
    title="BDW Agentic Production API Server",
    description="OpenAI-compatible edge gateway with multi-hop agentic loop and code execution",
    version="2.0.0"
)

# Cross-Origin Resource Sharing for Vercel Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request / Response Schemas
# =============================================================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "Qwen/Qwen2.5-72B-Instruct"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False


# =============================================================================
# Routes
# =============================================================================

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "BDW Agentic Production API Server",
        "version": "2.0.0",
        "backend": VLLM_BACKEND_URL,
        "features": ["agent_loop", "code_interpreter", "supabase_rag", "lora_adapter"]
    }


@app.get("/models")
@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "Qwen/Qwen2.5-72B-Instruct",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "bdw",
                "permission": [],
                "root": "Qwen/Qwen2.5-72B-Instruct",
                "parent": None
            },
            {
                "id": "bdw-hardware-lora",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "bdw",
                "permission": [],
                "root": "bdw-hardware-lora",
                "parent": "Qwen/Qwen2.5-72B-Instruct"
            }
        ]
    }


@app.post("/chat/completions")
@app.post("/v1/chat/completions")
async def create_chat_completion(
    req: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
):
    # Optional API key verification (if configured)
    if P5_API_KEY and authorization:
        token = authorization.replace("Bearer ", "").strip()
        if token != P5_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API Key.")

    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty.")

    # Initialize Agent Loop pointing to the live vLLM backend
    agent = BDWAgentLoop(
        api_base=VLLM_BACKEND_URL,
        api_key=P5_API_KEY,
        model_name=req.model,
        max_hops=5,
        temperature=req.temperature or 0.3,
        verbose=True,
    )

    msg_dicts = [{"role": m.role, "content": m.content} for m in req.messages]
    cmpl_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_time = int(time.time())

    # Streaming mode (Immediate response to edge, keeps Cloudflare tunnel alive with heartbeats)
    if req.stream:
        async def stream_generator():
            init_chunk = {
                "id": cmpl_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": ""},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(init_chunk)}\n\n"

            loop = asyncio.get_running_loop()
            task = loop.run_in_executor(None, agent.run, None, msg_dicts)

            # Send heartbeat comment every 5s while multi-hop agent loop reasons & executes tools
            while not task.done():
                await asyncio.sleep(5)
                if not task.done():
                    yield ": keep-alive\n\n"

            try:
                result = await task
                final_answer = result.get("final_answer", "")
            except Exception as exc:
                err_chunk = {
                    "id": cmpl_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {"content": f"\n\n[Inference Error: {exc}]"}, "finish_reason": "error"}]
                }
                yield f"data: {json.dumps(err_chunk)}\n\n"
                yield "data: [DONE]\n\n"
                return

            words = final_answer.split(" ")
            for i, word in enumerate(words):
                chunk_str = word + (" " if i < len(words) - 1 else "")
                chunk = {
                    "id": cmpl_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": req.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk_str},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.01)

            end_chunk = {
                "id": cmpl_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": req.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(end_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Non-streaming mode (standard OpenAI format)
    try:
        result = await asyncio.to_thread(agent.run, messages=msg_dicts)
        final_answer = result.get("final_answer", "")
    except Exception as exc:
        err_msg = str(exc)
        print(f"[API ERROR] Agent loop error: {err_msg}")
        if "Connection error" in err_msg or "Failed to connect" in err_msg:
            raise HTTPException(
                status_code=503,
                detail="vLLM 72B inference server is loading shards. Please retry in a few moments."
            )
        raise HTTPException(status_code=500, detail=f"Inference execution error: {err_msg}")

    prompt_tokens = sum(len(m.content.split()) for m in req.messages) * 2
    completion_tokens = len(final_answer.split()) * 2

    return {
        "id": cmpl_id,
        "object": "chat.completion",
        "created": created_time,
        "model": req.model or "Qwen/Qwen2.5-72B-Instruct",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": final_answer
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        },
        "bdw_meta": {
            "total_hops": result.get("total_hops", 1),
            "tools_called": [t.get("tool") for t in result.get("tools_called", [])]
        }
    }


if __name__ == "__main__":
    import uvicorn
    print(f"=== Starting BDW Agentic Production API Server on {HOST}:{PORT} ===")
    print(f"Backend vLLM target: {VLLM_BACKEND_URL}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
