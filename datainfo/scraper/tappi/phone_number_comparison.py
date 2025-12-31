#!/usr/bin/env python3
"""
Phone Number Comparison Script
Compares phone numbers from three CSV files and outputs detailed matches.
"""

import csv
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def normalize_phone(phone: str) -> str:
    """Normalize phone number by removing spaces, dashes, parentheses, and leading +"""
    if not phone or not isinstance(phone, str):
        return ""
    # Remove all non-digit characters except leading +
    phone = phone.strip()
    # Remove + sign if present at the start
    phone = phone.lstrip('+')
    # Remove all non-digit characters
    phone = re.sub(r'[^\d]', '', phone)
    return phone

def read_phone_numbers_from_csv(filepath: str, column_index: int, skip_header: bool = True) -> Dict[str, List[Tuple[int, str]]]:
    """
    Read phone numbers from a CSV file.
    Returns a dict mapping normalized phone -> list of (row_number, original_phone)
    """
    phone_dict = defaultdict(list)
    row_num = 1 if skip_header else 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            if skip_header:
                next(reader, None)  # Skip header
            
            for row in reader:
                if len(row) > column_index:
                    original_phone = row[column_index].strip()
                    if original_phone:  # Only process non-empty phones
                        normalized = normalize_phone(original_phone)
                        if normalized:  # Only add if normalization produced a valid number
                            phone_dict[normalized].append((row_num, original_phone))
                row_num += 1
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return phone_dict

