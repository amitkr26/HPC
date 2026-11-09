#!/usr/bin/env python3
"""
BDW Agentic Skills: Python Code Interpreter
==========================================
Autonomous sandbox execution of Python scripts for Qwen2.5-72B and BDW Agent.
Enables dynamic mathematical analysis, algorithm prototyping, tensor calculations,
and self-debugging through full stdout/stderr capture with a strict 15-second timeout.
"""

import os
import subprocess
import sys
import tempfile
import time
from typing import Dict, Any

DEFAULT_TIMEOUT_SECONDS = 15
MAX_OUTPUT_CHARS = 4000


def execute_python(code: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    """
    Executes a Python code snippet in a dedicated subprocess and returns the output.
    Captures both stdout and stderr so the LLM can inspect tracebacks and self-correct.

    Args:
        code: Valid Python code string to execute.
        timeout: Maximum execution walltime in seconds (default: 15s).

    Returns:
        Formatted execution string containing stdout, stderr, execution time, and exit status.
    """
    if not code or not code.strip():
        return "Error: Empty Python code provided."

    clean_code = code.strip()

    # If code was passed with markdown backticks (```python ... ```), strip them
    if clean_code.startswith("```"):
        import re
        clean_code = re.sub(r"^```(?:python|py)?\s*", "", clean_code)
        clean_code = re.sub(r"\s*```$", "", clean_code)
        clean_code = clean_code.strip()

    # Create an isolated temporary file for execution
    temp_dir = tempfile.mkdtemp(prefix="bdw_pyexec_")
    script_path = os.path.join(temp_dir, "solution.py")

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(clean_code)

        # Prepare isolated execution environment
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        start_time = time.time()
        process = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=temp_dir,
        )
        elapsed = time.time() - start_time

        stdout = process.stdout
        stderr = process.stderr
        rc = process.returncode

        # Truncate output if excessively large
        if len(stdout) > MAX_OUTPUT_CHARS:
            stdout = stdout[:MAX_OUTPUT_CHARS] + f"\n... [Output truncated after {MAX_OUTPUT_CHARS} characters]"
        if len(stderr) > MAX_OUTPUT_CHARS:
            stderr = stderr[:MAX_OUTPUT_CHARS] + f"\n... [Stderr truncated after {MAX_OUTPUT_CHARS} characters]"

        # Format output for LLM consumption and self-correction
        output_parts = [f"[Execution Time: {elapsed:.3f}s | Exit Code: {rc}]"]

        if rc == 0:
            output_parts.append("[Status: Succeeded]")
            if stdout.strip():
                output_parts.append(f"STDOUT:\n{stdout.strip()}")
            else:
                output_parts.append("STDOUT: (Script executed successfully with no printed output)")
            if stderr.strip():
                output_parts.append(f"STDERR (Warnings):\n{stderr.strip()}")
        else:
            output_parts.append("[Status: Failed - Inspect traceback to self-correct]")
            if stderr.strip():
                output_parts.append(f"STDERR:\n{stderr.strip()}")
            if stdout.strip():
                output_parts.append(f"STDOUT:\n{stdout.strip()}")

        return "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return (
            f"[Execution Error]: Execution timed out after {timeout} seconds.\n"
            "The script was terminated to conserve cluster resources. Ensure algorithms do not contain infinite loops."
        )
    except Exception as exc:
        return f"[Execution Error]: Internal interpreter exception: {str(exc)}"
    finally:
        # Clean up temporary directory and script
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass


if __name__ == "__main__":
    print("=== Testing Python Code Interpreter ===")
    test_code = """
import math

def calculate_sharded_memory(model_params_b, num_gpus):
    fp16_params_gb = model_params_b * 2
    fp16_grads_gb = model_params_b * 2
    fp32_adam_gb = model_params_b * 12
    total_static_gb = fp16_params_gb + fp16_grads_gb + fp32_adam_gb
    per_gpu_gb = total_static_gb / num_gpus
    return total_static_gb, per_gpu_gb

total, per_gpu = calculate_sharded_memory(70, 32)
print(f"Total ZeRO-3 footprint: {total:.1f} GB")
print(f"Static memory per GPU across 32 GPUs: {per_gpu:.2f} GB")
"""
    print(execute_python(test_code))

    print("\n=== Testing Error Traceback Capture (for Self-Correction) ===")
    error_code = """
x = 100
y = 0
print(x / y)
"""
    print(execute_python(error_code))

    print("\n=== Testing Timeout Guardrail ===")
    timeout_code = """
import time
time.sleep(20)
"""
    print(execute_python(timeout_code, timeout=2))
