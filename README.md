# NTU Academic Calendar → YAML

Parses NTU academic-calendar PDFs into clean, machine-readable YAML: every
semester's dated weeks (labeled teaching / recess / exam), public holidays,
and key events.

## Why

The official calendar PDF is a visual document — great for humans, awkward
for programs. This repo turns it into structured data so anything can
consume it (bots, scripts, dashboards).

## Usage

```sh
# requires poppler-utils (for pdftotext)
python3 parse_calendar.py <input.pdf> <output.yaml>
```

Example:

```sh
python3 parse_calendar.py \
  resource/ntu-academic-calendar-ay2026-27-*.pdf \
  output/ay2026-27.yaml
```

## Output

```yaml
academic_year: 2026-27
semester_1:
  weeks:
    - week: 8
      type: recess
      start: 2026-09-28
      end: 2026-10-04
    - week: 14
      type: exam
      start: 2026-11-09
      end: 2026-11-15
  key_events:
    - Orientation Activities 20 Jul - 6 Aug 2026
    - UG Qualifying English Test 31 Jul 2026
semester_2:
  public_holidays:
    - Chinese New Year 6 - 7 Feb 2027
    - Hari Raya Puasa 10 Mar 2027
special_term:
  note: "..."
```

## How it works

1. **`lib/text.py`** — extracts layout-preserved text via `pdftotext`.
2. **`lib/semester.py`** — splits the page into SEMESTER 1 / SEMESTER 2 /
   SPECIAL TERM blocks and classifies each line.
3. **`lib/events.py`** — pulls dated items (holidays, key events) out of the
   right-aligned event lists, handling single dates and date ranges.
4. **`lib/semester_weeks.py`** — builds the dated week ladder.

### Week types

The PDF marks teaching / recess / exam weeks with cell colors, but the text
legend is not row-aligned with the grid, so it cannot be trusted. Instead we
use NTU's fixed semester structure:

```
weeks 1-7    teaching
week 8       recess
weeks 9-13   teaching
weeks 14-15  exam
```

The semester start date (S1 = the Monday after orientation ends; S2 = the
first Monday of January) anchors the ladder. If NTU ever changes this
pattern, edit `WEEK_TYPE` in `lib/semester_weeks.py`.

## Layout

```
parse_calendar.py      # CLI entry point
lib/
  text.py              # PDF → text, year detection
  semester.py          # semester block splitting
  events.py            # holiday / key-event extraction
  semester_weeks.py    # dated week ladder
resource/              # source PDFs (one per academic year)
output/                # generated YAMLs
```

## Development

```sh
# regenerate all YAMLs
for pdf in resource/*.pdf; do
  out="output/$(basename "$pdf" | grep -oE 'ay[0-9]{4}-[0-9]{2}').yaml"
  python3 parse_calendar.py "$pdf" "$out"
done

# sanity check: YAML must parse
python3 -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('output/*.yaml')]"
```