def main():
    # File paths and column indices
    file1_path = "jay/merchants-0-to-12024.csv"
    file1_col = 53  # Column BB (0-indexed: BB = 53)
    file1_name = "Jay Merchants"
    
    file2_path = "fufu/all_merchants_20251219_143335.csv"
    file2_col = 3   # Column D (0-indexed: D = 3)
    file2_name = "Fufu All Merchants"
    
    file3_path = "fufu/all_contacts_20251219_143335.csv"
    file3_col = 0   # Column A (0-indexed: A = 0)
    file3_name = "Fufu All Contacts"
    
    print("=" * 80)
    print("PHONE NUMBER COMPARISON ANALYSIS")
    print("=" * 80)
    print()
    
    # Read phone numbers from each file
    print("Reading phone numbers from files...")
    phones1 = read_phone_numbers_from_csv(file1_path, file1_col)
    phones2 = read_phone_numbers_from_csv(file2_path, file2_col)
    phones3 = read_phone_numbers_from_csv(file3_path, file3_col)
    
    print(f"  {file1_name}: {len(phones1)} unique phone numbers")
    print(f"  {file2_name}: {len(phones2)} unique phone numbers")
    print(f"  {file3_name}: {len(phones3)} unique phone numbers")
    print()
    
    # Find matches between all three files
    all_phones = set(phones1.keys()) | set(phones2.keys()) | set(phones3.keys())
    
    # Categorize matches
    matches_all_three = []
    matches_1_and_2 = []
    matches_1_and_3 = []
    matches_2_and_3 = []
    only_in_1 = []
    only_in_2 = []
    only_in_3 = []
    
    for phone in all_phones:
        in_1 = phone in phones1
        in_2 = phone in phones2
        in_3 = phone in phones3
        
        if in_1 and in_2 and in_3:
            matches_all_three.append(phone)
        elif in_1 and in_2:
            matches_1_and_2.append(phone)
        elif in_1 and in_3:
            matches_1_and_3.append(phone)
        elif in_2 and in_3:
            matches_2_and_3.append(phone)
        elif in_1:
            only_in_1.append(phone)
        elif in_2:
            only_in_2.append(phone)
        elif in_3:
            only_in_3.append(phone)
    
    # Print detailed results
    print("=" * 80)
    print("MATCH SUMMARY")
    print("=" * 80)
    print(f"Phone numbers in ALL THREE files: {len(matches_all_three)}")
    print(f"Phone numbers in {file1_name} AND {file2_name}: {len(matches_1_and_2)}")
    print(f"Phone numbers in {file1_name} AND {file3_name}: {len(matches_1_and_3)}")
    print(f"Phone numbers in {file2_name} AND {file3_name}: {len(matches_2_and_3)}")
    print(f"Phone numbers ONLY in {file1_name}: {len(only_in_1)}")
    print(f"Phone numbers ONLY in {file2_name}: {len(only_in_2)}")
    print(f"Phone numbers ONLY in {file3_name}: {len(only_in_3)}")
    print()
    
    # Detailed match report
    print("=" * 80)
    print("DETAILED MATCH REPORT")
    print("=" * 80)
    print()
    
    # Matches in all three files
    if matches_all_three:
        print(f"\n📞 PHONE NUMBERS FOUND IN ALL THREE FILES ({len(matches_all_three)}):")
        print("-" * 80)
        for i, phone in enumerate(sorted(matches_all_three)[:50], 1):  # Show first 50
            entries1 = phones1[phone]
            entries2 = phones2[phone]
            entries3 = phones3[phone]
            print(f"\n  Match #{i}: {phone}")
            print(f"    {file1_name}: {len(entries1)} occurrence(s)")
            for row, orig in entries1[:3]:  # Show first 3 occurrences
                print(f"      - Row {row}: {orig}")
            if len(entries1) > 3:
                print(f"      ... and {len(entries1) - 3} more")
            print(f"    {file2_name}: {len(entries2)} occurrence(s)")
            for row, orig in entries2[:3]:
                print(f"      - Row {row}: {orig}")
            if len(entries2) > 3:
                print(f"      ... and {len(entries2) - 3} more")
            print(f"    {file3_name}: {len(entries3)} occurrence(s)")
            for row, orig in entries3[:3]:
                print(f"      - Row {row}: {orig}")
            if len(entries3) > 3:
                print(f"      ... and {len(entries3) - 3} more")
        if len(matches_all_three) > 50:
            print(f"\n  ... and {len(matches_all_three) - 50} more matches")
    
    # Matches between file 1 and 2
    if matches_1_and_2:
        print(f"\n📞 PHONE NUMBERS IN {file1_name} AND {file2_name} ({len(matches_1_and_2)}):")
        print("-" * 80)
        for i, phone in enumerate(sorted(matches_1_and_2)[:30], 1):  # Show first 30
            entries1 = phones1[phone]
            entries2 = phones2[phone]
            print(f"\n  Match #{i}: {phone}")
            print(f"    {file1_name}: {len(entries1)} occurrence(s) - Rows: {[r for r, _ in entries1[:5]]}")
            print(f"    {file2_name}: {len(entries2)} occurrence(s) - Rows: {[r for r, _ in entries2[:5]]}")
        if len(matches_1_and_2) > 30:
            print(f"\n  ... and {len(matches_1_and_2) - 30} more matches")
    
    # Matches between file 1 and 3
    if matches_1_and_3:
        print(f"\n📞 PHONE NUMBERS IN {file1_name} AND {file3_name} ({len(matches_1_and_3)}):")
        print("-" * 80)
        for i, phone in enumerate(sorted(matches_1_and_3)[:30], 1):  # Show first 30
            entries1 = phones1[phone]
            entries3 = phones3[phone]
            print(f"\n  Match #{i}: {phone}")
            print(f"    {file1_name}: {len(entries1)} occurrence(s) - Rows: {[r for r, _ in entries1[:5]]}")
            print(f"    {file3_name}: {len(entries3)} occurrence(s) - Rows: {[r for r, _ in entries3[:5]]}")
        if len(matches_1_and_3) > 30:
            print(f"\n  ... and {len(matches_1_and_3) - 30} more matches")
    
    # Matches between file 2 and 3
    if matches_2_and_3:
        print(f"\n📞 PHONE NUMBERS IN {file2_name} AND {file3_name} ({len(matches_2_and_3)}):")
        print("-" * 80)
        for i, phone in enumerate(sorted(matches_2_and_3)[:30], 1):  # Show first 30
            entries2 = phones2[phone]
            entries3 = phones3[phone]
            print(f"\n  Match #{i}: {phone}")
            print(f"    {file2_name}: {len(entries2)} occurrence(s) - Rows: {[r for r, _ in entries2[:5]]}")
            print(f"    {file3_name}: {len(entries3)} occurrence(s) - Rows: {[r for r, _ in entries3[:5]]}")
        if len(matches_2_and_3) > 30:
            print(f"\n  ... and {len(matches_2_and_3) - 30} more matches")
    
    # Export detailed matches to CSV
    print("\n" + "=" * 80)
    print("EXPORTING DETAILED RESULTS TO CSV")
    print("=" * 80)
    
    output_file = "phone_number_matches.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Normalized_Phone',
            'In_File1_Jay_Merchants',
            'In_File2_Fufu_Merchants',
            'In_File3_Fufu_Contacts',
            'Match_Type',
            'File1_Rows',
            'File2_Rows',
            'File3_Rows'
        ])
        
        all_matches = sorted(set(matches_all_three + matches_1_and_2 + matches_1_and_3 + matches_2_and_3))
        
        for phone in all_matches:
            in_1 = phone in phones1
            in_2 = phone in phones2
            in_3 = phone in phones3
            
            if in_1 and in_2 and in_3:
                match_type = "All_Three"
            elif in_1 and in_2:
                match_type = "File1_File2"
            elif in_1 and in_3:
                match_type = "File1_File3"
            elif in_2 and in_3:
                match_type = "File2_File3"
            else:
                match_type = "Unknown"
            
            rows1 = ','.join(str(r) for r, _ in phones1.get(phone, []))
            rows2 = ','.join(str(r) for r, _ in phones2.get(phone, []))
            rows3 = ','.join(str(r) for r, _ in phones3.get(phone, []))
            
            writer.writerow([
                phone,
                'Yes' if in_1 else 'No',
                'Yes' if in_2 else 'No',
                'Yes' if in_3 else 'No',
                match_type,
                rows1 or '',
                rows2 or '',
                rows3 or ''
            ])
    
    print(f"  Detailed results exported to: {output_file}")
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()


