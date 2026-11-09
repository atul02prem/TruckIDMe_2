"""The official definition of every CAN signal, read from the dataset's dictionary.

`DriverIDSQLiteCSVDataDictionary.pdf` ships with the ORNL dataset and defines each
SPN: what it measures, its units, and its enumerations and null sentinels. It is the
authoritative source for this dataset -- more so than the J1939-71 standard, because
it describes the columns as exported rather than the bus as specified.

Two uses:

1. **Corroborating the signal taxonomy.** The dictionary's own structure encodes the
   distinction `classify_signals.py` measures: a parameter that reports a physical
   quantity carries a `Units:` field, and a parameter that reports a *state* does not.
   Of the 13 signals with no `Units:` field, 11 are classified step. That is an
   independent check on the taxonomy from a direction no statistic touches.

2. **Catching decode faults.** Comparing observed values against the published range
   is what moved SPN 4154 from kept to excluded: its dictionary range is 0-0.875%,
   and 9.31% of its samples exceed that by 15-158x.

Extraction needs `pdftotext` (poppler-utils), so the parsed result is written to a
JSON beside this module and committed. Nothing in the pipeline depends on the PDF or
on poppler at run time; `load()` reads the JSON. Re-run this module if the PDF
changes.

Run from the repo root in the `truckidme` env:
    python -m src.qc.signal_dictionary
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DICTIONARY_PDF = PROJECT_ROOT / "DriverIDSQLiteCSVDataDictionary.pdf"
DICTIONARY_JSON = Path(__file__).with_suffix(".json")

SUMMARY_CHARS = 180

# A bullet introducing a signal entry: '● 3031 Aftertreatment 1 ... - Temperature of'
# The zero-width space is present in the PDF's text layer.
_ENTRY = re.compile(r"^\s*●\s*​?\s*(\d+)\s+(.*)")
_ANY_BULLET = re.compile(r"^\s*●")
_UNITS = re.compile(r"Units:\s*([^○·]+?)(?:\s*$|\s*[○·])")


def pdf_text() -> str:
    """Extract the dictionary PDF's text layer.

    Returns:
        The whole document as text, layout preserved.

    Raises:
        FileNotFoundError: if the dictionary PDF is not in the repository.
        RuntimeError: if `pdftotext` is unavailable.
    """
    if not DICTIONARY_PDF.exists():
        raise FileNotFoundError(f"dictionary PDF not found: {DICTIONARY_PDF}")
    try:
        done = subprocess.run(
            ["pdftotext", "-layout", str(DICTIONARY_PDF), "-"],
            capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pdftotext not found; install poppler-utils to re-extract. "
            f"The committed {DICTIONARY_JSON.name} is used at run time.") from exc
    return done.stdout


def parse_entries(text: str) -> dict[int, dict[str, str | None]]:
    """Parse one entry per SPN from the dictionary text.

    A `TimeNNNN` bullet is skipped because its name begins with a letter, so only
    the signal entries match, and each entry's body runs to the next bullet.

    Args:
        text: the dictionary's text layer.

    Returns:
        SPN to {'description', 'units'}; units is None where the entry has no
        `Units:` field, which is itself meaningful -- see the module docstring.
    """
    bodies: dict[int, list[str]] = {}
    current: int | None = None
    for line in text.splitlines():
        entry = _ENTRY.match(line)
        if entry:
            current = int(entry.group(1))
            bodies[current] = [entry.group(2)]
        elif _ANY_BULLET.match(line):
            current = None
        elif current is not None:
            bodies[current].append(line.strip())

    parsed: dict[int, dict[str, str | None]] = {}
    for spn, body in bodies.items():
        blob = re.sub(r"\s+", " ", " ".join(body)).replace("​", "").strip()
        units = _UNITS.search(blob)
        parsed[spn] = {
            "description": summarise(blob),
            "units": units.group(1).strip() if units else None,
        }
    return parsed


def summarise(blob: str) -> str:
    """Shorten one entry to its defining sentence.

    Args:
        blob: the entry's full text.

    Returns:
        The text after the name's ' - ' separator, truncated at a sentence end.
    """
    body = blob.split(" - ", 1)[1] if " - " in blob else blob
    body = re.split(r"[○·]\s*Units:", body)[0].strip()
    if len(body) <= SUMMARY_CHARS:
        return body
    cut = body[:SUMMARY_CHARS]
    stop = cut.rfind(". ")
    return (cut[:stop + 1] if stop > 60 else cut.rstrip() + "…").strip()


def extract() -> dict[int, dict[str, str | None]]:
    """Re-extract the dictionary from the PDF and write the committed JSON.

    Returns:
        SPN to {'description', 'units'}.
    """
    parsed = parse_entries(pdf_text())
    DICTIONARY_JSON.write_text(
        json.dumps({str(k): v for k, v in sorted(parsed.items())}, indent=1,
                   ensure_ascii=False) + "\n")
    return parsed


def load() -> dict[int, dict[str, str | None]]:
    """Read the committed dictionary extract.

    Returns:
        SPN to {'description', 'units'}, or an empty dict if the JSON is absent
        so that a caller can degrade rather than fail.
    """
    if not DICTIONARY_JSON.exists():
        return {}
    raw = json.loads(DICTIONARY_JSON.read_text())
    return {int(k): v for k, v in raw.items()}


def main() -> None:
    """Re-extract the dictionary and report what was found."""
    parsed = extract()
    with_units = sum(1 for v in parsed.values() if v["units"])
    print(f"entries parsed:     {len(parsed)}")
    print(f"with a Units field: {with_units}")
    print(f"without:            {len(parsed) - with_units} "
          f"-> {sorted(s for s, v in parsed.items() if not v['units'])}")
    print(f"written -> {DICTIONARY_JSON}")


if __name__ == "__main__":
    main()
