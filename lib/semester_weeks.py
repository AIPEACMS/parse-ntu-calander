"""NTU semester week ladder: given a semester start date, produce the dated
weeks with their type.

NTU standard semester structure (both S1 and S2):
    weeks 1-7      teaching
    week 8         recess
    weeks 9-13     teaching
    weeks 14-15    exam

The calendar PDF's own legend labels are not row-aligned, so the week type
comes from this fixed pattern rather than the (unreliable) text labels.
"""

import re
from datetime import date, timedelta

WEEK_TYPE = {i: "teaching" for i in range(1, 16)}
WEEK_TYPE[8] = "recess"
WEEK_TYPE[14] = "exam"
WEEK_TYPE[15] = "exam"

NUM_WEEKS = 15


def semester_start(semester: int, text: str, year_start: int) -> date:
    """Find the Monday of teaching week 1 for a semester.

    S1: the Monday after orientation ends (orientation is ~20 Jul - 6/8 Aug).
    S2: the Monday after the winter break / first Monday of January.
    """
    if semester == 1:
        # Orientation end date from the key events (e.g. "20 Jul - 6 Aug 2026").
        m = re.search(r"([A-Z][a-z]{2}) \d{1,2} - \d{1,2} ([A-Z][a-z]{2}) (\d{4})",
                      text)
        if m:
            end_month = _month_num(m.group(2))
            end_day = int(re.search(r"- \d{1,2}", text).group(0)[2:])
            end = date(int(m.group(3)), end_month, end_day)
        else:
            end = date(year_start, 8, 6)
        return _monday_after(end)
    else:
        # S2 starts the first Monday of January of the end year.
        first_jan = date(year_start + 1, 1, 1)
        return _monday_on_or_after(first_jan)


def _monday_after(d: date) -> date:
    return d + timedelta(days=(7 - d.weekday()) % 7)


def _monday_on_or_after(d: date) -> date:
    return d + timedelta(days=(7 - d.weekday()) % 7)


def _month_num(name: str) -> int:
    months = {m: i + 1 for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
         "Oct", "Nov", "Dec"])}
    return months[name]


def week_ladder(start: date) -> list[dict]:
    """Build the dated week ladder starting at [start] (week 1 Monday)."""
    weeks = []
    for i in range(1, NUM_WEEKS + 1):
        monday = start + timedelta(weeks=i - 1)
        sunday = monday + timedelta(days=6)
        weeks.append({
            "week": i,
            "type": WEEK_TYPE[i],
            "start": monday.isoformat(),
            "end": sunday.isoformat(),
        })
    return weeks
