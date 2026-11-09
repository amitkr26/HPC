#!/usr/bin/env python3
"""
BDW Agentic Skills: Multi-Hop Interceptor Loop
=============================================
Phase 7 Autonomous Reasoning Engine for Qwen2.5-72B and BDW Agent.
Features:
- Dynamic Python Code Interpreter with stdout/stderr traceback inspection.
- Multi-step autonomous tool chaining (up to 5 autonomous hops per query).
- Automated self-correction loop when errors occur.
- vLLM / OpenAI-compatible endpoint integration.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

# Import registered tools
try:
    from tools import (
        TOOL_REGISTRY,
        execute_tool,
        get_tool_definitions,
    )
except ImportError:
    from agentic_skills.tools import (
        TOOL_REGISTRY,
        execute_tool,
        get_tool_definitions,
    )

# =============================================================================
# 1. Authoritative Multi-Hop System Prompt
# =============================================================================

def build_system_prompt() -> str:
    """Builds the Phase 7 agent system prompt with active tool schemas and multi-hop directives."""
    tools_schema = get_tool_definitions()
    return f"""You are BerojgarDegreeWala AI (BDW Agent), India's premier autonomous intelligence engine for Deep-Tech Hardware, Semiconductors, VLSI design, and National Research Labs.

You possess native tool-calling and Python code interpretation capabilities.

AVAILABLE TOOLS:
{tools_schema}

### MULTI-HOP AUTONOMOUS REASONING & CODE INTERPRETATION DIRECTIVES:
1. TOOL INVOCATION SYNTAX:
   When you need external information, live lab notifications, or complex computations, output a tool call using this EXACT format:
   <tool_call>{{"name": "tool_name", "arguments": {{"param1": "value1"}}}}</tool_call>

2. PYTHON CODE INTERPRETER (`execute_python`):
   - You can write and execute full Python scripts in an isolated sandbox.
   - Use `execute_python` for multi-step logic, data processing, statistical modeling, VLSI timing slack tables, or simulating hardware architectures.
   - Always include `print(...)` statements in your scripts so you can read the output.

3. MULTI-STEP REASONING & SELF-CORRECTION:
   - You can chain multiple tools autonomously across multiple turns (up to 5 hops).
   - For example: Hop 1 (query documentation via `query_supabase_rag`) -> Hop 2 (write a Python script via `execute_python` to compute exact numbers) -> Final Response.
   - SELF-DEBUGGING: If your Python code or tool call returns an error or traceback in `<tool_result>`, carefully inspect the error message, identify the root cause, fix your code, and invoke the tool again with the corrected implementation.

4. IMMEDIATE TURN TERMINATION:
   - Immediately after outputting a `<tool_call>`, STOP GENERATING. Do not write filler text or guess the result.
   - The environment will execute the tool and provide the output in `<tool_result>...</tool_result>`.

5. FINAL SYNTHESIS:
   - Once all required information and computational results have been gathered, provide a technically rigorous, highly articulate final answer without emitting any further `<tool_call>` tags.
