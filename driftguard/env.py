from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from .drift import apply_schema_drift
from .scenarios import generate_ticket
from .state import Action, Observation, EpisodeResult, WorldState
from .tools import (
    AVAILABLE_TOOLS,
    apply_patch,
    ask_requester,
    ask_security,
    policy_scan,
    read_file,
    run_tests,
    search,
    submit_for_review,
    validate_schema,
)


class DriftGuardEnv:
    def __init__(self, step_limit: int = 15, seed: int = 0, drift_step: int = 4):
        self.step_limit = step_limit
        self.seed = seed
        self.default_drift_step = drift_step
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None
        self.world: Optional[WorldState] = None
        self.total_reward: float = 0.0

    def _repo_template(self) -> Path:
        return Path(__file__).resolve().parent / "repo_snapshot"

    def _make_working_repo(self) -> str:
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
        self._tmpdir = tempfile.TemporaryDirectory(prefix="driftguard_")
        dst = Path(self._tmpdir.name) / "repo_snapshot"
        shutil.copytree(self._repo_template(), dst)
        return str(dst)

    def reset(self, seed: Optional[int] = None) -> Observation:
        if seed is not None:
            self.seed = seed
        working_repo = self._make_working_repo()
        ticket = generate_ticket(seed=self.seed, drift_step=self.default_drift_step)
        self.world = WorldState(
            seed=self.seed,
            step_count=0,
            max_steps=self.step_limit,
            drift_step=ticket["drift_step"],
            drift_applied=False,
            working_repo=working_repo,
            ticket=ticket,
        )
        self.total_reward = 0.0
        return self._observation(last_tool_result=None)

    def _observation(self, last_tool_result: Optional[Dict[str, Any]]) -> Observation:
        assert self.world is not None
        return Observation(
            ticket=self.world.ticket,
            step=self.world.step_count,
            max_steps=self.world.max_steps,
            drift_applied=self.world.drift_applied,
            available_tools=list(AVAILABLE_TOOLS),
            last_tool_result=last_tool_result,
            status=dict(self.world.status),
        )

    def _execute_tool(self, action: Action) -> Dict[str, Any]:
        assert self.world is not None
        root = self.world.working_repo
        args = action.args or {}

        if action.tool == "read_file":
            return read_file(root, path=args.get("path", ""))
        if action.tool == "search":
            return search(root, pattern=args.get("pattern", ".*"))
        if action.tool == "apply_patch":
            return apply_patch(root, path=args.get("path", ""), old=args.get("old", ""), new=args.get("new", ""))
        if action.tool == "run_tests":
            return run_tests(root)
        if action.tool == "validate_schema":
            return validate_schema(root)
        if action.tool == "policy_scan":
            return policy_scan(root)
        if action.tool == "ask_requester":
            return ask_requester(question=args.get("question", ""), seed=self.world.seed)
        if action.tool == "ask_security":
            return ask_security(question=args.get("question", ""), seed=self.world.seed)
        if action.tool == "submit_for_review":
            return submit_for_review(summary=args.get("summary", ""), status=self.world.status, seed=self.world.seed)
        return {"ok": False, "error": f"Unknown tool: {action.tool}"}

    def _update_status(self, tool: str, result: Dict[str, Any]) -> None:
        assert self.world is not None
        if tool == "run_tests":
            self.world.status["tests_passed"] = bool(result.get("ok", False))
        elif tool == "validate_schema":
            self.world.status["schema_passed"] = bool(result.get("ok", False))
        elif tool == "policy_scan":
            self.world.status["policy_passed"] = bool(result.get("ok", False))

    def _reward(self, tool: str, result: Dict[str, Any]) -> float:
        assert self.world is not None
        reward = -0.01

        if tool in {"run_tests", "validate_schema", "policy_scan"}:
            if result.get("ok", False):
                reward += 1.0
            else:
                failures = self.world.failure_counts.get(tool, 0) + 1
                self.world.failure_counts[tool] = failures
                if failures > 1:
                    reward -= 0.05

        if tool == "submit_for_review":
            reward += 0.2 * float(result.get("explanation_score", 0.0))
            reward -= 0.1 * float(result.get("risk_flags", 0.0))

        return reward

    def step(self, action: Union[Action, Dict[str, Any]]) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        assert self.world is not None, "Call reset() first"

        if isinstance(action, dict):
            action = Action(tool=action.get("tool", ""), args=action.get("args", {}))

        self.world.step_count += 1

        drift_info = None
        if (not self.world.drift_applied) and self.world.step_count >= self.world.drift_step:
            drift_info = apply_schema_drift(self.world.working_repo)
            self.world.drift_applied = True

        result = self._execute_tool(action)
        self._update_status(action.tool, result)
        reward = self._reward(action.tool, result)
        self.total_reward += reward

        event = {
            "step": self.world.step_count,
            "tool": action.tool,
            "args": action.args,
            "result": result,
            "drift": drift_info,
            "reward": reward,
        }
        self.world.trace.append(event)

        done = all(self.world.status.values()) or self.world.step_count >= self.world.max_steps
        info = {"status": dict(self.world.status), "drift": drift_info}
        return self._observation(last_tool_result=result), reward, done, info

    def episode_result(self) -> EpisodeResult:
        assert self.world is not None
        return EpisodeResult(
            success=all(self.world.status.values()),
            total_reward=self.total_reward,
            steps=self.world.step_count,
            status=dict(self.world.status),
            trace=list(self.world.trace),
        )

    def close(self) -> None:
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None
