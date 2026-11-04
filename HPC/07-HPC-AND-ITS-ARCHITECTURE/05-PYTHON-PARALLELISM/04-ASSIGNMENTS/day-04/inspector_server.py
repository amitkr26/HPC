"""Exercise 3 Part A: RPyC remote server - System Inspector & Math Utility.

Exposes a SystemInspectorService through an RPyC ThreadedServer on port 18861.
Every public entry point is an exposed_* method so the client can reach it via
conn.root.

Run:  python inspector_server.py
Then: python inspector_client.py
"""

import ast
import math
import operator
import os
import platform
import time

import rpyc
from rpyc.utils.server import ThreadedServer

SERVER_PORT = 18861
MAX_EXPONENT = 512
MAX_POW_ABS_EXPONENT = 4096
MAX_CALL_ARGS = 4

_ALLOWED_FUNCTIONS = {
    name: getattr(math, name)
    for name in dir(math)
    if not name.startswith("_") and callable(getattr(math, name))
}
_ALLOWED_CONSTANTS = {
    name: getattr(math, name)
    for name in ("pi", "e", "tau", "inf", "nan", "epsilon")
    if hasattr(math, name)
}
_ALLOWED_NAMES = {"math": math}
_ALLOWED_NAMES.update(_ALLOWED_CONSTANTS)
_ALLOWED_NAMES.update(_ALLOWED_FUNCTIONS)


def _safe_pow(left, right):
    """Raise a clear error for exponents that would hang the server."""
    if isinstance(left, int) and isinstance(right, int) and abs(right) > MAX_POW_ABS_EXPONENT:
        raise ValueError(
            f"Exponent {right} is too large (limit {MAX_POW_ABS_EXPONENT})."
        )
    return left ** right


_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: _safe_pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitAnd: operator.and_,
    ast.BitXor: operator.xor,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Invert: operator.invert,
}


def safe_eval(expression_str):
    """Evaluate a numeric/math expression from a whitelisted AST subset.

    Allowed: numeric literals, arithmetic/bitwise operators, names such as
    pi/e/sqrt and calls of the form math.sqrt(...).  Everything else (names,
    subscripts, comprehensions, dunder access, ...) is rejected with ValueError.
    """
    if not isinstance(expression_str, str) or not expression_str.strip():
        raise ValueError("Expression must be a non-empty string.")
    try:
        tree = ast.parse(expression_str.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression: {exc.msg}") from exc
    return _evaluate(tree)


def _evaluate(node):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float, complex)):
            raise ValueError("Only numeric literals are allowed.")
        return node.value
    if isinstance(node, ast.BinOp):
        operation = _BINARY_OPS.get(type(node.op))
        if operation is None:
            raise ValueError(f"Operator {type(node.op).__name__} is not allowed.")
        return operation(_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp):
        operation = _UNARY_OPS.get(type(node.op))
        if operation is None:
            raise ValueError(f"Unary operator {type(node.op).__name__} is not allowed.")
        return operation(_evaluate(node.operand))
    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_NAMES:
            return _ALLOWED_NAMES[node.id]
        raise ValueError(f"Unknown name '{node.id}' is not allowed.")
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "math":
            if node.attr in _ALLOWED_FUNCTIONS:
                return _ALLOWED_FUNCTIONS[node.attr]
            if node.attr in _ALLOWED_CONSTANTS:
                return _ALLOWED_CONSTANTS[node.attr]
        raise ValueError(
            "Only math.<function> and math.<constant> attribute access is allowed."
        )
    if isinstance(node, ast.Call):
        function = _evaluate(node.func)
        if not callable(function):
            raise ValueError("Only whitelisted functions may be called.")
        if node.keywords:
            raise ValueError("Keyword arguments are not allowed.")
        if len(node.args) > MAX_CALL_ARGS:
            raise ValueError(f"At most {MAX_CALL_ARGS} arguments are allowed.")
        return function(*[_evaluate(arg) for arg in node.args])
    raise ValueError(f"Unsupported syntax: {type(node).__name__}.")


class SystemInspectorService(rpyc.Service):
    """Remote host inspection and safe math utilities."""

    def exposed_get_system_info(self):
        """Returns a dictionary containing server OS, hostname, and CPU count."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def exposed_list_files(self, directory_path="."):
        """Returns a list of filenames in the specified directory on the server."""
        entries = sorted(os.listdir(directory_path))
        return [
            name + "/" if os.path.isdir(os.path.join(directory_path, name)) else name
            for name in entries
        ]

    def exposed_compute_powers(self, base, max_exponent):
        """Returns a dictionary mapping exponent to base^exp computed on the server."""
        if isinstance(base, bool) or not isinstance(base, (int, float)):
            raise ValueError("base must be a number.")
        if isinstance(max_exponent, bool) or not isinstance(max_exponent, int):
            raise ValueError("max_exponent must be an integer.")
        if max_exponent < 0:
            raise ValueError("max_exponent must not be negative.")
        if max_exponent > MAX_EXPONENT:
            raise ValueError(f"max_exponent must be <= {MAX_EXPONENT}.")
        return {exponent: base ** exponent for exponent in range(max_exponent + 1)}

    def exposed_execute_expression(self, expression_str):
        """Safely evaluates a basic mathematical expression on the server."""
        return safe_eval(expression_str)


def main():
    """Start the threaded RPyC server (blocking)."""
    server = ThreadedServer(SystemInspectorService, port=SERVER_PORT)
    print(f"RPyC System Inspector Server running on port {SERVER_PORT}...")
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down the inspector server.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
