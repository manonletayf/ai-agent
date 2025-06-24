import streamlit as st
from core.coresignal_client import search_companies
from utils.env_loader import load_environment
from datetime import date

load_environment()

st.set_page_config(page_title="Company Search", layout="centered")
st.title("🔎 Advanced Company Filter")

# --- Static filter lists
company_sizes = [
    "2-10 employees",
    "11-50 employees",
    "51-200 employees",
    "201-500 employees",
    "501-1,000 employees",
    "1,001-5,000 employees",
    "5,001-10,000 employees",
    "5001-10,000 employees",
    "10,001+ employees"
]

industries = [
    "Accounting", "Aviation & Aerospace", "Banking", "Biotechnology", "Computer Software",
    "Financial Services", "Hospital & Health Care", "Information Technology & Services",
    "Marketing & Advertising", "Retail"
    # Add full industry list if needed
]

countries = [
    "United Kingdom", "France", "Germany", "United States", "India"
    # Add full country list if needed
]

funding_types = ["Seed", "Series A", "Series B", "Series C", "Series D", "Series E+"]

# --- UI Form
with st.form("filters_form"):
    size = st.multiselect("👥 Company Size", ["None"] + company_sizes)
    employees_count_gte = st.number_input("👷 Precision : Employees count ≥", min_value=0, value=100)
    industry = st.multiselect("🏭 Industry", ["None"] + industries)
    country = st.multiselect("🌍 Country", ["None"] + countries)
    location_input = st.text_input("📍 Location : City or Region , comma-separated", "")
    location = [loc.strip() for loc in location_input.split(",") if loc.strip()]
    funding_type = st.multiselect("🏷️ Last funding round type", ["None"] + funding_types)

    funding_rounds_gte = st.number_input("💰 Total funding rounds ≥", min_value=0, value=1)
    funding_date = st.date_input("📅 Last funding round date ≥", value=None)
    last_updated = st.date_input("🗓️ Last updated ≥", value=None)
    limit = st.slider("🔢 Number of companies", min_value=1, max_value=100, value=20)

    submit = st.form_submit_button("🔍 Search")

# --- Handle submission
if submit:
    filters = {}
    if size and "None" not in size:
        filters["size"] = size
    if industry and "None" not in industry:
        filters["industry"] = industry
    if country and "None" not in country:
        filters["country"] = country
    if location:
        filters["location"] = location
    if employees_count_gte > 0:
        filters["employees_count_gte"] = employees_count_gte
    if funding_rounds_gte > 0:
        filters["funding_total_rounds_count_gte"] = funding_rounds_gte
    if funding_date:
        filters["funding_last_round_date_gte"] = str(funding_date)
    if funding_type and "None" not in funding_type:
        filters["funding_last_round_type"] = funding_type
    if last_updated:
        filters["last_updated_gte"] = str(last_updated)

    filters["limit"] = limit

    st.write("🧾 Applied Filters", filters)

    # --- Optional debug: see actual payload before API call
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
    payload = {}
    for key, field in mapping.items():
        if key in filters and filters[key]:
            payload[field] = filters[key]
    payload["limit"] = filters.get("limit", 20)

    st.write("📦 Payload sent to Coresignal API:", payload)

    # --- Run API call
    with st.spinner("Querying Coresignal..."):
        try:
            companies = search_companies(filters)
            if companies:
                st.success(f"✅ Found {len(companies)} companies:")
                for company in companies[:20]:
                    st.write(f"- **{company.get('name', 'Unnamed')}** — {company.get('location', 'N/A')}")
            else:
                st.warning("No companies matched the selected filters.")
        except Exception as e:
            st.error(f"❌ Coresignal API error: {e}")