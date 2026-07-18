"""
restrictions.py
-----------------
Tracks repeated attempts to reference real copyrighted artists/songs in
the prompt box (as flagged by prompt_parser). After 3 such attempts,
exporting audio is disabled for 1 hour - nothing else in the app is
affected. The description box, in-app playback, and generating music
all keep working the whole time; only Export is ever restricted. State
is a small JSON file kept in this app's own local data folder
(contained to this app on this one PC - not system-wide, never roaming
to another machine).

Every 3 blocked prompts (counted from zero again after each trigger)
disables exporting for a fresh hour, whether or not a previous export
restriction was already active.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

WARNING_THRESHOLD = 3
LOCK_DURATION_HOURS = 1

APP_FOLDER_NAME = "Original Music Generator"

RESTRICTED_FEATURE = "export"
FEATURE_LABELS = {
    "export": "exporting audio files (Export)",
}


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
_STATE_PATH = os.path.join(_STATE_DIR, "restriction_state.json")


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


def active_restrictions():
    """
    Returns (disabled_features: list[str], locked_until: datetime | None).
    disabled_features is either [] or ["export"] - nothing else is ever
    restricted.
    """
    state = _load_state()
    locked_until = _parse_locked_until(state)
    if locked_until is None:
        return [], None

    now = datetime.now(timezone.utc)
    if now >= locked_until:
        return [], None

    return [RESTRICTED_FEATURE], locked_until


def register_violation():
    """
    Record one blocked-prompt attempt.
    Returns (disabled_features: list[str], newly_locked: bool,
    locked_until: datetime | None, attempts_until_lock: int | None).
    """
    state = _load_state()
    state["violations"] = state.get("violations", 0) + 1
    violations = state["violations"]

    if violations >= WARNING_THRESHOLD:
        locked_until = datetime.now(timezone.utc) + timedelta(hours=LOCK_DURATION_HOURS)
        state["violations"] = 0
        state["locked_until"] = locked_until.isoformat()
        _save_state(state)
        return [RESTRICTED_FEATURE], True, locked_until, None

    _save_state(state)
    return [], False, None, WARNING_THRESHOLD - violations


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
