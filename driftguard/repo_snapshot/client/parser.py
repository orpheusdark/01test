from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _active_schema_name() -> str:
    return (_repo_root() / "schemas" / "active_schema.txt").read_text(encoding="utf-8").strip()


def parse_user(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Initial parser supports v1 only; migration should add v2 compatibility."""
    active = _active_schema_name()

    if active == "user_v1.schema.json":
        return {
            "id": int(payload["id"]),
            "name": str(payload["name"]),
            "email": str(payload["email"]),
        }

    # Drifted behavior currently broken until agent patches this.
    return {
        "id": int(payload["id"]),
        "name": str(payload["name"]),
        "email": str(payload["email"]),
    }


def load_sample_payload() -> Dict[str, Any]:
    return json.loads((_repo_root() / "samples" / "current_payload.json").read_text(encoding="utf-8"))
