"""
lockout.py
-----------
Tracks attempts to reference real copyrighted artists/songs in the prompt
box (as flagged by prompt_parser) and locks the app for 24 hours after
3 such attempts. State is a small JSON file in the user's home directory,
so the lockout survives app restarts.
"""

import json
import os
from datetime import datetime, timedelta, timezone

MAX_VIOLATIONS = 3
LOCK_DURATION_HOURS = 24

_STATE_DIR = os.path.join(os.path.expanduser("~"), ".original_music_generator")
_STATE_PATH = os.path.join(_STATE_DIR, "lockout_state.json")


def _default_state():
    return {"violations": 0, "locked_until": None}


def _load_state():
    try:
        with open(_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        state = _default_state()
        state.update(data)
        return state
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _default_state()


def _save_state(state):
    try:
        os.makedirs(_STATE_DIR, exist_ok=True)
        with open(_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except OSError:
        pass


def _parse_locked_until(state):
    raw = state.get("locked_until")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def is_locked():
    """Returns (locked: bool, locked_until: datetime | None)."""
    state = _load_state()
    locked_until = _parse_locked_until(state)
    if locked_until is None:
        return False, None

    now = datetime.now(timezone.utc)
    if now >= locked_until:
        # lock has expired - clear it out for a fresh start
        _save_state(_default_state())
        return False, None

    return True, locked_until


def register_violation():
    """
    Record one blocked-prompt attempt.
    Returns (violation_count, newly_locked: bool, locked_until: datetime | None).
    """
    locked, locked_until = is_locked()
    if locked:
        return MAX_VIOLATIONS, False, locked_until

    state = _load_state()
    state["violations"] = state.get("violations", 0) + 1

    if state["violations"] >= MAX_VIOLATIONS:
        locked_until = datetime.now(timezone.utc) + timedelta(hours=LOCK_DURATION_HOURS)
        state["locked_until"] = locked_until.isoformat()
        state["violations"] = 0
        _save_state(state)
        return MAX_VIOLATIONS, True, locked_until

    _save_state(state)
    return state["violations"], False, None


def remaining_time_str(locked_until):
    if locked_until is None:
        return "0h 0m"
    now = datetime.now(timezone.utc)
    remaining = locked_until - now
    if remaining.total_seconds() <= 0:
        return "0h 0m"
    total_minutes = int(remaining.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"
