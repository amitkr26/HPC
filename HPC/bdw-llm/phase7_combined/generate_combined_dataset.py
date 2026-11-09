#!/usr/bin/env python3
"""Generate a deterministic Phase 7 reasoning + tool-calling SFT dataset.

Objective:
Each row represents a complex user query where the assistant must first generate
a <think>...</think> reasoning block explaining its decision-making, followed
immediately by a JSON <tool_call>...</tool_call> block.

Outputs:
  phase7_combined/data/combined_train.jsonl (~150 rows)
  phase7_combined/data/combined_eval.jsonl  (~30 rows)

CLI:
  python3 generate_combined_dataset.py [--check-only] [--train-count 150] [--eval-count 30] [--seed 42]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import operator
import os
import random
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent if (HERE.parent / "merged").exists() else HERE.parents[1]
DEFAULT_OUT = HERE / "data"
DEFAULT_TOKENIZER = ROOT / "merged" / "bdw-7b-sft"

SYSTEM_PROMPT = (
    "You are BDW, a precise reasoning assistant for deep-tech hardware, computing, and scientific engineering. "
    "When a user query requires computation, sizing, timing, or conversion: "
    "1. Formulate your reasoning step by step inside a <think>...</think> block. "
    "2. Conclude by calling the appropriate tool within a <tool_call>...</tool_call> block. "
    "Never skip the reasoning block and never omit closing tags."
)

SCHEMA_VERSION = "phase7-combined-v1"
SOURCE = "phase7-combined-v1"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate an exact arithmetic expression supporting numbers, parentheses, +, -, *, /, and exponents (**).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression string, e.g. '(180 + 450 + 120 + 50)' or '12.5 / (1.1**2 * 1.8e9)'."
                    }
                },
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unit_converter",
            "description": "Convert a numeric quantity between compatible physical, engineering, or computing units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "number",
                        "description": "The numeric magnitude to convert."
                    },
                    "from_unit": {
                        "type": "string",
                        "description": "Source unit symbol (e.g. ps, ns, um, nm, mw, uw, gb, mb, tb, gbps, km, mi, m, ft, kg, lb, c, f, s, hr)."
                    },
                    "to_unit": {
                        "type": "string",
                        "description": "Target unit symbol (e.g. ps, ns, um, nm, mw, uw, gb, mb, tb, gbps, km, mi, m, ft, kg, lb, c, f, s, hr)."
                    }
                },
                "required": ["value", "from_unit", "to_unit"],
                "additionalProperties": False,
            },
        },
    },
]

UNIT_CONVERSIONS = {
    # Time / VLSI
    ("ps", "ns"): 1e-3, ("ns", "ps"): 1e3,
    ("ns", "us"): 1e-3, ("us", "ns"): 1e3,
    ("us", "ms"): 1e-3, ("ms", "us"): 1e3,
    ("ms", "s"): 1e-3, ("s", "ms"): 1e3,
    ("s", "hr"): 1.0 / 3600.0, ("hr", "s"): 3600.0,
    ("min", "s"): 60.0, ("s", "min"): 1.0 / 60.0,
    # Distance / Geometry / Silicon
    ("nm", "um"): 1e-3, ("um", "nm"): 1e3,
    ("um", "mm"): 1e-3, ("mm", "um"): 1e3,
    ("mm", "m"): 1e-3, ("m", "mm"): 1e3,
    ("km", "mi"): 0.621371, ("mi", "km"): 1.609344,
    ("m", "ft"): 3.28084, ("ft", "m"): 0.3048,
    # Mass
    ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
    ("g", "kg"): 1e-3, ("kg", "g"): 1e3,
    # Power / Energy
    ("uw", "mw"): 1e-3, ("mw", "uw"): 1e3,
    ("mw", "w"): 1e-3, ("w", "mw"): 1e3,
    ("w", "kw"): 1e-3, ("kw", "w"): 1e3,
    ("wh", "kwh"): 1e-3, ("kwh", "wh"): 1e3,
    ("kwh", "j"): 3.6e6, ("j", "kwh"): 1.0 / 3.6e6,
    # Computing / Memory / Bandwidth
    ("mb", "gb"): 1.0 / 1024.0, ("gb", "mb"): 1024.0,
    ("gb", "tb"): 1.0 / 1024.0, ("tb", "gb"): 1024.0,
    ("tb", "pb"): 1.0 / 1024.0, ("pb", "tb"): 1024.0,
    ("gbps", "gb/s"): 0.125, ("gb/s", "gbps"): 8.0,
}

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(expr: str) -> float:
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        elif isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")
    return _eval(ast.parse(expr, mode="eval"))


def convert_units(val: float, f_u: str, t_u: str) -> float:
    f_u, t_u = f_u.lower(), t_u.lower()
    if f_u == t_u:
        return val
    if (f_u, t_u) == ("c", "f"):
        return val * 9.0 / 5.0 + 32.0
    if (f_u, t_u) == ("f", "c"):
        return (val - 32.0) * 5.0 / 9.0
    if (f_u, t_u) in UNIT_CONVERSIONS:
        return val * UNIT_CONVERSIONS[(f_u, t_u)]
    raise ValueError(f"Unsupported unit conversion: {f_u} -> {t_u}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# -----------------------------------------------------------------------------
# Synthetic Data Generators: VLSI & Chip Design
# -----------------------------------------------------------------------------
def gen_vlsi_timing(rng: random.Random) -> dict[str, Any]:
    t_cq = rng.randint(80, 220)
    t_comb = rng.randint(300, 850)
    t_setup = rng.randint(60, 160)
    t_skew = rng.randint(20, 80)
    question = (
        f"In a sequential VLSI datapath, a register has a clock-to-Q delay of {t_cq} ps and setup time of {t_setup} ps. "
        f"The critical combinational logic delay between registers is {t_comb} ps with an estimated clock skew of {t_skew} ps. "
        f"What is the minimum operating clock period T_min (ps) required to satisfy setup timing?"
    )
    expr = f"{t_cq} + {t_comb} + {t_setup} + {t_skew}"
    val = safe_eval(expr)
    steps = [
        f"Identify timing parameters: T_cq = {t_cq} ps, T_comb = {t_comb} ps, T_setup = {t_setup} ps, T_skew = {t_skew} ps.",
        "The governing formula for minimum clock period to prevent setup violation is T_min >= T_cq + T_comb + T_setup + T_skew.",
        f"Formulate arithmetic expression: {expr}.",
        "Invoke the calculator tool to evaluate the exact clock period.",
    ]
    return {
        "category": "vlsi",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_vlsi_power(rng: random.Random) -> dict[str, Any]:
    c_pf = rng.randint(15, 85)  # pF
    v_dd = round(rng.uniform(0.75, 1.25), 2)
    f_ghz = round(rng.uniform(1.2, 3.6), 1)
    question = (
        f"A deep-submicron CMOS processor core operates at Vdd = {v_dd} V with clock frequency {f_ghz} GHz. "
        f"The total effective switched capacitance is estimated at {c_pf} pF. "
        f"Compute the dynamic power consumption in watts using P_dyn = C_eff * Vdd^2 * f."
    )
    # C_eff in F = c_pf * 1e-12, f in Hz = f_ghz * 1e9 => c_pf * 1e-3 * v_dd^2 * f_ghz
    expr = f"({c_pf} * 1e-12) * ({v_dd}**2) * ({f_ghz} * 1e9)"
    val = safe_eval(expr)
    steps = [
        f"Extract parameters: switched capacitance C_eff = {c_pf} pF ({c_pf}e-12 F), Vdd = {v_dd} V, frequency f = {f_ghz} GHz ({f_ghz}e9 Hz).",
        "Recall dynamic power dissipation in digital CMOS is governed by P_dyn = C_eff * Vdd^2 * f.",
        f"Substitute parameters into formula: ({c_pf} * 1e-12) * ({v_dd}**2) * ({f_ghz} * 1e9).",
        "Call the calculator tool with the algebraic formulation.",
    ]
    return {
        "category": "vlsi",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_vlsi_yield(rng: random.Random) -> dict[str, Any]:
    wafers = rng.randint(50, 400)
    dies_per_wafer = rng.randint(300, 950)
    defect_yield = round(rng.uniform(84.0, 96.5), 1)
    packaging_yield = round(rng.uniform(92.0, 98.0), 1)
    question = (
        f"A semiconductor fabrication lot processes {wafers} wafers, each patterned with {dies_per_wafer} candidate dies. "
        f"Wafer probe testing demonstrates a die yield of {defect_yield}%, and subsequent packaging yield is {packaging_yield}%. "
        f"How many fully qualified packaged chips are produced from this lot?"
    )
    expr = f"int({wafers} * {dies_per_wafer} * ({defect_yield} / 100) * ({packaging_yield} / 100))"
    eval_expr = f"{wafers} * {dies_per_wafer} * ({defect_yield} / 100) * ({packaging_yield} / 100)"
    val = round(safe_eval(eval_expr), 2)
    steps = [
        f"Determine total raw dies: {wafers} wafers * {dies_per_wafer} dies/wafer.",
        f"Apply wafer test yield ({defect_yield}%) and packaging assembly yield ({packaging_yield}%).",
        f"Expression for good packaged units: {wafers} * {dies_per_wafer} * ({defect_yield} / 100) * ({packaging_yield} / 100).",
        "Invoke calculator to obtain the expected net chip output.",
    ]
    return {
        "category": "vlsi",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": eval_expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_vlsi_unit(rng: random.Random) -> dict[str, Any]:
    variants = [
        ("ps", "ns", rng.randint(150, 4800)),
        ("ns", "ps", round(rng.uniform(0.2, 12.5), 3)),
        ("nm", "um", rng.randint(28, 450)),
        ("um", "nm", round(rng.uniform(0.015, 2.5), 3)),
        ("mw", "uw", round(rng.uniform(1.5, 85.0), 2)),
        ("uw", "mw", rng.randint(250, 15000)),
    ]
    from_u, to_u, val = rng.choice(variants)
    unit_names = {
        "ps": "picoseconds", "ns": "nanoseconds", "nm": "nanometers", "um": "micrometers",
        "mw": "milliwatts", "uw": "microwatts"
    }
    question = (
        f"A physical design timing report lists an interconnect wire delay of {val} {unit_names[from_u]}. "
        f"Convert this value into {unit_names[to_u]} for compatibility with standard Liberty timing tables."
    )
    steps = [
        f"Analyze request: convert {val} {unit_names[from_u]} ({from_u}) to {unit_names[to_u]} ({to_u}).",
        f"Recall conversion relationship between {from_u} and {to_u}.",
        "Invoke the unit_converter tool with source magnitude and respective unit identifiers.",
    ]
    res = round(convert_units(val, from_u, to_u), 8)
    return {
        "category": "vlsi",
        "question": question,
        "tool": "unit_converter",
        "arguments": {"value": val, "from_unit": from_u, "to_unit": to_u},
        "reasoning_steps": steps,
        "expected_result": res,
    }


# -----------------------------------------------------------------------------
# Synthetic Data Generators: HPC & Systems
# -----------------------------------------------------------------------------
def gen_hpc_cluster_power(rng: random.Random) -> dict[str, Any]:
    nodes = rng.randint(16, 128)
    gpus_per_node = rng.choice([4, 8])
    gpu_wattage = rng.choice([300, 350, 400, 700])
    host_wattage = rng.choice([600, 800, 1000])
    pue = round(rng.uniform(1.15, 1.35), 2)
    question = (
        f"A PARAM Rudra supercomputing cluster partition comprises {nodes} compute nodes. Each node hosts "
        f"{gpus_per_node} enterprise GPUs drawing {gpu_wattage} W each, plus {host_wattage} W for host dual-socket CPUs and system memory. "
        f"If the facility Power Usage Effectiveness (PUE) is {pue}, calculate the total facility power draw in kilowatts."
    )
    expr = f"({nodes} * ({gpus_per_node} * {gpu_wattage} + {host_wattage}) * {pue}) / 1000"
    val = round(safe_eval(expr), 3)
    steps = [
        f"Calculate IT power per node: ({gpus_per_node} GPUs * {gpu_wattage} W) + {host_wattage} W host overhead.",
        f"Multiply by {nodes} total compute nodes to obtain aggregate IT power in watts.",
        f"Scale by data center PUE of {pue} and divide by 1000 to convert from watts to kilowatts.",
        f"Construct expression: {expr} and invoke calculator.",
    ]
    return {
        "category": "hpc",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_hpc_zero3_memory(rng: random.Random) -> dict[str, Any]:
    params_b = round(rng.uniform(7.0, 70.0), 1)
    nodes = rng.choice([8, 16, 32, 64])
    gpus_per_node = 8
    total_gpus = nodes * gpus_per_node
    # FP16 params: 2B, FP16 gradients: 2B, FP32 optimizer (AdamW): 12B => total 16 bytes/param
    question = (
        f"An LLM with {params_b} billion parameters is trained using DeepSpeed ZeRO-3 across {total_gpus} GPUs ({nodes} nodes x {gpus_per_node} GPUs). "
        f"Assuming 16 bytes per parameter (2B weights + 2B grads + 12B master weights/momentum/variance states) fully sharded, "
        f"calculate the static memory requirement per GPU in gigabytes (GB)."
    )
    expr = f"({params_b} * 1e9 * 16) / ({total_gpus} * (1024**3))"
    val = round(safe_eval(expr), 3)
    steps = [
        f"Determine total static state bytes: {params_b} * 10^9 parameters * 16 bytes/param.",
        f"In ZeRO-3, model states are evenly partitioned across all {total_gpus} GPUs.",
        f"Divide aggregate bytes by {total_gpus} and convert to GB (divide by 1024^3).",
        f"Formulate expression: {expr} and evaluate with calculator.",
    ]
    return {
        "category": "hpc",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_hpc_unit(rng: random.Random) -> dict[str, Any]:
    variants = [
        ("gb", "mb", rng.randint(4, 256)),
        ("mb", "gb", rng.choice([1024, 2048, 4096, 8192, 16384, 32768, 65536])),
        ("tb", "gb", round(rng.uniform(1.5, 48.0), 2)),
        ("gb", "tb", rng.choice([2048, 4096, 8192, 16384])),
        ("gbps", "gb/s", rng.choice([25, 40, 100, 200, 400, 800])),
        ("gb/s", "gbps", rng.choice([12.5, 25.0, 50.0, 100.0])),
    ]
    from_u, to_u, val = rng.choice(variants)
    unit_names = {
        "gb": "gigabytes", "mb": "megabytes", "tb": "terabytes", "gbps": "gigabits per second", "gb/s": "gigabytes per second"
    }
    question = (
        f"A cluster network adapter specification indicates an InfiniBand interconnect bandwidth of {val} {unit_names[from_u]}. "
        f"Convert this rate to {unit_names[to_u]} for cluster storage throughput benchmarking."
    )
    steps = [
        f"Identify input value: {val} {unit_names[from_u]} ({from_u}).",
        f"Identify target metric: {unit_names[to_u]} ({to_u}).",
        "Call unit_converter with the numeric value and matching unit tokens.",
    ]
    res = round(convert_units(val, from_u, to_u), 6)
    return {
        "category": "hpc",
        "question": question,
        "tool": "unit_converter",
        "arguments": {"value": val, "from_unit": from_u, "to_unit": to_u},
        "reasoning_steps": steps,
        "expected_result": res,
    }


# -----------------------------------------------------------------------------
# Synthetic Data Generators: Physics & Applied Mathematics
# -----------------------------------------------------------------------------
def gen_physics_kinetic(rng: random.Random) -> dict[str, Any]:
    mass = round(rng.uniform(120.0, 2400.0), 1)
    velocity = round(rng.uniform(15.0, 95.0), 1)
    question = (
        f"An autonomous electric test vehicle has an unladen mass of {mass} kg and cruises at a constant velocity of {velocity} m/s. "
        f"Calculate the total kinetic energy of the vehicle in joules (J) using E_k = 0.5 * m * v^2."
    )
    expr = f"0.5 * {mass} * ({velocity}**2)"
    val = round(safe_eval(expr), 2)
    steps = [
        f"Record physical quantities: mass m = {mass} kg, velocity v = {velocity} m/s.",
        "Governing physical law for classical kinetic energy: E_k = 1/2 * m * v^2.",
        f"Substitute quantities into equation: 0.5 * {mass} * ({velocity}^2).",
        "Call the calculator tool to compute the kinetic energy in joules.",
    ]
    return {
        "category": "physics_math",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_physics_rc_cutoff(rng: random.Random) -> dict[str, Any]:
    r_kohm = rng.randint(2, 50)
    c_nf = rng.randint(5, 200)
    question = (
        f"An analog signal conditioning filter circuit features a series resistor R = {r_kohm} kOhms and shunt capacitor C = {c_nf} nF. "
        f"What is the -3dB cutoff frequency f_c (Hz) of this first-order low-pass filter? (Use formula f_c = 1 / (2 * pi * R * C))."
    )
    # R in ohms = r_kohm * 1e3, C in farads = c_nf * 1e-9
    expr = f"1.0 / (2 * {round(math.pi, 6)} * ({r_kohm} * 1e3) * ({c_nf} * 1e-9))"
    val = round(safe_eval(expr), 3)
    steps = [
        f"Convert component values to base SI units: R = {r_kohm} kOhm = {r_kohm}e3 Ohm, C = {c_nf} nF = {c_nf}e-9 F.",
        "Recall cutoff frequency expression for first-order RC filter: f_c = 1 / (2 * pi * R * C).",
        f"Formulate expression using pi approx {round(math.pi, 6)}: {expr}.",
        "Invoke the calculator tool to evaluate the cutoff frequency in Hertz.",
    ]
    return {
        "category": "physics_math",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_math_geometry(rng: random.Random) -> dict[str, Any]:
    radius = round(rng.uniform(2.5, 18.0), 1)
    height = round(rng.uniform(5.0, 40.0), 1)
    question = (
        f"A cylindrical coolant reservoir has a circular radius of {radius} meters and a vertical height of {height} meters. "
        f"Compute the total enclosed volume of the cylinder in cubic meters using V = pi * r^2 * h."
    )
    expr = f"{round(math.pi, 6)} * ({radius}**2) * {height}"
    val = round(safe_eval(expr), 3)
    steps = [
        f"Extract dimensions: base radius r = {radius} m, cylinder height h = {height} m.",
        "Formula for volume of a right circular cylinder: V = pi * r^2 * h.",
        f"Set up calculation: {round(math.pi, 6)} * ({radius}^2) * {height}.",
        "Execute calculation using the calculator tool.",
    ]
    return {
        "category": "physics_math",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_physics_math_unit(rng: random.Random) -> dict[str, Any]:
    variants = [
        ("km", "mi", round(rng.uniform(10.0, 450.0), 1)),
        ("mi", "km", round(rng.uniform(10.0, 300.0), 1)),
        ("m", "ft", round(rng.uniform(1.5, 120.0), 1)),
        ("ft", "m", round(rng.uniform(5.0, 400.0), 1)),
        ("kg", "lb", round(rng.uniform(5.0, 250.0), 1)),
        ("lb", "kg", round(rng.uniform(10.0, 500.0), 1)),
        ("c", "f", round(rng.uniform(-20.0, 110.0), 1)),
        ("f", "c", round(rng.uniform(0.0, 230.0), 1)),
    ]
    from_u, to_u, val = rng.choice(variants)
    unit_names = {
        "km": "kilometers", "mi": "miles", "m": "meters", "ft": "feet",
        "kg": "kilograms", "lb": "pounds", "c": "degrees Celsius", "f": "degrees Fahrenheit"
    }
    question = (
        f"An experimental telemetry test logs a temperature or distance measurement of {val} {unit_names[from_u]}. "
        f"Convert this physical quantity into {unit_names[to_u]} for cross-laboratory validation."
    )
    steps = [
        f"Input specification: {val} {unit_names[from_u]} ({from_u}).",
        f"Target specification: {unit_names[to_u]} ({to_u}).",
        "Call the unit_converter tool with the magnitude and unit strings.",
    ]
    res = round(convert_units(val, from_u, to_u), 6)
    return {
        "category": "physics_math",
        "question": question,
        "tool": "unit_converter",
        "arguments": {"value": val, "from_unit": from_u, "to_unit": to_u},
        "reasoning_steps": steps,
        "expected_result": res,
    }


# -----------------------------------------------------------------------------
# Synthetic Data Generators: Finance, Cloud & Analytics
# -----------------------------------------------------------------------------
def gen_cloud_cost(rng: random.Random) -> dict[str, Any]:
    hourly_rate = round(rng.uniform(2.50, 16.00), 2)
    instances = rng.randint(4, 48)
    days = rng.choice([7, 14, 30, 90])
    discount_pct = rng.choice([0, 10, 15, 20, 25])
    question = (
        f"A machine learning pipeline runs {instances} dedicated GPU instances costing ${hourly_rate}/hour each continuously for {days} days. "
        f"The cloud provider offers a committed-use discount of {discount_pct}%. "
        f"What is the total billed cloud compute cost in dollars?"
    )
    hours = days * 24
    expr = f"({instances} * {hourly_rate} * {hours}) * (1.0 - {discount_pct} / 100)"
    val = round(safe_eval(expr), 2)
    steps = [
        f"Determine total instance-hours: {instances} instances * ({days} days * 24 hours/day) = {instances * hours} hours.",
        f"Compute gross expense: {instances * hours} hours * ${hourly_rate}/hr.",
        f"Factor in {discount_pct}% volume discount: gross * (1 - {discount_pct}/100).",
        f"Construct expression: {expr} and evaluate with calculator.",
    ]
    return {
        "category": "finance_analytics",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_server_capacity(rng: random.Random) -> dict[str, Any]:
    peak_qps = rng.randint(2500, 45000)
    server_qps_capacity = rng.randint(400, 1800)
    headroom_factor = round(rng.uniform(1.2, 1.5), 2)
    question = (
        f"An edge API service experiences peak incoming traffic of {peak_qps} queries per second (QPS). "
        f"A single backend container replica can reliably service {server_qps_capacity} QPS. "
        f"To withstand sudden surges, the architecture requires an N+1 redundancy factor of {headroom_factor}. "
        f"Calculate the minimum number of container replicas required: ({peak_qps} * {headroom_factor}) / {server_qps_capacity}."
    )
    expr = f"({peak_qps} * {headroom_factor}) / {server_qps_capacity}"
    val = round(safe_eval(expr), 2)
    steps = [
        f"Identify peak traffic load: {peak_qps} QPS.",
        f"Apply redundancy scaling multiplier: {headroom_factor} => target throughput is {peak_qps} * {headroom_factor} QPS.",
        f"Divide by per-replica processing capability of {server_qps_capacity} QPS.",
        f"Invoke calculator with expression: {expr}.",
    ]
    return {
        "category": "finance_analytics",
        "question": question,
        "tool": "calculator",
        "arguments": {"expression": expr},
        "reasoning_steps": steps,
        "expected_result": val,
    }


def gen_analytics_unit(rng: random.Random) -> dict[str, Any]:
    variants = [
        ("s", "hr", rng.choice([3600, 7200, 14400, 28800, 86400, 172800])),
        ("hr", "s", round(rng.uniform(0.5, 48.0), 1)),
        ("min", "s", rng.randint(15, 600)),
        ("s", "min", rng.choice([300, 600, 1200, 1800, 3600])),
        ("wh", "kwh", rng.randint(500, 85000)),
        ("kwh", "wh", round(rng.uniform(1.5, 75.0), 2)),
    ]
    from_u, to_u, val = rng.choice(variants)
    unit_names = {
        "s": "seconds", "hr": "hours", "min": "minutes", "wh": "watt-hours", "kwh": "kilowatt-hours"
    }
    question = (
        f"A data center workload execution profile records a job runtime or battery consumption of {val} {unit_names[from_u]}. "
        f"Convert this measurement into {unit_names[to_u]} for the weekly executive capacity report."
    )
    steps = [
        f"Analyze source measurement: {val} {unit_names[from_u]} ({from_u}).",
        f"Target metric: {unit_names[to_u]} ({to_u}).",
        "Invoke unit_converter to perform the exact unit scaling.",
    ]
    res = round(convert_units(val, from_u, to_u), 6)
    return {
        "category": "finance_analytics",
        "question": question,
        "tool": "unit_converter",
        "arguments": {"value": val, "from_unit": from_u, "to_unit": to_u},
        "reasoning_steps": steps,
        "expected_result": res,
    }


# -----------------------------------------------------------------------------
# Row Construction & Rendering
# -----------------------------------------------------------------------------
def build_row(case_id: str, split: str, item: dict[str, Any], tokenizer: Any | None = None) -> dict[str, Any]:
    reasoning_text = "\n".join(f"{i}. {s}" for i, s in enumerate(item["reasoning_steps"], 1))
    think_block = f"<think>\n{reasoning_text}\n</think>"
    tool_call_payload = {
        "name": item["tool"],
        "arguments": item["arguments"]
    }
    tool_call_json = json.dumps(tool_call_payload, ensure_ascii=False)
    assistant_text = f"{think_block}\n\n<tool_call>\n{tool_call_json}\n</tool_call>"

    call_id = f"call_{case_id.split('_')[-1]}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": item["question"]},
        {
            "role": "assistant",
            "content": think_block,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": item["tool"],
                        "arguments": item["arguments"]
                    }
                }
            ]
        }
    ]

    rendered_text = ""
    token_count = 0
    if tokenizer is not None:
        rendered_text = tokenizer.apply_chat_template(messages, tools=TOOLS, tokenize=False)
        token_count = len(tokenizer.encode(rendered_text))

    return {
        "id": case_id,
        "split": split,
        "source": SOURCE,
        "category": item["category"],
        "question": item["question"],
        "tools": TOOLS,
        "messages": messages,
        "metadata": {
            "tool": item["tool"],
            "expected_arguments": item["arguments"],
            "reasoning_steps": item["reasoning_steps"],
            "expected_result": item["expected_result"],
        },
        "text": rendered_text,
        "tokens": token_count,
    }


# -----------------------------------------------------------------------------
# Generator Main Loop
# -----------------------------------------------------------------------------
def generate_all(
    train_count: int,
    eval_count: int,
    seed: int,
    tokenizer_path: Path,
    out_dir: Path
) -> tuple[Path, Path]:
    rng = random.Random(seed)
    tokenizer = None
    if tokenizer_path.exists():
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))
    else:
        print(f"[WARN] Tokenizer path {tokenizer_path} not found. Skipping chat template pre-rendering.")

    generators = [
        # VLSI
        gen_vlsi_timing, gen_vlsi_power, gen_vlsi_yield, gen_vlsi_unit,
        # HPC
        gen_hpc_cluster_power, gen_hpc_zero3_memory, gen_hpc_unit,
        # Physics / Math
        gen_physics_kinetic, gen_physics_rc_cutoff, gen_math_geometry, gen_physics_math_unit,
        # Finance / Analytics
        gen_cloud_cost, gen_server_capacity, gen_analytics_unit,
    ]

    seen_questions: set[str] = set()

    def sample_unique_items(target_n: int) -> list[dict[str, Any]]:
        items = []
        while len(items) < target_n:
            fn = rng.choice(generators)
            data = fn(rng)
            if data["question"] not in seen_questions:
                seen_questions.add(data["question"])
                items.append(data)
        return items

    print(f"[*] Generating {train_count} train rows and {eval_count} eval rows (seed={seed})...")
    train_items = sample_unique_items(train_count)
    eval_items = sample_unique_items(eval_count)

    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "combined_train.jsonl"
    eval_path = out_dir / "combined_eval.jsonl"

    with open(train_path, "w", encoding="utf-8") as fh:
        for idx, item in enumerate(train_items, 1):
            row = build_row(f"comb_train_{idx:04d}", "train", item, tokenizer)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(eval_path, "w", encoding="utf-8") as fh:
        for idx, item in enumerate(eval_items, 1):
            row = build_row(f"comb_eval_{idx:04d}", "eval", item, tokenizer)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[+] Wrote train dataset: {train_path} ({train_count} rows, sha256={sha256_file(train_path)[:12]}...)")
    print(f"[+] Wrote eval dataset:  {eval_path} ({eval_count} rows, sha256={sha256_file(eval_path)[:12]}...)")
    return train_path, eval_path


def check_dataset(train_path: Path, eval_path: Path) -> int:
    print(f"[*] Running dry-run validation on dataset...")
    for label, path in [("TRAIN", train_path), ("EVAL", eval_path)]:
        if not path.exists():
            print(f"[FAIL] {label} file does not exist: {path}")
            return 1

        rows = []
        with open(path, "r", encoding="utf-8") as fh:
            for lno, line in enumerate(fh, 1):
                try:
                    row = json.loads(line)
                    rows.append(row)
                except Exception as exc:
                    print(f"[FAIL] {label} line {lno} invalid JSON: {exc}")
                    return 1

        tool_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        token_lengths: list[int] = []

        for r in rows:
            for key in ["id", "split", "source", "category", "question", "tools", "messages", "metadata", "text", "tokens"]:
                if key not in r:
                    print(f"[FAIL] Missing key '{key}' in row {r.get('id')}")
                    return 1

            cat = r["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

            tool = r["metadata"]["tool"]
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

            text = r["text"]
            if "<think>" not in text or "</think>" not in text:
                print(f"[FAIL] Missing <think> block in row {r['id']}")
                return 1
            if "<tool_call>" not in text or "</tool_call>" not in text:
                print(f"[FAIL] Missing <tool_call> block in row {r['id']}")
                return 1

            # Check order: think must precede tool_call
            think_idx = text.find("</think>")
            tool_idx = text.find("<tool_call>")
            if think_idx == -1 or tool_idx == -1 or think_idx > tool_idx:
                print(f"[FAIL] Incorrect tag ordering in row {r['id']}")
                return 1

            token_lengths.append(r["tokens"])

        avg_tokens = sum(token_lengths) / len(token_lengths) if token_lengths else 0
        min_tokens = min(token_lengths) if token_lengths else 0
        max_tokens = max(token_lengths) if token_lengths else 0

        print(f"\n--- {label} SET SUMMARY ({len(rows)} rows) ---")
        print(f"Categories: {category_counts}")
        print(f"Tools:      {tool_counts}")
        print(f"Tokens:     min={min_tokens}, avg={avg_tokens:.1f}, max={max_tokens}")

    # Check zero overlap between train and eval questions
    with open(train_path, "r", encoding="utf-8") as fh:
        train_q = {json.loads(line)["question"] for line in fh if line.strip()}
    with open(eval_path, "r", encoding="utf-8") as fh:
        eval_q = {json.loads(line)["question"] for line in fh if line.strip()}

    overlap = train_q.intersection(eval_q)
    if overlap:
        print(f"[FAIL] Detected {len(overlap)} overlapping questions between train and eval sets!")
        return 1
    print(f"\n[OK] Zero question overlap verified ({len(train_q)} train vs {len(eval_q)} eval).")
    print(f"RESULT: PHASE7_DATASET_VALIDATION_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 7 combined dataset")
    parser.add_argument("--train-count", type=int, default=150, help="Number of training rows (default: 150)")
    parser.add_argument("--eval-count", type=int, default=30, help="Number of evaluation rows (default: 30)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--tokenizer", type=Path, default=DEFAULT_TOKENIZER, help="Tokenizer path")
    parser.add_argument("--check-only", action="store_true", help="Dry-run validate existing datasets without regenerating")
    args = parser.parse_args()

    train_path = args.out_dir / "combined_train.jsonl"
    eval_path = args.out_dir / "combined_eval.jsonl"

    if args.check_only:
        return check_dataset(train_path, eval_path)

    generate_all(args.train_count, args.eval_count, args.seed, args.tokenizer, args.out_dir)
    return check_dataset(train_path, eval_path)


if __name__ == "__main__":
    sys.exit(main())
