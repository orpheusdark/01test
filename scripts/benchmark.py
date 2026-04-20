from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from driftguard.eval import run_batch
from scripts.run_rollout import naive_policy, smart_policy


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DriftGuard benchmark")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--step-limit", type=int, default=15)
    parser.add_argument("--agent", choices=["naive", "smart"], default="smart")
    parser.add_argument("--output", default="benchmark_metrics.json")
    args = parser.parse_args()

    policy = smart_policy if args.agent == "smart" else naive_policy
    metrics, _ = run_batch(policy_fn=policy, episodes=args.episodes, seed=args.seed, step_limit=args.step_limit)

    out = {
        "agent": args.agent,
        "metrics": metrics,
    }
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print("=== DriftGuard Benchmark ===")
    print(json.dumps(out, indent=2))
    print(f"Saved metrics to {args.output}")


if __name__ == "__main__":
    main()
