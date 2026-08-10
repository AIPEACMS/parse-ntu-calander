"""Decode the 3-month calendar grid rows into dated weeks.

The NTU semester calendar shows three months side by side. Each grid row is
one week (Mon-Sun) and carries, left to right, that week's dates in month A,
month B, month C. This module reads the date numbers at their column offsets
and reconstructs real start/end dates per month column.

Column offsets are derived from the 'S M T W T F S' weekday headers that
repeat once per month block.
"""

import re
from datetime import date

MONTHS = {
    "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11,
    "DECEMBER": 12, "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
    "MAY": 5, "JUNE": 6,
}

WEEK_LABELS = [
    ("Teaching Week", "teaching"),
    ("Recess Week", "recess"),
    ("Revision and Examination Week", "exam"),
    ("University Orientation Week", "orientation"),
]


def month_columns(header_line: str) -> list[tuple[str, int]]:
    """Map each month in a 'S M T W T F S ... S M T W T F S' header to the
    column offset of its first weekday column (Sat). Returns
    [(month_name, sat_col)]."""
    cols = []
    for m in re.finditer(r"S\s+M\s+T\s+W\s+T\s+F\s+S", header_line):
        cols.append(m.start())
    return cols


def week_label(line: str) -> str | None:
    for label, kind in WEEK_LABELS:
        if label in line:
            return kind
    return None


def split_week_dates(line: str, month_cols: list[int],
                     month_names: list[str], year: int) -> list[dict]:
    """Read the date numbers under each month column of a grid row.

    Returns [{month, start_day, end_day}] — one entry per month column that
    has dates on this row. `year` is the calendar year for those months.
    """
    out = []
    for col, name in zip(month_cols, month_names):
        # Slice the line at this column, take the first 7 day numbers.
        segment = line[col:col + 30]
        nums = re.findall(r"\b(\d{1,2})\b", segment)
        if not nums:
            continue
        days = [int(n) for n in nums[:7]]
        mon = MONTHS[name]
        # Days may wrap a month boundary (e.g. 28,29,30,31,1,2,3); handle by
        # assuming ascending and capping at the month's day count.
        start = days[0]
        end = days[-1]
        if end < start:
            # Month wrap: the week spans into the next month.
            out.append({"month": name, "start_day": start,
                        "end_day": None, "year": year})
        else:
            out.append({"month": name, "start_day": start, "end_day": end,
                        "year": year})
    return out
