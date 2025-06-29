import os
import streamlit as st
import requests
from dotenv import load_dotenv
import pandas as pd
import time
from urllib.parse import urlencode

load_dotenv()
if "results" not in st.session_state:
    st.session_state["results"] = []
API_KEY = os.getenv("HUBSPOT_ACCESS_TOKEN")  # jeton OAuth


def search_people(company_name, job_titles, locations, seniorities=None, domains=None, per_page=50, page=1):
    # Build query parameters for Apollo API
    params = []
    for title in job_titles:
        params.append(("person_titles[]", title))
    for loc in locations:
        params.append(("person_locations[]", loc))
    if seniorities:
        for s in seniorities:
            params.append(("person_seniorities[]", s))
    if domains:
        for d in domains:
            params.append(("q_organization_domains_list[]", d))
    params.append(("q_organization_names[]", company_name))
    params.append(("include_similar_titles", "true"))
    params.append(("per_page", str(per_page)))
    params.append(("page", str(page)))
    url = f"https://api.apollo.io/api/v1/mixed_people/search?{urlencode(params)}"
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("APOLLO_API_KEY")
    }
    resp = requests.post(url, headers=headers)
    resp.raise_for_status()
    return resp.json().get("people", [])

# — Interface Streamlit —

st.title("🔍 Recherche de personnes via Apollo pour des entreprises HubSpot")

# Étape 1 – récup la liste des entreprises via un fichier Excel OU saisie manuelle
col1, col2 = st.columns(2)
all_comps = []
with col1:
    uploaded_file = st.file_uploader("Upload Excel file with company names", type=["xlsx", "xls"])
    if uploaded_file:
        df_excel = pd.read_excel(uploaded_file)
        if "Company name" not in df_excel.columns:
            st.error("Excel file must contain a 'Company name' column.")
        else:
            all_comps += [n for n in df_excel["Company name"].dropna().unique()]
with col2:
    manual_companies = st.text_area(
        "Or enter company names manually (one per line)",
        placeholder="Company A\nCompany B\nCompany C"
    )
    if manual_companies:
        all_comps += [n.strip() for n in manual_companies.split("\n") if n.strip()]
# Remove duplicates and empty
all_comps = list({n for n in all_comps if n})
if not all_comps:
    st.warning("Please upload an Excel file or enter company names manually.")
    st.stop()
all_comps = [{"id": i, "Company name": n} for i, n in enumerate(all_comps)]

# Étape 2 – sélection des entreprises & filtres
selected = st.multiselect(
    "Sélectionnez des entreprises",
    options=[c["Company name"] for c in all_comps]
)
if len(selected) > 20:
    st.warning("You have selected more than 20 companies. This may take a while and could hit API rate limits.")

job_titles_input = st.text_input(
    "Job title filters (1 to 5), separated by ; (e.g. HR Director; Recruiter)"
)
locations_input = st.text_input(
    "Location filters (1 to 2), separated by ; (e.g. London ; Paris)",
)
seniorities = st.multiselect(
    "Seniority filters (optional, select up to 2)",
    options=[
        "owner", "founder", "c_suite", "partner", "vp", "head",
        "director", "manager", "senior", "entry", "intern"
    ],
    default=[]
)

if st.button("Search"):
    job_titles = [j.strip() for j in job_titles_input.split(";") if j.strip()]
    locations = [l.strip() for l in locations_input.split(";") if l.strip()]
    if not selected or not job_titles or not locations:
        st.error("Please select at least:\n• 1 company\n• 1 job title\n• 1 location")
    else:
        try:
            st.session_state["results"] = []  # Reset stored results
            seen_emails = set()
            progress = st.progress(0, text="Searching companies...")
            for idx, company in enumerate(selected):
                try:
                    people = search_people(
                        company_name=company,
                        job_titles=job_titles,
                        locations=locations,
                        seniorities=seniorities
                    )
                    for p in people:
                        email = p.get("email") or next((e["email"] for e in p.get("contact_emails", []) if e.get("email_status") == "verified"), None)
                        if email and email in seen_emails:
                            continue
                        if email:
                            seen_emails.add(email)
                        st.session_state["results"].append(p)
                except Exception as e:
                    st.warning(f"Error searching {company}: {e}")
                progress.progress((idx + 1) / len(selected), text=f"Searched {idx + 1}/{len(selected)} companies")
                time.sleep(0.2)  # Small delay to avoid rate limits
            progress.empty()
        except Exception as e:
            st.error(f"Error during search: {e}")

# Pagination for results
def get_page(items, page, page_size):
    start = page * page_size
    end = start + page_size
    return items[start:end]

if st.session_state.get("results"):
    data = st.session_state["results"]
    rows = []
    for p in data:
        email = p.get("email") or (
            next((e["email"] for e in p.get("contact_emails", []) if e.get("email_status") == "verified"), None)
        )
        if email == "email_not_unlocked@domain.com":
            email = "Locked (enrich to see)"
        rows.append({
            "Name": p.get("name"),
            "Title": p.get("title"),
            "Email": email,
            "Company": p.get("organization_name"),
            "Location": p.get("present_raw_address") or f"{p.get('city')}, {p.get('country')}",
            "LinkedIn": p.get("linkedin_url")
        })
    # Pagination controls
    page_size = 10
    total_pages = (len(rows) - 1) // page_size + 1
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1) - 1
    paged_rows = get_page(rows, page, page_size)
    for i, row in enumerate(paged_rows):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{row['Name']}** – {row['Title']}  \n"
                        f"📧 {row['Email']}  \n"
                        f"🏢 {row['Company']}  \n"
                        f"📍 {row['Location']}  \n"
                        f"[LinkedIn]({row['LinkedIn']})" if row['LinkedIn'] else "")
        with col2:
            if st.button("Export to HubSpot", key=f"export_{page}_{i}"):
                try:
                    props = {
                        "email": row["Email"] or "",
                        "firstname": row["Name"].split()[0] if row["Name"] else "",
                        "lastname": " ".join(row["Name"].split()[1:]) if row["Name"] and len(row["Name"].split()) > 1 else "",
                        "jobtitle": row["Title"] or "",
                        "company": row["Company"] or "",
                        "linkedinbio": row["LinkedIn"] or "",
                        "city": row["Location"] or ""
                    }
                    hubspot_client.crm.contacts.basic_api.create(simple_public_object_input={"properties": props})
                    st.success(f"{row['Name']} exported to HubSpot.")
                except Exception as e:
                    st.error(f"Failed to export {row['Name']} to HubSpot: {e}")
            