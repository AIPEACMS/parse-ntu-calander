"""CLI: parse an NTU academic-calendar PDF into a faithful YAML file.

Usage:
    python3 parse_calendar.py <input.pdf> <output.yaml>
"""

import sys
from pathlib import Path

import yaml

from text import pdf_to_text, detect_year
from semester import split_semester_blocks, parse_semester


def extract_calendar(pdf_path: Path) -> dict:
    text = pdf_to_text(pdf_path)
    lines = text.split("\n")
    year = detect_year(text)

    semesters = []
    for label, srow, erow in split_semester_blocks(lines):
        entry: dict = {"section": label}
        if label == "SPECIAL TERM":
            entry["note"] = _clean_note(lines[srow + 1:erow])
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


def _clean_note(lines: list[str]) -> str:
    import re
    from text import clean
    return clean(" ".join(
        l for l in lines
        if l.strip() and "MINDEF" not in l and "Year of Study" not in l
    ))


def to_yaml(cal: dict) -> str:
    """Serialize as valid YAML with a flat, readable shape."""
    lines = [f"academic_year: {cal['academic_year']}"]
    for sem in cal["semesters"]:
        key = ("semester_" + sem["section"].split()[-1].lower()
               if sem["section"] != "SPECIAL TERM" else "special_term")
        lines.append(f"{key}:")
        if "note" in sem:
            quoted = yaml.safe_dump(sem["note"]).strip()
            lines.append(f"  note: {quoted}")
        if sem.get("weeks"):
            lines.append("  weeks:")
            for w in sem["weeks"]:
                lines.append(f"    - {w}")
        for field in ("public_holidays", "key_events"):
            if sem.get(field):
                lines.append(f"  {field}:")
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
