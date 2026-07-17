"""
lockout.py
-----------
Tracks attempts to reference real copyrighted artists/songs in the prompt
box (as flagged by prompt_parser) and locks the app for 24 hours after
3 such attempts. State is a small JSON file kept in this app's own local
data folder, so the lockout survives app restarts but stays contained to
this one app on this one PC - it's not written anywhere shared, and (on
Windows) it lives under %LOCALAPPDATA%, which never roams to other
machines, so it can never follow the user or affect anything PC-wide.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

MAX_VIOLATIONS = 3
LOCK_DURATION_HOURS = 24

APP_FOLDER_NAME = "Original Music Generator"


def _app_data_dir():
    """This app's own per-user, per-machine data folder (OS-appropriate)."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(base, APP_FOLDER_NAME)
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_FOLDER_NAME)
    xdg_data = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(xdg_data, APP_FOLDER_NAME)


_STATE_DIR = _app_data_dir()
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
