from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from driftguard.env import DriftGuardEnv
from driftguard.state import Observation


SMART_OLD_SNIPPET = '''
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
'''.strip("\n")

SMART_NEW_SNIPPET = '''
def parse_user(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Supports v1 and v2 while returning canonical output keys."""
    active = _active_schema_name()

    if active == "user_v1.schema.json":
        return {
            "id": int(payload["id"]),
            "name": str(payload["name"]),
            "email": str(payload["email"]),
        }

    email = payload.get("email")
    if email is None and isinstance(payload.get("contact"), dict):
        email = payload["contact"].get("email")
    if not email:
        email = "unknown@example.com"

    name = payload.get("name")
    if name is None:
        name = payload.get("full_name")
    if not name:
        name = "unknown"

    return {
        "id": int(payload["id"]),
        "name": str(name),
        "email": str(email),
    }
'''.strip("\n")


def naive_policy(obs: Observation) -> Dict[str, Any]:
    step = obs.step
    if step == 0:
        return {"tool": "read_file", "args": {"path": "client/parser.py"}}
    if step % 3 == 1:
        return {"tool": "run_tests", "args": {}}
    if step % 3 == 2:
        return {"tool": "validate_schema", "args": {}}
    if step % 3 == 0:
        return {"tool": "policy_scan", "args": {}}
    return {"tool": "submit_for_review", "args": {"summary": "tests schema policy checked"}}


def smart_policy(obs: Observation) -> Dict[str, Any]:
    last = obs.last_tool_result or {}

    if obs.step == 0:
        return {"tool": "ask_requester", "args": {"question": "What field changed in the schema?"}}
    if obs.step == 1:
        return {"tool": "ask_security", "args": {"question": "Any PII logging constraints?"}}

    if obs.status.get("tests_passed") is False:
        if last.get("returncode", 0) != 0 and "KeyError: 'name'" in last.get("stdout", ""):
            return {
                "tool": "apply_patch",
                "args": {
                    "path": "client/parser.py",
                    "old": SMART_OLD_SNIPPET,
                    "new": SMART_NEW_SNIPPET,
                },
            }
        return {"tool": "run_tests", "args": {}}

    if not obs.status.get("schema_passed"):
        return {"tool": "validate_schema", "args": {}}

    if not obs.status.get("policy_passed"):
        return {"tool": "policy_scan", "args": {}}

    return {
        "tool": "submit_for_review",
        "args": {"summary": "Updated parser, validated tests/schema/policy with drift support."},
    }


def select_policy(name: str):
    if name == "naive":
        return naive_policy
    if name == "smart":
        return smart_policy
    raise ValueError(f"Unknown agent: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one DriftGuard rollout")
    parser.add_argument("--agent", choices=["naive", "smart"], default="smart")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--step-limit", type=int, default=15)
    args = parser.parse_args()

    env = DriftGuardEnv(step_limit=args.step_limit, seed=args.seed)
    obs = env.reset(seed=args.seed)
    policy = select_policy(args.agent)

    done = False
    while not done:
        action = policy(obs)
        obs, reward, done, info = env.step(action)
        print(
            json.dumps(
                {
                    "step": obs.step,
                    "action": action,
                    "reward": round(reward, 4),
                    "status": info["status"],
                    "drift": info.get("drift"),
                }
            )
        )

    result = env.episode_result()
    print("\n=== FINAL ===")
    print(
        json.dumps(
            {
                "success": result.success,
                "total_reward": round(result.total_reward, 4),
                "steps": result.steps,
                "status": result.status,
            },
            indent=2,
        )
    )
    env.close()


if __name__ == "__main__":
    main()
