from __future__ import annotations

from client.parser import load_sample_payload, parse_user


def test_parse_user_output_shape() -> None:
    payload = load_sample_payload()
    user = parse_user(payload)

    assert set(user.keys()) == {"id", "name", "email"}
    assert isinstance(user["id"], int)
    assert "@" in user["email"]
    assert len(user["name"]) > 0
