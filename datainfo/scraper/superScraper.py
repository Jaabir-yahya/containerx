#!/usr/bin/env python3
"""
Python version of superScraper.js
Fetches enterprise data from Kilimax API
"""

import json
import os
import requests
from pathlib import Path

BEARER_TOKEN = "eyJhbGciOiJIUzM4NCJ9.eyJzdWIiOiIxMDAzOTIzIiwiaWF0IjoxNzY2NjA5MDQzLCJleHAiOjE3NjcyMTM4NDN9.AfPhcSgqqE0YeV3CBhQCZwh4x9mqcrxWZdcKuQ6hQlc_j6M8jLkuTFCXtvlPJUQ4"
OUTPUT_FILE = "enterpriseData.json"

ENTERPRISE_IDS = list(range(3220, 3230))  # First 10: 3220-3229
URLS = [
    "https://account.kilimax.com/api/user/company/getAllCompanyPage",
    "https://account.kilimax.com/api/user/user/userPage"
]

def main():
    # Load existing data if it exists
    data = {}
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    for enterprise_id in ENTERPRISE_IDS:
        enterprise_id_str = str(enterprise_id)
        if enterprise_id_str not in data:
            data[enterprise_id_str] = {}
        
        for url in URLS:
            if url in data[enterprise_id_str]:
                print(f"Already fetched {enterprise_id} - {url}")
                continue
            
            payload = {
                "current": 1,
                "size": 10,
                "enterpriseId": enterprise_id_str
            }
            
            # Add extra fields for userPage endpoint
            if url.endswith("/userPage"):
                payload["data"] = []
                payload["roleIds"] = []
            
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {BEARER_TOKEN}",
                    "Accept": "application/json"
                }
                
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                json_data = response.json()
                
                data[enterprise_id_str][url] = json_data
                
                # Save after each fetch
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Saved enterprise {enterprise_id}, {url}")
                
                # Display first 10 results for company data
                if "getAllCompanyPage" in url:
                    info = json_data.get("data", {}).get("info", {})
                    records = info.get("records", [])
                    if records:
                        records_to_show = records[:10]
                        print(f"\n📊 First {len(records_to_show)} companies for enterprise {enterprise_id}:")
                        for idx, record in enumerate(records_to_show, 1):
                            company_name = record.get("companyName", "N/A")
                            company_id = record.get("id", "N/A")
                            country = record.get("countryName", "N/A")
                            print(f"  {idx}. {company_name} (ID: {company_id}) - {country}")
                        print()
                        
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching {enterprise_id} - {url}: {e}")
            except Exception as e:
                print(f"❌ Unexpected error for {enterprise_id} - {url}: {e}")
    
    print("\n" + "="*80)
    print("✅ All done!")
    print("="*80)

if __name__ == "__main__":
    main()
