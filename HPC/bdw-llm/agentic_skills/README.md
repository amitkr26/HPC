# BDW Agentic Skills: Phase 7 Multi-Hop Reasoning & Python Code Interpreter

Autonomous tool calling, multi-step reasoning, and dynamic Python code interpreter for Qwen2.5-72B and BDW Agent models.

## Core Capabilities
- **Python Code Interpreter (`code_interpreter.py`)**: Runs Python scripts in an isolated subprocess with a strict 15-second walltime limit. Captures both stdout and stderr with full tracebacks for self-debugging.
- **Production Tool Registry (`tools.py`)**:
  - `calculate_math(expression)`: AST-based safe evaluator for numeric expressions.
  - `execute_python(code)`: Dynamic Python code execution sandbox.
  - `web_search(query)`: Deep-tech and semiconductor literature/recruitment search.
  - `query_supabase_rag(topic)`: Supabase vector store retrieval.
- **Multi-Hop Interceptor Loop (`agent_loop.py`)**:
  - Intercepts `<tool_call>` tags from model generations.
  - Supports multi-step reasoning chains (up to 5 autonomous hops per query).
  - Automatically feeds back tool outputs in `<tool_result>` blocks.
  - Enables self-correction if an error traceback is returned.

## Verification & Tests
```bash
python3 agent_loop.py --test
```

## CLI Usage
```bash
# Multi-step problem solving
python3 agent_loop.py --prompt "Write and execute a Python script to compute the setup slack for a clock period of 2.5ns with T_cq=0.3ns, T_comb=1.4ns, T_setup=0.2ns, and T_skew=0.1ns."

# View system prompt and active tool schemas
python3 agent_loop.py --dry-run
```
