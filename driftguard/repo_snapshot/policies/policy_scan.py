from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from .policy_rules import BANNED_PATTERNS


SCAN_EXTENSIONS = {".py", ".md", ".txt", ".json"}


def scan_repo(repo_root: str) -> Dict[str, Any]:
    root = Path(repo_root)
    violations: List[Dict[str, Any]] = []

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        if ".pytest_cache" in p.parts or "__pycache__" in p.parts:
            continue
        if p.name == "policy_rules.py":
            continue

        rel = p.relative_to(root).as_posix()
        text = p.read_text(encoding="utf-8", errors="ignore")
        for rule in BANNED_PATTERNS:
            if rule in text:
                violations.append({"path": rel, "pattern": rule})

    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "count": len(violations),
    }
