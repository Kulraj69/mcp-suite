"""Tools the server exposes. Each is a plain callable plus its MCP schema.

Kept dependency-free: sibling projects (costrouter, teval) are imported
lazily so this server still runs where they are not installed.
"""

import os
import sys

# Sibling projects live next to this repo in the portfolio workspace.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _sib in ("../../trajectory-eval", "../../cost-router"):
    _p = os.path.realpath(os.path.join(_HERE, _sib))
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)

MAX_READ_BYTES = 100_000


def _schema(props, required):
    return {"type": "object", "properties": props, "required": required}


def read_file(path: str, root: str = ".") -> str:
    """Read a UTF-8 text file inside a sandboxed root directory."""
    base = os.path.realpath(root)
    target = os.path.realpath(os.path.join(base, path))
    if not (target == base or target.startswith(base + os.sep)):
        raise ValueError("path escapes sandbox root")
    with open(target, encoding="utf-8") as f:
        data = f.read(MAX_READ_BYTES + 1)
    return data[:MAX_READ_BYTES]


def route_cost(prompt: str, expected_output_tokens: int = 512) -> str:
    """Route a prompt to the cheapest capable provider (costrouter)."""
    from costrouter.router import route
    d = route(prompt, expected_output_tokens=expected_output_tokens)
    return (f"{d.provider.name} (tier {d.provider.tier}) - "
            f"~${d.estimated_cost:.6f} for {d.estimated_input_tokens}+{d.estimated_output_tokens} tokens")


def grade_trajectory(trajectory_jsonl: str, root: str = ".") -> str:
    """Grade a golden trajectory file with teval (pass/fail + score)."""
    from teval.harness import evaluate
    from teval.schema import load_jsonl
    trajs = load_jsonl(os.path.join(root, trajectory_jsonl))
    result = evaluate(trajs, {})
    status = "PASS" if result.passed else "FAIL"
    return (f"{status}: score {result.score:.3f} across {len(result.results)} "
            f"trajectories, {result.violation_count} violations")


TOOLS = [
    ("read_file", "Read a UTF-8 text file within the sandbox root.",
     _schema({"path": {"type": "string"}, "root": {"type": "string"}}, ["path"]),
     read_file),
    ("route_cost", "Pick the cheapest model that can handle a prompt (costrouter).",
     _schema({"prompt": {"type": "string"}, "expected_output_tokens": {"type": "integer"}}, ["prompt"]),
     route_cost),
    ("grade_trajectory", "Grade a golden trajectory file (teval).",
     _schema({"trajectory_jsonl": {"type": "string"}, "root": {"type": "string"}}, ["trajectory_jsonl"]),
     grade_trajectory),
]
