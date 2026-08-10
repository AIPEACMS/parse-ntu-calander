"""Extraction of dated items (public holidays, key events) from a calendar
line. The NTU semester calendar prints events to the right of the month grid;
each line carries a name followed by a date or date range."""

import re

MONTH_WORDS = (
    "JANUARY FEBRUARY MARCH APRIL MAY JUNE JULY "
    "AUGUST SEPTEMBER OCTOBER NOVEMBER DECEMBER"
).split()

# A full date, three shapes:
#   "9 Aug 2026"                    (single day)
#   "6 - 7 Feb 2027"                (same-month range)
#   "20 Jul - 6 Aug 2026"           (cross-month range)
DATE = (
    r"\d{1,2} [A-Z][a-z]{2} \d{4}"
    r"|"
    r"\d{1,2} - \d{1,2} [A-Z][a-z]{2} \d{4}"
    r"|"
    r"\d{1,2} [A-Z][a-z]{2} - \d{1,2} [A-Z][a-z]{2} \d{4}"
)

WEEKDAY_HDR = r"^[SMTWF](?:\s+[SMTWF]){5,6}\s+"


def strip_grid_prefix(line: str) -> str:
    """Cut away the date grid (digits, month headers, weekday headers) that
    precedes the right-aligned event text."""
    s = re.sub(r"^[\d\s]+\s*", "", line.strip())
    for w in MONTH_WORDS:
        s = re.sub(r"^" + w + r"\s+", "", s)
    # Weekday headers may repeat once per month block.
    while True:
        new = re.sub(WEEKDAY_HDR, "", s)
        if new == s:
            break
        s = new
    return s


def extract_event(line: str) -> str | None:
    """Extract 'Name date' from a right-aligned event/holiday line, or None.

    The name is capital-letter words (may contain lowercase 'of', 'the', ...),
    followed by a date in one of the three supported shapes.
    """
    s = strip_grid_prefix(line)
    m = re.search(
        r"([A-Z][A-Za-z'’\-]*(?:\s+[A-Za-z'’\-]+)*)\s+(" + DATE + r")",
        s,
    )
    if not m:
        return None
    name = re.sub(r"\s+", " ", m.group(1).strip())
    date = re.sub(r"\s+", " ", m.group(2).strip())
    return f"{name} {date}"


def has_date(line: str) -> bool:
    return bool(re.search(r"\d{1,2} [A-Z][a-z]{2} \d{4}", line))
