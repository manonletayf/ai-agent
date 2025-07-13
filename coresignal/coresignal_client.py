# core/coresignal_client.py

import requests
import os

BASE_URL = "https://api.coresignal.com/cdapi/v2/company_base/search/filter"

def search_companies(filters: dict) -> list[dict]:
    """
    Envoie dynamiquement les filtres fournis à l'API Coresignal et retourne les résultats.
    """

    headers = {
        "accept": "application/json",
        "apikey": os.getenv("CORESIGNAL_API_KEY"),
        "Content-Type": "application/json"
    }

    payload = {}
    # Mapping des clés en payload respectant les noms API
    mapping = {
        "size": "size",
        "industry": "industry",
        "country": "country",
        "location": "location",
        "employees_count_gte": "employees_count_gte",        
        "last updated gte": "last updated gte"
    }

    for key, field in mapping.items():
        if key in filters and filters[key]:
            payload[field] = filters[key]


    response = requests.post(BASE_URL, headers=headers, json=payload)

    print("🔎 Response status:", response.status_code)
    if response.status_code != 200:
        raise Exception(f"Coresignal API error {response.status_code}: {response.text}")
    
    data = response.json()
    print("📦 Search results:", data)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "results" in data:
        return data["results"]
    else:
        raise ValueError("Unexpected API response format")
