import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

if not HUNTER_API_KEY:
    st.warning("⚠️ La clé API Hunter.io est manquante. Vérifiez votre fichier .env.")

@st.cache_data(show_spinner=False)
def get_domain(company_name):
    try:
        if not HUNTER_API_KEY:
            return None

        url = f"https://api.hunter.io/v2/domain-search?company={company_name}&api_key={HUNTER_API_KEY}"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("data", {}).get("domain")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            st.error("🚦 Hunter.io rate limit reached (429 Too Many Requests). Please wait a few minutes and try again.")
            return 'RATE_ERROR'
        else:
            st.error(f"❌ Hunter.io — erreur domaine pour {company_name}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Hunter.io — erreur domaine pour {company_name}: {e}")
        return None

@st.cache_data(show_spinner=False)
def get_contacts(domain, roles=None):
    try:
        if not HUNTER_API_KEY:
            return []

        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        emails = res.json().get("data", {}).get("emails", [])

        filtered = []
        for e in emails:
            role_text = (e.get("position") or "").lower()
            if not roles or any(keyword in role_text for keyword in roles):
                filtered.append({
                    "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                    "position": e.get("position"),
                    "email": e.get("value"),
                    "linkedin": e.get("linkedin")
                })

        if not filtered:
            st.info(f"ℹ️ Aucun contact trouvé pour {domain} avec les rôles : {roles}")

        return filtered
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            st.error("🚦 Hunter.io rate limit reached (429 Too Many Requests). Please wait a few minutes and try again.")
        else:
            st.error(f"❌ Hunter.io — erreur contacts pour {domain}: {e}")
        return []