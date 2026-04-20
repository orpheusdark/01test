from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List

import jsonschema

from .actors import RequesterActor, SecurityActor, OversightActor


AVAILABLE_TOOLS = [
    "read_file",
    "search",
    "apply_patch",
    "run_tests",
    "validate_schema",
    "policy_scan",
    "ask_requester",
    "ask_security",
    "submit_for_review",
]


def _safe_path(root: Path, rel_path: str) -> Path:
    p = (root / rel_path).resolve()
    if not str(p).startswith(str(root.resolve())):
        raise ValueError("Path escapes repository root")
    return p


def read_file(repo_root: str, path: str) -> Dict[str, Any]:
    root = Path(repo_root)
    p = _safe_path(root, path)
    if not p.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    return {"ok": True, "path": path, "content": p.read_text(encoding="utf-8")}


def search(repo_root: str, pattern: str) -> Dict[str, Any]:
    root = Path(repo_root)
    results: List[Dict[str, Any]] = []
    regex = re.compile(pattern)
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if ".pytest_cache" in file_path.parts or "__pycache__" in file_path.parts:
            continue
        rel = file_path.relative_to(root).as_posix()
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                results.append({"path": rel, "line": idx, "text": line.strip()})
    return {"ok": True, "matches": results[:200], "count": len(results)}


def apply_patch(repo_root: str, path: str, old: str, new: str) -> Dict[str, Any]:
    root = Path(repo_root)
    p = _safe_path(root, path)
    if not p.exists():
        return {"ok": False, "error": f"File not found: {path}"}
    content = p.read_text(encoding="utf-8")
    if old not in content:
        return {"ok": False, "error": "Target snippet not found for replacement"}
    updated = content.replace(old, new, 1)
    p.write_text(updated, encoding="utf-8")
    return {"ok": True, "path": path, "changed": True}


def run_tests(repo_root: str) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        ["python", "-m", "pytest", "-q"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def validate_schema(repo_root: str) -> Dict[str, Any]:
    root = Path(repo_root)
    active_name = (root / "schemas" / "active_schema.txt").read_text(encoding="utf-8").strip()
    schema = json.loads((root / "schemas" / active_name).read_text(encoding="utf-8"))
    payload = json.loads((root / "samples" / "current_payload.json").read_text(encoding="utf-8"))

    try:
        jsonschema.validate(payload, schema)
        return {"ok": True, "active_schema": active_name}
    except jsonschema.ValidationError as exc:
        return {"ok": False, "active_schema": active_name, "error": str(exc)}


def policy_scan(repo_root: str) -> Dict[str, Any]:
    from .repo_snapshot.policies.policy_scan import scan_repo

    return scan_repo(repo_root)


def ask_requester(question: str, seed: int = 0) -> Dict[str, Any]:
    return RequesterActor(seed=seed).respond(question)


def ask_security(question: str, seed: int = 0) -> Dict[str, Any]:
    return SecurityActor(seed=seed).respond(question)


def submit_for_review(summary: str, status: Dict[str, bool], seed: int = 0) -> Dict[str, Any]:
    return OversightActor(seed=seed).review(summary=summary, status=status)
