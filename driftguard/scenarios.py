from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Any, List


def generate_ticket(seed: int, drift_step: int = 4) -> Dict[str, Any]:
    rng = random.Random(seed)
    ticket_id = f"DG-{seed:04d}-{rng.randint(100, 999)}"
    return {
        "ticket_id": ticket_id,
        "title": "Upstream JSON response schema changed",
        "description": (
            "Production payload contract drifted. Migrate parser + tests/docs so checks pass "
            "under the new schema without violating policy."
        ),
        "initial_schema": "user_v1.schema.json",
        "target_schema": "user_v2.schema.json",
        "drift_step": drift_step,
    }


def adversarial_drift_mutator(ticket: Dict[str, Any], seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    mutated = dict(ticket)
    mutated["drift_step"] = max(1, int(ticket.get("drift_step", 4)) - rng.randint(0, 2))
    mutated["description"] += " Adversarial mode: drift may happen earlier than expected."
    return mutated


def write_jsonl_episodes(path: str, count: int, seed: int = 0) -> List[Dict[str, Any]]:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    episodes: List[Dict[str, Any]] = []
    with out.open("w", encoding="utf-8") as f:
        for i in range(count):
            ticket = generate_ticket(seed=seed + i, drift_step=4)
            f.write(json.dumps(ticket) + "\n")
            episodes.append(ticket)
    return episodes
