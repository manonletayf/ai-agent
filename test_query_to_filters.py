
from core.filters import parse_user_query_to_filters
from utils.env_loader import load_environment

def test_query_to_filters():
    load_environment()  # Assure que les variables d'env sont chargées

    user_query = "Find 50 tech companies in London with more than 1000 employees"

    filters = parse_user_query_to_filters(user_query)

    print("🧪 Parsed Filters:\n")
    for key, value in filters.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_query_to_filters()