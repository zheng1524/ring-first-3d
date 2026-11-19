"""Load selected, SHA-locked definitions without historical imports/main/side effects."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

LOCK = json.loads(Path(__file__).with_name("source_lock.json").read_text())
ROOT = Path(__file__).resolve().parents[2]
REGISTRY_SNAPSHOT = "fa649fa1cf20b111bfdb8489e8af20ba90339bba"


def source(key):
    rec = LOCK["sources"][key]
    root = Path(os.environ.get("RING_FIRST_SOURCE_ROOT", ROOT))
    p = root / rec["path"]
    if p.is_file():
        raw = p.read_bytes()
    else:
        # A main-ready shallow checkout may have the registry snapshot without
        # its historical parent commit. Both locations must pass the same SHA.
        try:
            raw = subprocess.check_output(["git", "-C", str(root), "show",
                                           rec["commit"] + ":" + rec["path"]], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raw = subprocess.check_output(["git", "-C", str(root), "show",
                                           REGISTRY_SNAPSHOT + ":" + rec["path"]], stderr=subprocess.PIPE)
    if hashlib.sha256(raw).hexdigest() != rec["sha256"]:
        raise ValueError("Historical source SHA mismatch: " + key)
    return ast.parse(raw, filename=rec["path"])


def definitions(key, names, namespace):
    tree = source(key)
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    if {n.name for n in nodes} != set(names):
        raise ValueError("Missing historical definitions: " + key)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), LOCK["sources"][key]["path"], "exec"), namespace)
    return namespace


def main_loop_block(key, start, end, namespace):
    """Inclusive statement-boundary extraction; original AST and constants are unchanged."""
    tree = source(key)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    loops = [n for n in ast.walk(main) if isinstance(n, ast.For)]
    for loop in loops:
        starts = [i for i, n in enumerate(loop.body) if n.lineno == start]
        ends = [i for i, n in enumerate(loop.body) if n.end_lineno == end]
        if starts and ends:
            nodes = loop.body[starts[0]:ends[0] + 1]
            exec(compile(ast.Module(body=nodes, type_ignores=[]), LOCK["sources"][key]["path"], "exec"), namespace)
            return namespace
    raise ValueError(f"Historical AST block not found: {key}:{start}-{end}")


def line_statements(key, line, namespace, skip=0):
    nodes = [n for n in ast.walk(source(key)) if isinstance(n, ast.stmt) and n.lineno == line and n.end_lineno == line]
    nodes.sort(key=lambda n: n.col_offset)
    exec(compile(ast.Module(body=nodes[skip:], type_ignores=[]), LOCK["sources"][key]["path"], "exec"), namespace)
    return namespace
