"""User configuration.

The shorthand timezone list, the highlighted row, the default timezone and the
tick length all used to be module-level constants. They now come from
``$XDG_CONFIG_HOME/timepal.toml`` (``~/.config/timepal.toml`` when XDG_CONFIG_HOME
is unset), and fall back to the values below so the CLI still runs on a machine
that has no config file.

Set ``TIMEPAL_CONFIG`` to point at a different file.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rich.console import Console

DEFAULT_TIMEZONE = "Asia/Jerusalem"
DEFAULT_INCREMENT_SECONDS = 1.0
DEFAULT_TIMEZONES: dict[str, str] = {
    "LA": "America/Los_Angeles",
    "NY": "America/New_York",
    "UTC": "UTC",
    "Israel": "Asia/Jerusalem",
}

_KNOWN_KEYS = frozenset({"default_timezone", "highlight", "increment_seconds", "timezones"})


@dataclass(frozen=True)
class Config:
    default_timezone: str
    highlight: str
    increment: timedelta
    timezones: dict[str, str]


def config_path() -> Path:
    """Where the config is read from, whether or not it exists."""
    if override := os.environ.get("TIMEPAL_CONFIG"):
        return Path(override).expanduser()
    if xdg := os.environ.get("XDG_CONFIG_HOME"):
        return Path(xdg).expanduser() / "timepal.toml"
    return Path.home() / ".config" / "timepal.toml"


def _bail(message: str) -> "None":
    Console(stderr=True).print(f"[bold red]config:[/] {message}")
    sys.exit(1)


def _as_str(raw: dict, key: str, default: str) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str):
        _bail(f"[bold]{key}[/] must be a string, got {type(value).__name__}")
    return value


def _check_timezone(name: str, where: str) -> str:
    """Reject unknown zones here, where we can name the offending key.

    Otherwise a typo surfaces as a traceback from deep in the display loop.
    """
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        _bail(f"[bold]{where}[/] is not a known timezone: {name}")
    return name


def _as_timezones(raw: dict) -> dict[str, str]:
    """A user-supplied [timezones] table replaces the defaults outright.

    Order is preserved -- it is the row order of the table the CLI prints.
    """
    if "timezones" not in raw:
        return dict(DEFAULT_TIMEZONES)

    table = raw["timezones"]
    if not isinstance(table, dict):
        _bail("[bold]timezones[/] must be a table of shorthand = \"Area/City\"")
    for shorthand, full in table.items():
        if not isinstance(full, str):
            _bail(f"[bold]timezones.{shorthand}[/] must be a string, got {type(full).__name__}")
        _check_timezone(full, f"timezones.{shorthand}")
    return dict(table)


def _as_increment(raw: dict) -> timedelta:
    value = raw.get("increment_seconds", DEFAULT_INCREMENT_SECONDS)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _bail("[bold]increment_seconds[/] must be a number")
    if value <= 0:
        _bail("[bold]increment_seconds[/] must be greater than 0")
    return timedelta(seconds=value)


@lru_cache(maxsize=1)
def get_config() -> Config:
    path = config_path()
    raw: dict = {}

    if path.is_file():
        try:
            raw = tomllib.loads(path.read_text())
        except tomllib.TOMLDecodeError as e:
            _bail(f"{path} is not valid TOML -- {e}")
        except OSError as e:
            _bail(f"cannot read {path} -- {e}")

    if unknown := sorted(set(raw) - _KNOWN_KEYS):
        _bail(f"unknown key(s) in {path}: {', '.join(unknown)}")

    default_timezone = _check_timezone(
        _as_str(raw, "default_timezone", DEFAULT_TIMEZONE), "default_timezone"
    )
    # An explicit default_timezone with no highlight means highlight it: the
    # emphasised row is "where I am", which is what default_timezone says.
    highlight = _check_timezone(_as_str(raw, "highlight", default_timezone), "highlight")

    return Config(
        default_timezone=default_timezone,
        highlight=highlight,
        increment=_as_increment(raw),
        timezones=_as_timezones(raw),
    )
