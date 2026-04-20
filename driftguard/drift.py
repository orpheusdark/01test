from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


def apply_schema_drift(repo_root: str) -> Dict[str, Any]:
    root = Path(repo_root)
    (root / "schemas" / "active_schema.txt").write_text("user_v2.schema.json\n", encoding="utf-8")

    payload_v2 = {
        "id": 123,
        "full_name": "Ada Lovelace",
        "contact": {"email": "ada@example.com"},
        "role": "admin",
    }
    (root / "samples" / "current_payload.json").write_text(
        json.dumps(payload_v2, indent=2) + "\n", encoding="utf-8"
    )
    return {"drift_applied": True, "active_schema": "user_v2.schema.json"}


def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "name" in payload:
        return {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "email": payload.get("email"),
        }
    return {
        "id": payload.get("id"),
        "name": payload.get("full_name"),
        "email": payload.get("contact", {}).get("email") if isinstance(payload.get("contact"), dict) else None,
    }
