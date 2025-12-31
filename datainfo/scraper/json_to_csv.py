import json
import csv
from pathlib import Path


def json_to_csv(
    json_path: str,
    csv_path: str,
) -> None:
    """
    Convert a JSON array of objects to CSV.

    - Top-level keys become CSV columns.
    - Nested dicts/lists are JSON-encoded as strings in the CSV.
    """
    json_file = Path(json_path)
    csv_file = Path(csv_path)

    with json_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array of objects")

    # Collect all top-level keys across all objects
    fieldnames = sorted({key for item in data if isinstance(item, dict) for key in item.keys()})

    with csv_file.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for item in data:
            if not isinstance(item, dict):
                continue

            row = {}
            for key in fieldnames:
                value = item.get(key, "")
                # For nested structures, store as JSON string
                if isinstance(value, (dict, list)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            writer.writerow(row)


if __name__ == "__main__":
    base_dir = Path("/Users/jaabirahmed/Documents/projects/containerx")
    src = base_dir / "tappi" / "merchants-0-to-12024.json"
    dest = base_dir / "tappi" / "merchants-0-to-12024.csv"

    json_to_csv(str(src), str(dest))
    print(f"CSV written to: {dest}")


