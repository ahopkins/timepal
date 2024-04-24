import argparse
from datetime import datetime, timezone
from sys import argv
from zoneinfo import ZoneInfo

from timepal.util import (convert_to_aware_datetime, display_datetime,
                          display_timezones, goodbye)

DEFAULT_TIMEZONE = "Asia/Jerusalem"


def main():
    now_utc = datetime.now(tz=timezone.utc)
    now_local = now_utc.astimezone(ZoneInfo(DEFAULT_TIMEZONE))
    parser = argparse.ArgumentParser(description="Process time and timezone.")
    parser.add_argument(
        "time", nargs="?", default=now_local.time(), help="The time input (required)"
    )
    parser.add_argument(
        "timezone", nargs="?", default=DEFAULT_TIMEZONE, help="Timezone (optional)"
    )
    parser.add_argument(
        "--date",
        default=now_local.date(),
        help="Date in YYYY-MM-DD format (optional, defaults to today)",
    )
    parser.add_argument(
        "--list",
        nargs="?",
        const=True,
        default=False,
        help="List all available timezones and exit",
    )

    args = parser.parse_args()

    if args.list:
        q = args.list if isinstance(args.list, str) else None
        display_timezones(q)
        return

    aware_datetime = convert_to_aware_datetime(args.time, args.date, args.timezone)
    continuous = len(argv) == 1
    try:
        display_datetime(aware_datetime, continuous)
    except KeyboardInterrupt:
        goodbye()
