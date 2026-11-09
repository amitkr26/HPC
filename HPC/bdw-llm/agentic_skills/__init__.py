"""
BDW Agentic Skills Package (Phase 7 Multi-Hop Reasoning)
=======================================================
Autonomous Tool Calling, Python Code Interpretation, and Interception Framework.
"""

from .code_interpreter import execute_python

from .tools import (
    TOOL_REGISTRY,
    calculate_math,
    execute_python,
    web_search,
    query_supabase_rag,
    execute_tool,
    get_tool_definitions,
)

from .agent_loop import (
    BDWAgentLoop,
    build_system_prompt,
    extract_tool_calls,
)

__all__ = [
    "TOOL_REGISTRY",
    "calculate_math",
    "execute_python",
    "web_search",
    "query_supabase_rag",
    "execute_tool",
    "get_tool_definitions",
    "BDWAgentLoop",
    "build_system_prompt",
    "extract_tool_calls",
]
