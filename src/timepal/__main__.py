import argparse
from datetime import datetime, timezone
from sys import argv
from zoneinfo import ZoneInfo

from timepal.config import get_config
from timepal.util import (convert_to_aware_datetime, display_datetime,
                          display_timezones, goodbye, looks_like_timezone,
                          now_shifted, parse_relative_hours)


def main():
    config = get_config()
    now_utc = datetime.now(tz=timezone.utc)
    now_local = now_utc.astimezone(ZoneInfo(config.default_timezone))
    parser = argparse.ArgumentParser(description="Process time and timezone.")
    parser.add_argument(
        "time",
        nargs="?",
        default=now_local.time(),
        help="A time (14:30, 8), a relative shift (+2, -3), or a timezone",
    )
    parser.add_argument(
        "timezone",
        nargs="?",
        default=None,
        help="Timezone the time is in: a shorthand, a UTC offset (+2, UTC-5:30), or a zone name",
    )
    parser.add_argument(
        "--date",
        default=None,
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

    # `t UTC+2` and `t NY` name a zone with no time, meaning "now, over there".
    # A bare `t +2` is a relative shift instead, so it never lands here.
    zone_only = args.timezone is None and looks_like_timezone(args.time)
    if zone_only:
        args.time, args.timezone = None, args.time
    if args.timezone is None:
        args.timezone = config.default_timezone

    relative_hours = None if zone_only else parse_relative_hours(args.time)

    if zone_only or relative_hours is not None:
        if args.date is not None:
            parser.error("--date cannot be combined with a relative shift")
        # Anchored on the instant, not on a wall clock: reinterpreting the
        # local wall clock in another zone would name a different moment.
        aware_datetime = now_shifted(relative_hours or 0, args.timezone)
    else:
        aware_datetime = convert_to_aware_datetime(
            args.time, args.date or now_local.date(), args.timezone
        )

    continuous = len(argv) == 1
    try:
        display_datetime(aware_datetime, continuous)
    except KeyboardInterrupt:
        goodbye()
