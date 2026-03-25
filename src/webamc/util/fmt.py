#!/usr/bin/env python3

from datetime import date, datetime
from babel import dates

from webamc import config


def fmt_date(d: date) -> str:
    date_format = config.CONFIG["date_format"]
    date_locale = config.CONFIG["date_locale"]
    if date_format is None:
        return dates.format_date(d, locale=date_locale)
    return dates.format_date(d, format=date_format, locale=date_locale)


def fmt_datetime(d: datetime) -> str:
    datetime_format = config.CONFIG["datetime_format"]
    date_locale = config.CONFIG["date_locale"]
    if datetime_format is None:
        return dates.format_datetime(d, locale=date_locale)
    return dates.format_datetime(d, format=datetime_format, locale=date_locale)


def fmt_title(s: str) -> str:
    if s == "":
        return s
    return s[0].upper() + s[1:]


def fmt_name(fst_name: str, name: str) -> str:
    return fst_name.title() + " " + name.upper()


def fmt_file_size(size: int) -> str:
    num = size
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if num < 1000:
            if unit == "":
                return str(num)
            return f"{num:3.1f} {unit}"
        num = int(num / 1000)
    return str(size)
