from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from .env import DriftGuardEnv
from .state import EpisodeResult, Observation


PolicyFn = Callable[[Observation], Dict[str, Any]]


def compute_metrics(results: List[EpisodeResult]) -> Dict[str, Any]:
    if not results:
        return {
            "episodes": 0,
            "success_rate": 0.0,
            "avg_reward": 0.0,
            "avg_steps": 0.0,
            "tests_pass_rate": 0.0,
            "schema_pass_rate": 0.0,
            "policy_pass_rate": 0.0,
        }

    n = len(results)
    success_rate = sum(1 for r in results if r.success) / n
    avg_reward = sum(r.total_reward for r in results) / n
    avg_steps = sum(r.steps for r in results) / n
    tests_rate = sum(1 for r in results if r.status.get("tests_passed")) / n
    schema_rate = sum(1 for r in results if r.status.get("schema_passed")) / n
    policy_rate = sum(1 for r in results if r.status.get("policy_passed")) / n

    return {
        "episodes": n,
        "success_rate": round(success_rate, 4),
        "avg_reward": round(avg_reward, 4),
        "avg_steps": round(avg_steps, 4),
        "tests_pass_rate": round(tests_rate, 4),
        "schema_pass_rate": round(schema_rate, 4),
        "policy_pass_rate": round(policy_rate, 4),
    }


def run_batch(policy_fn: PolicyFn, episodes: int = 10, seed: int = 0, step_limit: int = 15) -> Tuple[Dict[str, Any], List[EpisodeResult]]:
    results: List[EpisodeResult] = []
    for i in range(episodes):
        env = DriftGuardEnv(step_limit=step_limit, seed=seed + i)
        obs = env.reset(seed=seed + i)
        done = False
        while not done:
            action = policy_fn(obs)
            obs, _, done, _ = env.step(action)
        results.append(env.episode_result())
        env.close()
    return compute_metrics(results), results
