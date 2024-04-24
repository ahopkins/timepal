import sys
from datetime import date, datetime, time, timedelta
from time import sleep
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytz
from rich.columns import Columns
from rich.console import Console
from rich.table import Table

console = Console()

SHORTHAND_TIMEZONES = {
    "LA": "America/Los_Angeles",
    "NY": "America/New_York",
    "Brazil": "America/Sao_Paulo",
    "UTC": "UTC",
    "Israel": "Asia/Jerusalem",
    "Brisbane": "Australia/Brisbane",
    "Byron": "Australia/Sydney",
}
HIGHLIGHT = "Asia/Jerusalem"
INCREMENT = timedelta(seconds=1)


def _get_shorthand_timezone(tz: str) -> str | None:
    for shorthand, full in SHORTHAND_TIMEZONES.items():
        if tz.lower() == shorthand.lower():
            return full
    return None


def convert_to_aware_datetime(
    time_raw: str | time, date_raw: str | date, timezone_str: str
) -> datetime:
    if short_timezone := _get_shorthand_timezone(timezone_str):
        timezone_str = short_timezone
    elif (offset_str := timezone_str.strip("+-")).isnumeric():
        as_int = int("-" + offset_str if timezone_str.startswith("-") else offset_str)
        if as_int < -12 or as_int > 12:
            raise ValueError("Timezone must be between -12 and 12")
        timezone_str = f"Etc/GMT{as_int:+d}"

    if not isinstance(time_raw, time):
        time_raw = time_raw.strip().replace(".", ":")
        if ":" not in time_raw:
            time_raw += ":00"
        if len(time_raw) < 5:
            time_raw = "0" + time_raw
        time_raw = time.fromisoformat(time_raw)

    if not isinstance(date_raw, date):
        date_raw = date.fromisoformat(date_raw)

    naive_datetime = datetime.combine(date_raw, time_raw)
    try:
        timezone = ZoneInfo(timezone_str)
    except ZoneInfoNotFoundError:
        console.print(f"Timezone [bold red]{timezone_str}[/] not found")
        sys.exit(1)
    aware_datetime = naive_datetime.replace(tzinfo=timezone)

    return aware_datetime


def display_datetime(dt: datetime, continuous: bool) -> None:
    console = Console()
    input_date = dt.date()

    while True:
        if continuous:
            console.clear()
        output = ["\n"]

        input_info = [
            ("Date", input_date.isoformat()),
            ("Time", dt.strftime("%H:%M:%S")),
            ("Timezone", str(dt.tzinfo)),
        ]

        for label, value in input_info:
            output.append(f"{label}: [bold yellow]{value}[/]\n")

        output.append("\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Timezone")
        table.add_column("Local Time", style="yellow")

        for name, tz in SHORTHAND_TIMEZONES.items():
            date_indicator = ""
            current_indicator = ""
            local_dt = dt.astimezone(ZoneInfo(tz))
            date_diff = (local_dt.date() - input_date).days
            if date_diff != 0:
                date_indicator = f"{date_diff:+d}"
            row_style = "bold green" if tz == HIGHLIGHT else ""
            if date_indicator:
                date_indicator = f" [bold cyan]{date_indicator}[/]"
            if tz == str(dt.tzinfo):
                current_indicator = " 👈"
            table.add_row(
                f"{name}{current_indicator}",
                f"{local_dt.strftime('%H:%M')}{date_indicator}",
                style=row_style,
            )

        output.append(table)

        console.print(*output, end="\r")
        if continuous:
            dt += INCREMENT
            sleep(1)
        else:
            break


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
