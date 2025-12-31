#!/usr/bin/env python3
"""
Convert Kilimax Results.json to CSV format
Extracts all company records from the nested JSON structure
"""

import json
import csv
from pathlib import Path

def flatten_record(record, enterprise_id):
    """Flatten a record and add enterpriseId"""
    flat = {'enterpriseId': enterprise_id}
    for key, value in record.items():
        # Convert None to empty string for CSV compatibility
        if value is None:
            flat[key] = ''
        elif isinstance(value, (dict, list)):
            # Convert nested structures to JSON strings
            flat[key] = json.dumps(value) if value else ''
        else:
            flat[key] = value
    return flat

def convert_json_to_csv(json_file_path, csv_file_path):
    """Convert JSON file to CSV"""
    print(f"Reading JSON file: {json_file_path}")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} enterprise entries")
    
    # Extract all records
    all_records = []
    fieldnames_set = set()
    
    for entry in data:
        enterprise_id = entry.get('enterpriseId', '')
        data_obj = entry.get('data', {})
        info = data_obj.get('info', {})
        records = info.get('records', [])
        
        for record in records:
            flat_record = flatten_record(record, enterprise_id)
            all_records.append(flat_record)
            fieldnames_set.update(flat_record.keys())
    
    print(f"Extracted {len(all_records)} company records")
    
    # Determine column order: enterpriseId first, then others alphabetically
    fieldnames = ['enterpriseId'] + sorted([f for f in fieldnames_set if f != 'enterpriseId'])
    
    # Write to CSV
    print(f"Writing CSV file: {csv_file_path}")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        if all_records:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_records)
        else:
            # Write header even if no records
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    
    print(f"Successfully created CSV with {len(all_records)} rows and {len(fieldnames)} columns")
    print(f"Columns: {', '.join(fieldnames[:10])}..." if len(fieldnames) > 10 else f"Columns: {', '.join(fieldnames)}")

if __name__ == "__main__":
    json_file = Path(__file__).parent / "Kilimax Results.json"
    csv_file = Path(__file__).parent / "Kilimax Results.csv"
    
    convert_json_to_csv(json_file, csv_file)
    print(f"\n✅ Conversion complete!")
    print(f"📄 Output file: {csv_file}")
