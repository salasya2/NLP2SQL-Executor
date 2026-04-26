"""
fill_csv_descriptions.py

Reads index.json and fills the 'value_description' column in every
database_description CSV with the richer descriptions stored in the index.
Matching is done by stripping whitespace from the original_column_name in the
CSV and looking it up in the index's sample_values dict for the corresponding
table (file-name without extension).
"""

import json
import csv
import io
import os
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent   # project root
INDEX_FILE = BASE_DIR / "index" / "index.json"
DATA_DIR   = BASE_DIR / "data"

# ── load index ───────────────────────────────────────────────────────────────
with open(INDEX_FILE, encoding="utf-8") as f:
    index: dict = json.load(f)

# Build a flat lookup:  table_name → {column_name → value_description}
descriptions: dict[str, dict[str, str]] = {}
for table_name, table_data in index.items():
    col_desc: dict[str, str] = {}
    sample_values = table_data.get("sample_values", {})
    for col_name, col_info in sample_values.items():
        vd = col_info.get("value_description", "")
        if vd:
            col_desc[col_name.strip()] = vd
    descriptions[table_name.strip().lower()] = col_desc

# ── iterate over all database_description CSVs ───────────────────────────────
csv_files_found  = 0
cells_updated    = 0

for db_dir in DATA_DIR.iterdir():
    if not db_dir.is_dir():
        continue
    desc_dir = db_dir / "database_description"
    if not desc_dir.exists():
        continue

    for csv_path in desc_dir.glob("*.csv"):
        table_name_key = csv_path.stem.strip().lower()
        col_map = descriptions.get(table_name_key, {})

        # Read the whole file as text so we can preserve the exact line endings
        raw = csv_path.read_bytes().decode("utf-8-sig")  # handles BOM if any

        reader = csv.DictReader(io.StringIO(raw))
        if reader.fieldnames is None:
            print(f"  [SKIP] {csv_path} – no header row found")
            continue

        # Make sure value_description column exists
        fieldnames = list(reader.fieldnames)
        if "value_description" not in fieldnames:
            print(f"  [SKIP] {csv_path} – no 'value_description' column")
            continue

        rows = list(reader)
        updated_count = 0

        for row in rows:
            orig_col = (row.get("original_column_name") or "").strip()
            if not orig_col:
                continue  # blank original name, skip

            new_vd = col_map.get(orig_col, "")
            if not new_vd:
                continue  # no description in index for this column

            existing = (row.get("value_description") or "").strip()
            if existing != new_vd.strip():
                row["value_description"] = new_vd
                updated_count += 1

        # Write back
        out = io.StringIO()
        writer = csv.DictWriter(
            out,
            fieldnames=fieldnames,
            lineterminator="\r\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)

        csv_path.write_bytes(out.getvalue().encode("utf-8"))

        csv_files_found += 1
        cells_updated   += updated_count
        status = f"{updated_count} cell(s) updated" if updated_count else "no changes needed"
        print(f"  [{db_dir.name}] {csv_path.name}: {status}")

print(f"\nDone. {csv_files_found} CSV file(s) processed, {cells_updated} value_description cell(s) filled.")
