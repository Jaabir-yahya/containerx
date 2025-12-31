import json
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List


def flatten_json(obj: Any, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten a nested JSON-like object.

    - Nested dict keys become dot-separated (e.g. country.name).
    - Lists are stored as JSON strings to keep the table rectangular.
    """
    items: Dict[str, Any] = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten_json(v, new_key, sep=sep))
            elif isinstance(v, list):
                # Keep lists as JSON strings so they remain readable in the table
                try:
                    items[new_key] = json.dumps(v, ensure_ascii=False)
                except TypeError:
                    # Fallback if something inside isn't serializable
                    items[new_key] = str(v)
            else:
                items[new_key] = v
    else:
        # Root is not a dict (unexpected for this file, but keep it robust)
        items[parent_key or "value"] = obj

    return items


def json_to_csv(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array of merchants.")

    flattened_rows: List[Dict[str, Any]] = []
    all_keys: set[str] = set()

    for obj in data:
        if not isinstance(obj, dict):
            # Skip non-object entries just in case
            continue
        flat = flatten_json(obj)
        flattened_rows.append(flat)
        all_keys.update(flat.keys())

    fieldnames = sorted(all_keys)

    with output_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in flattened_rows:
            writer.writerow(row)


def main(argv: List[str]) -> None:
    if len(argv) < 3:
        print(
            "Usage: python merchants_to_csv.py <input_json_path> <output_csv_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = Path(argv[1]).expanduser().resolve()
    output_path = Path(argv[2]).expanduser().resolve()

    if not input_path.exists():
        print(f"Input file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading JSON from: {input_path}")
    print("Converting to flattened CSV (this may take a little while)...")
    json_to_csv(input_path, output_path)
    print(f"CSV written to: {output_path}")


if __name__ == "__main__":
    main(sys.argv)




