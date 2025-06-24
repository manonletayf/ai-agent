from core.filters import parse_user_query_to_filters
from core.coresignal_client import search_companies
from utils.env_loader import load_environment

def test_search():
    load_environment()

    user_query = "Find 20 software companies in London with more than 200 employees"    filters = parse_user_query_to_filters(user_query)
    print("🔍 Using filters:", filters)

    companies = search_companies(filters)
    print(f"\n✅ Found {len(companies)} companies:\n")
    for c in companies[:10]:
        print(f"- {c.get('name')} ({c.get('location') or c.get('headquarters new address')})")

if __name__ == "__main__":
    test_search()