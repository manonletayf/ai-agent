import requests
import os

BASE_URL = "https://api.coresignal.com/cdapi/v2/company/base/collect/"

def collect_company_data(company_id: str) -> dict:
    """
    Retrieves full company data from Coresignal using the collect endpoint.
    """
    url = BASE_URL + company_id
    headers = {
        "accept": "application/json",
        "apikey": os.getenv("CORESIGNAL_API_KEY")
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Coresignal collect error {response.status_code}: {response.text}")

    return response.json()