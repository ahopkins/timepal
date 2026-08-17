# timepal

A timezone table for the people you work with. Give it a time and it shows you
that instant everywhere at once.

```
$ t 14:30 NY        # 2:30pm New York, in every configured zone
$ t 8 LA            # bare hours work too
$ t +2              # two hours from now
$ t -3              # three hours ago
$ t 12:00 UTC+2     # noon at UTC+2; offsets may carry minutes (UTC-5:30)
$ t +2 +2           # two hours from now, read as UTC+2
$ t UTC+2           # now, over at UTC+2
$ t --date 2026-09-01 09:00 UTC
$ t                 # no arguments: a live clock, ticking. ctrl-c to leave
$ t --list jerus    # search the full tz database
```

Installs two identical commands, `timepal` and `t`.

## Arguments

The first is **when**, the second is **where that when is**:

| Position | Accepts | Meaning |
| --- | --- | --- |
| 1 | `14:30`, `8`, `9.15` | a wall-clock time |
| 1 | `+2`, `-3` | a relative shift, in whole hours, from right now |
| 2 | `NY`, `LA` | a shorthand from your config |
| 2 | `+2`, `UTC+2`, `UTC-5:30` | a fixed UTC offset |
| 2 | `Africa/Johannesburg` | any zone name from the tz database |

`+N` therefore means two different things, but never in the same slot: a shift
in position 1, an offset in position 2. Where a lone argument would be
ambiguous, `t +2` is read as the shift — spell the zone `t UTC+2` to get the
offset instead.

An offset in position 2 means what it says: `+2` is UTC+2, agreeing with any
real UTC+2 zone. (It is *not* mapped to `Etc/GMT+2`, which is UTC−2 under the
POSIX sign convention.)

Relative shifts are anchored on the instant rather than on a wall clock, so
`t +2 LA` and `t +2 NY` name the same moment and differ only in which row is
marked 👈. `--date` cannot be combined with a shift.

## Configuration

Optional. Read from `$XDG_CONFIG_HOME/timepal.toml`, or `~/.config/timepal.toml`
when `XDG_CONFIG_HOME` is unset; `TIMEPAL_CONFIG` overrides both. Every key has
a built-in default, so the file may be partial or absent entirely.

```toml
# Assumed timezone when no positional timezone is given, and the zone the
# clock reads "now" in.
default_timezone = "Asia/Jerusalem"

# Row drawn in bold green -- "where I am". Defaults to default_timezone.
highlight = "Asia/Jerusalem"

# Tick length of the continuous clock.
increment_seconds = 1

# The table to print, in this order. Keys are the shorthand accepted as the
# positional timezone argument, matched case-insensitively.
[timezones]
LA = "America/Los_Angeles"
NY = "America/New_York"
UTC = "UTC"
Israel = "Asia/Jerusalem"
```

Supplying `[timezones]` **replaces** the built-in list rather than adding to it,
so the printed table is exactly what the file says. Zone names are validated at
startup — a typo names the offending key and exits rather than surfacing as a
traceback mid-render.

## Install

```
uv tool install --editable .
```
