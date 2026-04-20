from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client.parser import load_sample_payload, parse_user


def test_parse_user_output_shape() -> None:
    payload = load_sample_payload()
    user = parse_user(payload)

    assert set(user.keys()) == {"id", "name", "email"}
    assert isinstance(user["id"], int)
    assert "@" in user["email"]
    assert len(user["name"]) > 0
