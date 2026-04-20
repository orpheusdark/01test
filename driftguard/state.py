from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Action:
    tool: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    ticket: Dict[str, Any]
    step: int
    max_steps: int
    drift_applied: bool
    available_tools: List[str]
    last_tool_result: Optional[Dict[str, Any]] = None
    status: Dict[str, bool] = field(default_factory=dict)


@dataclass
class WorldState:
    seed: int
    step_count: int
    max_steps: int
    drift_step: int
    drift_applied: bool
    working_repo: str
    ticket: Dict[str, Any]
    status: Dict[str, bool] = field(default_factory=lambda: {
        "tests_passed": False,
        "schema_passed": False,
        "policy_passed": False,
    })
    failure_counts: Dict[str, int] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EpisodeResult:
    success: bool
    total_reward: float
    steps: int
    status: Dict[str, bool]
    trace: List[Dict[str, Any]]
