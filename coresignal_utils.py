import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
CORESIGNAL_API_KEY = os.getenv("CORESIGNAL_API_KEY")

if not CORESIGNAL_API_KEY:
    st.warning("⚠️ La clé API Coresignal est manquante. Vérifiez votre fichier .env.")

@st.cache_data(show_spinner=False)
def estimate_local_employees(company_name, location):
    url = "https://api.coresignal.com/v1/employee/search"
    headers = {
        "Authorization": f"Bearer {CORESIGNAL_API_KEY}",
        "Content-Type": "application/json"
    }

    query = {
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"experience.company.name": company_name}},
                    {"match_phrase": {"location.name": location}},
                    {"term": {"experience.current": True}}
                ]
            }
        },
        "size": 0,
        "track_total_hits": True
    }

    try:
        response = requests.post(url, json=query, headers=headers, timeout=10)
        response.raise_for_status()
        total_hits = response.json().get("hits", {}).get("total", {}).get("value", 0)
        return total_hits
    except Exception as e:
        st.error(f"❌ Coresignal — erreur estimation effectifs pour {company_name} à {location} : {e}")
        return None

@st.cache_data(show_spinner=False)
def has_relevant_profile_in_location(company_name, location, roles=None):
    url = "https://api.coresignal.com/v1/employee/search"
    headers = {
        "Authorization": f"Bearer {CORESIGNAL_API_KEY}",
        "Content-Type": "application/json"
    }

    must_filters = [
        {"match_phrase": {"experience.company.name": company_name}},
        {"match_phrase": {"location.name": location}},
        {"term": {"experience.current": True}}
    ]

    if roles:
        role_filters = [{"match": {"experience.title": role}} for role in roles]
        must_filters.append({"bool": {"should": role_filters}})

    query = {
        "query": {
            "bool": {
                "must": must_filters
            }
        },
        "size": 1
    }

    try:
        response = requests.post(url, json=query, headers=headers, timeout=10)
        response.raise_for_status()
        total = response.json().get("hits", {}).get("total", {}).get("value", 0)
        if total == 0:
            st.info(f"ℹ️ Aucun profil pertinent trouvé pour {company_name} à {location} avec les rôles {roles}.")
        return total > 0
    except Exception as e:
        st.error(f"❌ Coresignal — erreur filtrage pour {company_name} : {e}")
        return False