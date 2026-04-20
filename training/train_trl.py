from __future__ import annotations

import argparse
import json
import random
from typing import Dict, Any

from driftguard.eval import run_batch
from scripts.run_rollout import smart_policy


def random_policy(_obs) -> Dict[str, Any]:
    # Deliberately weak policy for demonstration.
    tools = ["run_tests", "validate_schema", "policy_scan", "read_file"]
    tool = random.choice(tools)
    if tool == "read_file":
        return {"tool": "read_file", "args": {"path": "client/parser.py"}}
    return {"tool": tool, "args": {}}


def maybe_run_trl_placeholder() -> None:
    try:
        import trl  # noqa: F401
        print("TRL detected: plug environment trajectories into PPO/SFT pipeline here.")
    except Exception:
        print("TRL not installed; running offline placeholder trainer only.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal DriftGuard training stub")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    maybe_run_trl_placeholder()

    # Offline placeholder: evaluate weak policy, then evaluate scripted policy.
    random_metrics, _ = run_batch(policy_fn=random_policy, episodes=max(5, args.episodes // 2), seed=args.seed)
    smart_metrics, _ = run_batch(policy_fn=smart_policy, episodes=max(5, args.episodes // 2), seed=args.seed + 1000)

    report = {
        "placeholder_training": {
            "random_policy": random_metrics,
            "smart_policy": smart_metrics,
        }
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
