from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def test_payload_matches_active_schema() -> None:
    root = Path(__file__).resolve().parents[1]
    active_name = (root / "schemas" / "active_schema.txt").read_text(encoding="utf-8").strip()
    schema = json.loads((root / "schemas" / active_name).read_text(encoding="utf-8"))
    payload = json.loads((root / "samples" / "current_payload.json").read_text(encoding="utf-8"))
    jsonschema.validate(payload, schema)