"""


# =============================================================================
# 2. Tool Call Interceptor & Parser
# =============================================================================

TOOL_CALL_REGEX = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)


def extract_tool_calls(text: str) -> List[Dict[str, Any]]:
    """
    Extracts all tool calls from the LLM output.
    Supports clean JSON and markdown code block wrappers (```json ... ```).
    """
    matches = TOOL_CALL_REGEX.findall(text)
    tool_calls = []

    for raw_match in matches:
        clean_json = raw_match.strip()
        # Strip markdown code fencing if present
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
            clean_json = re.sub(r"\s*```$", "", clean_json)
            clean_json = clean_json.strip()

        try:
            parsed = json.loads(clean_json)
            if isinstance(parsed, dict) and "name" in parsed:
                args = parsed.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"query": args}
                tool_calls.append({
                    "name": parsed["name"],
                    "arguments": args if isinstance(args, dict) else {},
                    "raw": raw_match,
                })
        except json.JSONDecodeError as exc:
            # Fallback regex extraction for loosely-formatted calls
            name_match = re.search(r'"name":\s*"([^"]+)"', clean_json)
            if name_match:
                tool_name = name_match.group(1)
                args = {}
                args_match = re.search(r'"arguments":\s*({.*?})', clean_json, re.DOTALL)
                if args_match:
                    try:
                        args = json.loads(args_match.group(1))
                    except Exception:
                        pass
                tool_calls.append({
                    "name": tool_name,
                    "arguments": args,
                    "raw": raw_match,
                    "parse_warning": str(exc),
                })

    return tool_calls


# =============================================================================
# 3. Multi-Hop Autonomous Agent Loop
# =============================================================================

class BDWAgentLoop:
    """Multi-hop autonomous tool execution loop with Python code interpretation."""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_hops: int = 5,
        temperature: float = 0.1,
        verbose: bool = True,
    ):
        self.api_base = (
            api_base
            or os.environ.get("VLLM_API_BASE")
            or os.environ.get("NEXT_PUBLIC_API_URL", "").replace("/chat/completions", "")
            or "http://127.0.0.1:8000/v1"
        ).rstrip("/")

        if not self.api_base.endswith("/v1") and not self.api_base.endswith("/v1/chat/completions"):
            if "ai.berojgardegreewala.app" in self.api_base:
                self.api_base = f"{self.api_base}/v1"

        self.api_key = api_key or os.environ.get("BDW_API_KEY") or os.environ.get("HF_TOKEN", "")
        self.model_name = model_name
        self.max_hops = max_hops
        self.temperature = temperature
        self.verbose = verbose

    def _resolve_model(self) -> str:
        """Dynamically queries the /v1/models endpoint if model_name is not set."""
        if self.model_name:
            return self.model_name

        models_endpoint = f"{self.api_base}/models"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            req = urllib.request.Request(models_endpoint, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "data" in data and len(data["data"]) > 0:
                    detected = data["data"][0]["id"]
                    if self.verbose:
                        print(f"[BDW-Agent] Auto-detected serving model: {detected}")
                    self.model_name = detected
                    return detected
        except Exception as e:
            if self.verbose:
                print(f"[BDW-Agent] Could not resolve model via /models ({e}), using default.")

        self.model_name = "Qwen/Qwen2.5-72B-Instruct"
        return self.model_name

    def call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Sends chat completion request to vLLM endpoint."""
        model = self._resolve_model()
        url = f"{self.api_base}/chat/completions"
        if not url.endswith("/v1/chat/completions") and "/v1" not in url:
            url = f"{self.api_base}/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BDW-Agentic-Skills/2.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1024,
            "stream": False,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choice = result["choices"][0]
                return choice["message"].get("content", "")
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"vLLM API HTTP {he.code}: {err_body}")
        except Exception as exc:
            raise RuntimeError(f"Connection error to vLLM ({url}): {str(exc)}")

    def run(
        self,
        user_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes multi-hop autonomous reasoning:
        - Allows up to self.max_hops autonomous tool calls per user query.
        - Intercepts each <tool_call>, executes it, appends <tool_result>, and feeds back to model.
        - Stops when model emits answer without <tool_call> or when max_hops is reached.
        """
        if messages:
            conv_messages: List[Dict[str, str]] = [
                {"role": "system", "content": build_system_prompt()}
            ]
            for m in messages:
                if m.get("role") != "system":
                    conv_messages.append({"role": m["role"], "content": m["content"]})
            user_texts = [m["content"] for m in conv_messages if m["role"] == "user"]
            active_prompt = user_texts[-1] if user_texts else (user_prompt or "")
            messages = conv_messages
        else:
            active_prompt = user_prompt or ""
            messages = [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": active_prompt},
            ]

        tool_execution_trace: List[Dict[str, Any]] = []
        hop = 0

        if self.verbose:
            print(f"\n{'='*75}")
            print(f"[BDW-Agent Phase 7] New Query: {active_prompt}")
            print(f"{'='*75}")

        while hop < self.max_hops:
            hop += 1
            if self.verbose:
                print(f"\n--- [Hop {hop}/{self.max_hops}] Calling LLM ---")

            llm_output = self.call_llm(messages)
            tool_calls = extract_tool_calls(llm_output)

            # Case A: Model has concluded reasoning -> Final answer
            if not tool_calls:
                if self.verbose:
                    print(f"[BDW-Agent] Completed reasoning chain in {hop} hop(s). No further tools required.")
                messages.append({"role": "assistant", "content": llm_output})
                return {
                    "final_answer": llm_output,
                    "total_hops": hop,
                    "tools_called": tool_execution_trace,
                    "messages": messages,
                }

            # Case B: Tool call(s) detected -> Intercept, execute, and feed back
            if self.verbose:
                print(f"[BDW-Agent] Detected {len(tool_calls)} tool invocation(s) at Hop {hop}.")

            messages.append({"role": "assistant", "content": llm_output})

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]

                if self.verbose:
                    print(f"  ==> Executing: {tool_name}")
                    if tool_name == "execute_python":
                        code_preview = tool_args.get("code", "").strip().split("\n")
                        print(f"      Code ({len(code_preview)} lines): {code_preview[0]} ...")
                    else:
                        print(f"      Arguments: {tool_args}")

                start_t = time.time()
                tool_output = execute_tool(tool_name, tool_args)
                elapsed = time.time() - start_t

                if self.verbose:
                    preview = tool_output.replace("\n", " ")[:120]
                    print(f"  <== Result ({elapsed:.3f}s): {preview}...")

                tool_execution_trace.append({
                    "hop": hop,
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": tool_output,
                    "execution_time_sec": round(elapsed, 4),
                })

                # Inject tool result formatted for model consumption
                result_message = {
                    "role": "user",
                    "content": f"<tool_result>\n{tool_output}\n</tool_result>",
                }
                messages.append(result_message)

        # Max hops reached: Force final answer generation
        if self.verbose:
            print(f"[BDW-Agent WARNING] Reached maximum limit of {self.max_hops} hops. Forcing final synthesis.")

        forced_synthesis_msg = {
            "role": "user",
            "content": "You have reached the maximum autonomous tool-call limit. Synthesize your final answer now based on all results gathered above."
        }
        messages.append(forced_synthesis_msg)
        final_answer = self.call_llm(messages)
        messages.append({"role": "assistant", "content": final_answer})

        return {
            "final_answer": final_answer,
            "total_hops": self.max_hops,
            "tools_called": tool_execution_trace,
            "messages": messages,
            "warning": f"Terminated at max_hops ({self.max_hops}).",
        }


# =============================================================================
# 4. Comprehensive Unit Test Suite
# =============================================================================

def run_unit_tests() -> bool:
    """Verifies Python interpreter execution, multi-hop chaining, and limit enforcement."""
    print("\n" + "=" * 65)
    print("RUNNING BDW PHASE 7 MULTI-HOP AGENTIC UNIT TESTS")
    print("=" * 65)

    # Test 1: Python Code Execution
    py_test = execute_tool("execute_python", {
        "code": "import math\nprint(f'PI_APPROX={math.pi:.4f}')"
    })
    assert "[Status: Succeeded]" in py_test and "PI_APPROX=3.1416" in py_test, f"Failed: {py_test}"
    print("  [PASS] Python Interpreter: Code executed cleanly with output capture.")

    # Test 2: Error Capture & Self-Correction Traceback
    err_test = execute_tool("execute_python", {
        "code": "def divide(a, b): return a / b\nprint(divide(10, 0))"
    })
    assert "ZeroDivisionError" in err_test and "[Status: Failed" in err_test, f"Failed: {err_test}"
    print("  [PASS] Traceback Capture: Correctly recorded ZeroDivisionError for self-correction.")

    # Test 3: Multi-Hop Mock Simulation (3-Hop Reasoning Chain)
    class MockMultiHopAgent(BDWAgentLoop):
        def __init__(self):
            super().__init__(max_hops=5, verbose=False)
            self.step = 0

        def call_llm(self, messages: List[Dict[str, str]]) -> str:
            self.step += 1
            if self.step == 1:
                # Hop 1: RAG query
                return '<tool_call>{"name": "query_supabase_rag", "arguments": {"topic": "memory for 70b deepspeed zero-3"}}</tool_call>'
            if self.step == 2:
                # Hop 2: Write Python code to verify calculation
                code = (
                    "params_b = 70\n"
                    "fp16_gb = params_b * 2\n"
                    "adam_gb = params_b * 12\n"
                    "total_gb = fp16_gb + fp16_gb + adam_gb\n"
                    "per_gpu = total_gb / 32\n"
                    "print(f'TOTAL={total_gb}, PER_GPU={per_gpu}')\n"
                )
                return f'<tool_call>{{"name": "execute_python", "arguments": {{"code": {json.dumps(code)}}}}}</tool_call>'
            # Hop 3: Final Answer
            return (
                "Final Analysis:\n"
                "According to BDW RAG and dynamic Python calculation, a 70B parameter model under ZeRO-3 requires 1,120 GB total static memory.\n"
                "Across 32 GPUs, each GPU requires exactly 35.0 GB static memory."
            )

    agent = MockMultiHopAgent()
    res = agent.run("Calculate the static memory for a 70B model sharded with DeepSpeed ZeRO-3 across 32 GPUs.")
    assert res["total_hops"] == 3
    assert len(res["tools_called"]) == 2
    assert res["tools_called"][0]["tool"] == "query_supabase_rag"
    assert res["tools_called"][1]["tool"] == "execute_python"
    assert "35.0 GB" in res["final_answer"]
    print(f"  [PASS] Multi-Hop Reasoning: Executed 3-hop autonomous chain (RAG -> Python -> Synthesis).")

    # Test 4: Max-Hops Guardrail Enforcement (Prevent Infinite Loops)
    class InfiniteLoopAgent(BDWAgentLoop):
        def __init__(self):
            super().__init__(max_hops=5, verbose=False)

        def call_llm(self, messages: List[Dict[str, str]]) -> str:
            last = messages[-1].get("content", "")
            if "reached the maximum autonomous tool-call limit" in last:
                return "Final forced synthesis complete."
            return '<tool_call>{"name": "calculate_math", "arguments": {"expression": "1 + 1"}}</tool_call>'

    loop_agent = InfiniteLoopAgent()
    loop_res = loop_agent.run("Test loop")
    assert loop_res["total_hops"] == 5
    assert len(loop_res["tools_called"]) == 5
    assert "Final forced synthesis" in loop_res["final_answer"]
    print("  [PASS] Max-Hop Guardrail: Enforced strict limit of 5 hops and forced clean termination.")

    print("\nALL PHASE 7 UNIT TESTS PASSED! (4/4)\n")
    return True


# =============================================================================
# 5. CLI Entrypoint
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="BDW Agentic Skills: Phase 7 Multi-Hop Reasoning & Python Code Interpreter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--prompt", type=str, help="User prompt to execute autonomously.")
    parser.add_argument("--api-base", type=str, default=None, help="vLLM API base URL.")
    parser.add_argument("--api-key", type=str, default=None, help="vLLM / BDW API Key.")
    parser.add_argument("--model", type=str, default=None, help="Target model identifier.")
    parser.add_argument("--max-hops", type=int, default=5, help="Maximum autonomous tool-calling hops.")
    parser.add_argument("--test", action="store_true", help="Run comprehensive unit test suite.")
    parser.add_argument("--dry-run", action="store_true", help="Print system prompt and registered tool schemas.")

    args = parser.parse_args()

    if args.test:
        success = run_unit_tests()
        sys.exit(0 if success else 1)

    if args.dry_run:
        print("=== BDW PHASE 7 SYSTEM PROMPT ===")
        print(build_system_prompt())
        sys.exit(0)

    if not args.prompt:
        args.prompt = "Write and execute a Python script to compute the setup slack for a clock period of 2.5ns with T_cq=0.3ns, T_comb=1.4ns, T_setup=0.2ns, and T_skew=0.1ns."

    agent = BDWAgentLoop(
        api_base=args.api_base,
        api_key=args.api_key,
        model_name=args.model,
        max_hops=args.max_hops,
    )

    try:
        output = agent.run(args.prompt)
        print(f"\n{'='*75}")
        print("FINAL BDW AGENT RESPONSE:")
        print(f"{'='*75}")
        print(output["final_answer"])
        print(f"\n[Execution Metadata] Total Hops: {output['total_hops']}, Tools Executed: {len(output['tools_called'])}")
    except Exception as e:
        print(f"\n[ERROR] Agent execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
