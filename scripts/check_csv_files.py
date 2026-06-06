from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER_DIR = ROOT / "registers"


def main() -> None:
    paths = sorted(REGISTER_DIR.glob("*.csv"))
    if not paths:
        raise SystemExit("csv check: no register CSV files found")

    errors: list[str] = []
    for path in paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        if not rows:
            errors.append(f"{path.relative_to(ROOT)} is empty")
            continue
        header = rows[0]
        if not header or any(not column.strip() for column in header):
            errors.append(f"{path.relative_to(ROOT)} has an empty header column")
            continue
        expected = len(header)
        for line_number, row in enumerate(rows[1:], start=2):
            if not any(cell.strip() for cell in row):
                continue
            if len(row) != expected:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number} has {len(row)} "
                    f"columns; expected {expected}"
                )

    if errors:
        raise SystemExit("csv check failed:\n" + "\n".join(errors))
    print(f"csv check: ok ({len(paths)} files)")


if __name__ == "__main__":
    main()
