#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 18 15:28:58 2025

@author: manonletayf
"""

# List of company domains to search (you can also load from CSV or GPT output)
'''
Paster below the Python list that GPT gave you 
'''
company_domains = [
    {"Company": "Allica Bank", "Domain": "allica.bank"},
    {"Company": "OakNorth Bank", "Domain": "oaknorth.co.uk"},
    {"Company": "WorldFirst", "Domain": "worldfirst.com"},
    {"Company": "Zopa", "Domain": "zopa.com"},
    {"Company": "Teya", "Domain": "teya.com"}
]


import requests
import pandas as pd
import time

# Your Hunter.io API key here
HUNTER_API_KEY = "07781ecb9fe8f50a49019fd63a3861841add4cec"



# Define role keywords to filter for decision-makers
target_keywords = ["CEO", "Chief", "Head", "People", "HR", "Talent", "Director"]

results = []

def search_domain(domain, company_name):
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Failed for {domain}: {response.status_code}")
        
        try:
           error_detail = response.json().get("errors", response.text)
           print(f"📄 Error details: {error_detail}")
        except Exception as e:
           print(f"⚠️ Could not parse error message: {e}")
    
        if response.status_code == 401:
           print("🔐 Check your API key — it may be missing or invalid.")
        elif response.status_code == 403:
           print("🚫 You may have hit a rate limit or lack access to this endpoint.")
        elif response.status_code == 429:
           print("⏳ Too many requests — you're being rate limited. Try again later.")
        elif response.status_code == 404:
           print("❓ Domain not found or no emails returned.")
        else:
           print("💥 Unknown error occurred.")

        
        return []

    data = response.json().get("data", {})
    emails = data.get("emails", [])
    filtered = []

    for person in emails:
        position = person.get("position", "")
        if any(keyword.lower() in (position or "").lower() for keyword in target_keywords):
            full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
            email = person.get("value")
            linkedin = person.get("linkedin", "")
            filtered.append({
                "Company": company_name,
                "Person": full_name,
                "Job": position or "N/A",
                "Email": email,
                "LinkedIn": linkedin or "N/A"
            })

    return filtered

# Main loop
for entry in company_domains:
    company = entry["Company"]
    domain = entry["Domain"]
    print(f"🔍 Searching {company} ({domain})...")
    people = search_domain(domain, company)
    results.extend(people)
    time.sleep(1)  # Respect rate limits

# Export to Excel
df = pd.DataFrame(results)
df.to_excel("hunter_stakeholders.xlsx", index=False, engine="openpyxl")
print(f"✅ Exported {len(results)} contacts to hunter_stakeholders.xlsx")