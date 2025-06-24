# core/filters.py

def build_filters(location: str, industry: str, min_employees: int, limit: int) -> dict:
    """
    Build a filters dictionary to pass to Coresignal API from structured user input.
    """
    return {
        "location": location,
        "industry": industry,
        "min_employees": min_employees,
        "limit": limit
    }