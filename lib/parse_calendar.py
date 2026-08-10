#!/usr/bin/env python3
"""Parse NTU academic-calendar PDFs into a faithful YAML representation.

Usage:
    python3 lib/parse_calendar.py <input.pdf> <output.yaml>

The YAML is a text-only, faithful copy of the calendar's data: the academic
year, each semester's week grid as printed, all public holidays, and all key
events / test dates. The visual calendar (recess/exam shading, colors) is
best read from the PDF itself — this captures the *data*.

Requires `pdftotext` (poppler-utils) on PATH.
"""

import re
import subprocess
import sys
from pathlib import Path

# A holiday or key-event line carries a real date like "9 Aug 2026".
DATE_PAT = re.compile(r"(\d{1,2}) ([A-Z][a-z]{2}) (\d{4})")


def pdf_to_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def detect_year(text: str) -> str:
    m = re.search(r"AY\s*(\d{4})-(\d{2})", text)
    if not m:
        raise ValueError("could not detect academic year (expected 'AY2026-27')")
    return f"{m.group(1)}-{m.group(2)}"


def split_semester_blocks(lines: list[str]):
    """[(label, start_row, end_row)] for SEMESTER 1 / 2 / SPECIAL TERM."""
    markers = []
    for i, ln in enumerate(lines):
        m = re.search(r"(SEMESTER \d|SPECIAL TERM)", ln)
        if m:
            markers.append((i, m.group(1).strip()))
    blocks = []
    for idx, (row, label) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else len(lines)
        blocks.append((label, row, end))
    return blocks


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


MONTH_WORDS = (
    "JANUARY FEBRUARY MARCH APRIL MAY JUNE JULY "
    "AUGUST SEPTEMBER OCTOBER NOVEMBER DECEMBER"
).split()


def extract_event(ln: str) -> str | None:
    """Extract 'Name date' from a right-aligned event/holiday line.

    The event text sits right of the date grid. We take everything from the
    first alphabetic run after the grid, then normalize. Handles both single
    dates ('9 Aug 2026') and ranges ('6 - 7 Feb 2027') plus trailing
    annotations ('(Sat - Sun)*^').
    """
    # Cut the line at the event column: everything before the event text is
    # the date grid (numbers + weekday headers). The event starts at the
    # first capital-letter word that is not a stray month header.
    stripped = ln.strip()
    # Drop a leading run of grid digits (the month grids).
    stripped = re.sub(r"^[\d\s]+\s*", "", stripped)
    # Drop leading month headers that belong to the grid legend (APRIL MAY ...).
    for w in MONTH_WORDS:
        stripped = re.sub(r"^" + w + r"\s+", "", stripped)
    # Drop leading weekday headers (S M T W T F S) — may repeat per month block.
    while True:
        new = re.sub(r"^[SMTWF](?:\s+[SMTWF]){5,6}\s+", "", stripped)
        if new == stripped:
            break
        stripped = new

    # Name ... date — supports three shapes:
    #   "9 Aug 2026"                    (single day)
    #   "6 - 7 Feb 2027"                (same-month range)
    #   "20 Jul - 6 Aug 2026"           (cross-month range)
    date = (
        r"\d{1,2} [A-Z][a-z]{2} \d{4}"
        r"|"
        r"\d{1,2} - \d{1,2} [A-Z][a-z]{2} \d{4}"
        r"|"
        r"\d{1,2} [A-Z][a-z]{2} - \d{1,2} [A-Z][a-z]{2} \d{4}"
    )
    m = re.search(
        r"([A-Z][A-Za-z'’\-]*(?:\s+[A-Za-z'’\-]+)*)\s+(" + date + r")",
        stripped,
    )
    if not m:
        return None
    name = m.group(1).strip()
    date_part = re.sub(r"\s+", " ", m.group(2).strip())
    ev = f"{name} {date_part}".strip()
    return ev or None


def parse_semester(lines: list[str], start: int, end: int) -> dict:
    """Extract week rows, public holidays, and key events from one block."""
    weeks: list[str] = []
    holidays: list[str] = []
    events: list[str] = []

    in_holidays = False
    in_events = False

    for i in range(start, end):
        ln = lines[i]
        # Section headers (to the right of the grid).
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
        has_date = DATE_PAT.search(ln)

        if in_holidays:
            if has_date:
                ev = extract_event(ln)
                if ev:
                    holidays.append(ev)
            continue

        if in_events:
            if has_date:
                ev = extract_event(ln)
                if ev:
                    events.append(ev)
            continue

        # Outside lists: a line with >=6 numbers is a week (date-grid) row,
        # unless it is a bare weekday header.
        if len(nums) >= 6 and not re.match(r"^\s*[SMTWF](?:\s+[SMTWF])+", ln):
            weeks.append(clean(ln))

    return {"weeks": weeks, "holidays": holidays, "events": events}


def extract_calendar(pdf_path: Path) -> dict:
    text = pdf_to_text(pdf_path)
    lines = text.split("\n")
    year = detect_year(text)

    semesters = []
    for label, srow, erow in split_semester_blocks(lines):
        entry: dict = {"section": label}
        if label == "SPECIAL TERM":
            entry["note"] = clean(" ".join(
                l for l in lines[srow + 1:erow]
                if l.strip() and "MINDEF" not in l and "Year of Study" not in l
            ))
            semesters.append(entry)
            continue

        parsed = parse_semester(lines, srow, erow)
        entry["weeks"] = parsed["weeks"]
        if parsed["holidays"]:
            entry["public_holidays"] = parsed["holidays"]
        if parsed["events"]:
            entry["key_events"] = parsed["events"]
        semesters.append(entry)

    return {"academic_year": year, "semesters": semesters}


def to_yaml(cal: dict) -> str:
    """Serialize as valid YAML with a flat, readable shape."""
    import yaml

    lines = [f"academic_year: {cal['academic_year']}"]
    for sem in cal["semesters"]:
        key = ("semester_" + sem["section"].split()[-1].lower()
               if sem["section"] != "SPECIAL TERM" else "special_term")
        lines.append(f"{key}:")
        if "note" in sem:
            # Quote the note so special characters never break YAML.
            quoted = yaml.safe_dump(sem["note"]).strip()
            lines.append(f"  note: {quoted}")
        if sem.get("weeks"):
            lines.append("  weeks:")
            for w in sem["weeks"]:
                lines.append(f"    - {w}")
        for field, label in (("public_holidays", "public_holidays"),
                             ("key_events", "key_events")):
            if sem.get(field):
                lines.append(f"  {label}:")
                for item in sem[field]:
                    lines.append(f"    - {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    pdf, yaml_out = (Path(a) for a in sys.argv[1:])
    cal = extract_calendar(pdf)
    yaml_out.write_text(to_yaml(cal))
    print(f"parsed {pdf.name}: AY {cal['academic_year']} -> {yaml_out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
