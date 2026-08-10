"""Semester-block structure of the calendar: split the text into SEMESTER 1 /
SEMESTER 2 / SPECIAL TERM sections and classify each line within a block."""

import re

from text import clean
from events import extract_event, has_date

SECTION_HDR = re.compile(r"(SEMESTER \d|SPECIAL TERM)")
WEEKDAY_HDR_ONLY = re.compile(r"^\s*[SMTWF](?:\s+[SMTWF])+")


def split_semester_blocks(lines: list[str]):
    """[(label, start_row, end_row)] for SEMESTER 1 / 2 / SPECIAL TERM."""
    markers = []
    for i, ln in enumerate(lines):
        m = SECTION_HDR.search(ln)
        if m:
            markers.append((i, m.group(1).strip()))
    blocks = []
    for idx, (row, label) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        blocks.append((label, row, end))
    return blocks


def parse_semester(lines: list[str], start: int, end: int) -> dict:
    """Extract week rows, public holidays, and key events from one block."""
    weeks: list[str] = []
    holidays: list[str] = []
    events: list[str] = []

    in_holidays = False
    in_events = False

    for i in range(start, end):
        ln = lines[i]
        if "SINGAPORE PUBLIC HOLIDAYS" in ln:
            in_holidays = True
            in_events = False
            continue
        if "UNIVERSITY KEY EVENTS" in ln or "UNIVERSITY KEY EVENT" in ln:
            in_events = True
            in_holidays = False
            continue

        stripped = ln.strip()
        if not stripped:
            continue

        nums = re.findall(r"\b\d{1,2}\b", ln)

        if in_holidays:
            if has_date(ln):
                ev = extract_event(ln)
                if ev:
                    holidays.append(ev)
            continue

        if in_events:
            if has_date(ln):
                ev = extract_event(ln)
                if ev:
                    events.append(ev)
            continue

        # Outside lists: a line with >=6 numbers is a week (date-grid) row,
        # unless it is a bare weekday header.
        if len(nums) >= 6 and not WEEKDAY_HDR_ONLY.match(ln):
            weeks.append(clean(ln))

    return {"weeks": weeks, "holidays": holidays, "events": events}
