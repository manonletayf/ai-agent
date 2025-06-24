# core/coresignal_client.py

import requests
from config import CORESIGNAL_API_KEY

BASE_URL = "https://api.coresignal.com/api/v2/company/base/search/filter"

def search_companies(filters: dict) -> list[dict]:
    """
    Envoie dynamiquement les filtres fournis à l’API Coresignal et retourne les résultats.
    """

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apikey": CORESIGNAL_API_KEY
    }

    payload = {}
    # Mapping des clés en payload respectant les noms API
    mapping = {
        "size": "size",
        "industry": "industry",
        "country": "country",
        "location": "location",
        "employees_count_gte": "employees count gte",
        "funding_total_rounds_count_gte": "funding total rounds count gte",
        "funding_last_round_date_gte": "funding last round date gte",
        "funding_last_round_type": "funding last round type",
        "last_updated_gte": "last updated gte"
    }

    for key, field in mapping.items():
        if key in filters and filters[key]:
            payload[field] = filters[key]

    # Ajout de la limite
    payload["limit"] = filters.get("limit", 20)

    response = requests.post(BASE_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Coresignal API error {response.status_code}: {response.text}")

    return response.json().get("results", [])