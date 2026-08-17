import re
import sys
from datetime import date, datetime, time, timedelta, timezone
from time import sleep
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytz
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.text import Text

from timepal.config import get_config

console = Console()


def _get_shorthand_timezone(tz: str) -> str | None:
    for shorthand, full in get_config().timezones.items():
        if tz.lower() == shorthand.lower():
            return full
    return None


# A relative shift in the time slot: `+2`, `-3`. Whole hours only, so it can
# never be confused with the UTC offsets below, which may carry minutes.
_RELATIVE = re.compile(r"^([+-])(\d{1,2})$")

# A UTC offset in the timezone slot: `+2`, `-3`, `UTC+2`, `utc-5:30`, `GMT+1`.
# The `UTC` prefix is what makes an offset unambiguous in the *first* slot,
# where a bare `+2` is read as a relative shift instead.
_UTC_OFFSET = re.compile(r"^(?:UTC|GMT)?([+-])(\d{1,2})(?::?([0-5][0-9]))?$", re.IGNORECASE)
_UTC_PREFIXED = re.compile(r"^(?:UTC|GMT)", re.IGNORECASE)


def parse_relative_hours(raw: str | time) -> int | None:
    """Hours to shift from now, for a `+2` / `-3` in the time slot."""
    if isinstance(raw, time):
        return None
    if not (match := _RELATIVE.match(raw.strip())):
        return None
    sign, hours = match.groups()
    return -int(hours) if sign == "-" else int(hours)


def looks_like_timezone(raw: str | time) -> bool:
    """Is this first-slot argument really a timezone, not a time?

    `t UTC+2` and `t NY` mean "now, over there". A bare `t +2` does not --
    that is a relative shift, so an offset only counts here when spelled
    with its UTC/GMT prefix.
    """
    if isinstance(raw, time):
        return False
    raw = raw.strip()
    if _UTC_PREFIXED.match(raw):
        return True
    return "/" in raw or _get_shorthand_timezone(raw) is not None


def resolve_timezone(timezone_str: str):
    """A shorthand, a UTC offset, or a full zone name -> a tzinfo."""
    if short_timezone := _get_shorthand_timezone(timezone_str):
        timezone_str = short_timezone
    elif match := _UTC_OFFSET.match(timezone_str.strip()):
        sign, hours, minutes = match.groups()
        offset = timedelta(hours=int(hours), minutes=int(minutes or 0))
        if sign == "-":
            offset = -offset
        if abs(offset) > timedelta(hours=14):
            console.print("Timezone offset must be between [bold red]-14[/] and [bold red]+14[/]")
            sys.exit(1)
        # A true fixed offset: `+2` means UTC+2. Deliberately not Etc/GMT+2,
        # which is UTC-2 under the POSIX sign convention.
        return timezone(offset)

    try:
        return ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, ValueError):
        console.print(f"Timezone [bold red]{timezone_str}[/] not found")
        sys.exit(1)


def now_shifted(hours: int, timezone_str: str) -> datetime:
    """The instant `hours` from now, expressed in the given zone."""
    return datetime.now(tz=resolve_timezone(timezone_str)) + timedelta(hours=hours)


def convert_to_aware_datetime(
    time_raw: str | time, date_raw: str | date, timezone_str: str
) -> datetime:
    tzinfo = resolve_timezone(timezone_str)

    if not isinstance(time_raw, time):
        as_given = time_raw.strip()
        normalised = as_given.replace(".", ":")
        if ":" not in normalised:
            normalised += ":00"
        if len(normalised) < 5:
            normalised = "0" + normalised
        try:
            time_raw = time.fromisoformat(normalised)
        except ValueError:
            console.print(f"Cannot read [bold red]{as_given}[/] as a time")
            sys.exit(1)

    if not isinstance(date_raw, date):
        try:
            date_raw = date.fromisoformat(date_raw)
        except ValueError:
            console.print(f"Cannot read [bold red]{date_raw}[/] as a date (want YYYY-MM-DD)")
            sys.exit(1)

    return datetime.combine(date_raw, time_raw).replace(tzinfo=tzinfo)


def _frame(dt: datetime, input_date: date) -> Group:
    """One rendered snapshot of the clock."""
    config = get_config()

    input_info = [
        ("Date", input_date.isoformat()),
        ("Time", dt.strftime("%H:%M:%S")),
        ("Timezone", str(dt.tzinfo)),
    ]
    heading = [
        Text.from_markup(f"{label}: [bold yellow]{value}[/]") for label, value in input_info
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Timezone")
    table.add_column("Local Time", style="yellow")

    for name, tz in config.timezones.items():
        date_indicator = ""
        current_indicator = ""
        local_dt = dt.astimezone(ZoneInfo(tz))
        date_diff = (local_dt.date() - input_date).days
        if date_diff != 0:
            date_indicator = f"{date_diff:+d}"
        row_style = "bold green" if tz == config.highlight else ""
        if date_indicator:
            date_indicator = f" [bold cyan]{date_indicator}[/]"
        if tz == str(dt.tzinfo):
            current_indicator = " 👈"
        table.add_row(
            f"{name}{current_indicator}",
            f"{local_dt.strftime('%H:%M')}{date_indicator}",
            style=row_style,
        )

    return Group(Text(""), *heading, Text(""), table)


def display_datetime(dt: datetime, continuous: bool) -> None:
    console = Console()
    input_date = dt.date()

    if not continuous:
        console.print(_frame(dt, input_date))
        return

    increment = get_config().increment

    # Live overwrites the previous frame in place. Clearing the screen and
    # reprinting -- what this used to do -- leaves the terminal blank for the
    # gap between the two, which is the flicker.
    with Live(
        _frame(dt, input_date),
        console=console,
        auto_refresh=False,
        transient=False,
    ) as live:
        while True:
            sleep(increment.total_seconds())
            dt += increment
            live.update(_frame(dt, input_date), refresh=True)


def display_timezones(q: str | None = None) -> None:
    all_timezones = pytz.all_timezones
    timezone_entries = []

    for tz in sorted(all_timezones):
        if q and q.lower() not in tz.lower():
            continue
        timezone = pytz.timezone(tz)
        now = datetime.now(timezone)
        offset = now.strftime("%z")
        formatted_offset = f"UTC{offset[:3]}:{offset[3:]}"
        entry = f"[yellow]{tz}[/] [green]{formatted_offset}[/]"
        timezone_entries.append(entry)

    console = Console()

    # Organize the entries into columns and display them
    columns = Columns(timezone_entries, expand=True)
    console.print(columns)


def goodbye():
    console = Console()
    console.print("\nGoodbye :wave:", style="bold cyan")
