"""
restrictions.py
-----------------
Tracks repeated attempts to reference real copyrighted artists/songs in
the prompt box (as flagged by prompt_parser) and, if it keeps happening,
progressively turns off individual features for 24 hours at a time -
never the app itself, which always still opens. State is a small JSON
file kept in this app's own local data folder (contained to this app on
this one PC - not system-wide, never roaming to another machine).

Escalation ladder (the violation count persists across restarts, but is
never used to block the app from launching, and never reaches every
feature - generating music is never disabled, so there's always
something the app can still do):

    3 violations  -> the description box is disabled for 24 hours
    2 more (5)    -> in-app playback is also disabled for 24 hours
    2 more (7+)   -> exporting WAV files is also disabled for 24 hours,
                     which is as far as it goes - you can still generate
                     music the whole time, just not describe it in free
                     text, preview it in-app, or export it until the
                     restriction passes.

Each new threshold re-locks everything up to that point for a fresh 24
hours. If a lock window passes with no further violation, the
restriction lifts completely. If the filter is triggered again after
that, escalation resumes from wherever the ladder left off - once the
top of the ladder is reached, any further attempt (after the previous
window has passed) simply re-locks everything at that same top tier.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

FIRST_THRESHOLD = 3
STEP_THRESHOLD = 2
LOCK_DURATION_HOURS = 24

APP_FOLDER_NAME = "Original Music Generator"

FEATURES = ["prompt_box", "play", "export"]
FEATURE_LABELS = {
    "prompt_box": "the description box",
    "play": "in-app playback (Play)",
    "export": "exporting WAV files (Export WAV)",
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
    return {"violations": 0, "tier": 0, "locked_until": None}


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


def _tier_for(violations):
    """How many features (from the front of FEATURES) a given total
    violation count corresponds to. 0 = none."""
    if violations < FIRST_THRESHOLD:
        return 0
    tier = 1 + (violations - FIRST_THRESHOLD) // STEP_THRESHOLD
    return min(tier, len(FEATURES))


def active_restrictions():
    """
    Returns (disabled_features: list[str], locked_until: datetime | None).
    Empty list if nothing is currently restricted (either never
    triggered, or the most recent lock window has passed).
    """
    state = _load_state()
    locked_until = _parse_locked_until(state)
    if locked_until is None:
        return [], None

    now = datetime.now(timezone.utc)
    if now >= locked_until:
        return [], None

    tier = state.get("tier", 0)
    return FEATURES[:tier], locked_until


def register_violation():
    """
    Record one blocked-prompt attempt. Only meaningful to call while the
    prompt box is actually enabled, which - by construction - means no
    restriction window is currently active.

    Returns (disabled_features: list[str], newly_escalated: bool,
    locked_until: datetime | None, attempts_until_next_escalation: int | None).
    When disabled_features is empty, nothing is restricted yet and
    attempts_until_next_escalation says how many more blocked prompts
    would trigger (or extend) a restriction.
    """
    state = _load_state()
    state["violations"] = state.get("violations", 0) + 1
    violations = state["violations"]

    prev_tier = state.get("tier", 0)
    target_tier = _tier_for(violations)
    at_ceiling = prev_tier >= len(FEATURES)

    if target_tier > prev_tier or at_ceiling:
        tier = max(target_tier, prev_tier)
        locked_until = datetime.now(timezone.utc) + timedelta(hours=LOCK_DURATION_HOURS)
        state["tier"] = tier
        state["locked_until"] = locked_until.isoformat()
        _save_state(state)
        newly_escalated = tier > prev_tier
        return FEATURES[:tier], newly_escalated, locked_until, None

    _save_state(state)
    if violations < FIRST_THRESHOLD:
        next_in = FIRST_THRESHOLD - violations
    else:
        next_in = STEP_THRESHOLD - ((violations - FIRST_THRESHOLD) % STEP_THRESHOLD)
    return [], False, None, next_in


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
