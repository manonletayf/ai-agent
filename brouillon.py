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


def search_people(company_name, locations, job_titles=None, seniorities=None, domains=None, per_page=50, page=1):
    # Build query parameters for Apollo API
    params = []
    if job_titles:  # Only add job titles if provided
        for title in job_titles:
            params.append(("person_titles[]", title))
        params.append(("include_similar_titles", "true"))
    for loc in locations:
        params.append(("person_locations[]", loc))
    if seniorities:
        for s in seniorities:
            params.append(("person_seniorities[]", s))
    if domains:
        for d in domains:
            params.append(("q_organization_domains_list[]", d))
    if company_name:  # Only add company name if it's not empty
        params.append(("q_organization_names[]", company_name))
    params.append(("contact_email_status[]", "verified"))
    params.append(("per_page", str(per_page)))
    params.append(("page", str(page)))
    search_type = "DOMAIN" if domains else "COMPANY"
    search_value = domains[0] if domains else company_name
    print(f"\n🔍 === SEARCHING FOR {search_type}: {search_value} ===")
    print(f"📍 Job titles: {job_titles if job_titles else 'Any position'}")
    print(f"🌍 Locations: {locations}")
    print(f"👥 Seniorities: {seniorities if seniorities else 'Any level'}")
    if domains:
        print(f"🌐 Domains: {domains}")
    
    # Show the exact parameters being sent
    print(f"📋 URL Parameters:")
    for param_name, param_value in params:
        print(f"   {param_name}: {param_value}")
    
    url = f"https://api.apollo.io/api/v1/mixed_people/search?{urlencode(params)}"
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("APOLLO_API_KEY")
    }
    
    try:
        
        api_key = os.getenv('APOLLO_API_KEY')
        print(f"🔑 API Key present: {'Yes' if api_key else 'No'}")
        print(f"🔑 API Key (first 10 chars): {api_key[:10] + '...' if api_key else 'None'}")
        print(f"🌐 Request URL: {url}")
        
        resp = requests.post(url, headers=headers)
        print(f"📊 HTTP Status: {resp.status_code}")
        
        resp.raise_for_status()
        data = resp.json()
        
        # Print specific info about people returned
        people = data.get("people", [])
        total_results = data.get("total_results", 0)
        
        print(f"👥 People in response: {len(people)}")
        print(f"📈 Total results available: {total_results}")
        
        # Log the first person's complete details for debugging
        if people:
            first_person = people[0]
            print(f"🔍 First person returned:")
            print(f"   Name: {first_person.get('name', 'N/A')}")
            print(f"   Company: {first_person.get('organization_name', 'N/A')}")
            print(f"   Title: {first_person.get('title', 'N/A')}")
            print(f"   Location: {first_person.get('present_raw_address', 'N/A')}")
            print(f"\n📋 COMPLETE FIRST PERSON DATA:")
            print(f"{first_person}")
            print("=" * 80)
        
        return people
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for {company_name}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"📊 Error status: {e.response.status_code}")
            print(f"📋 Error response: {e.response.text}")
        return []
    except Exception as e:
        print(f"❌ Error processing response for {company_name}: {e}")
        return []



# — Interface Streamlit —

st.title("Contact Finder")

# Step 1 – get the list of company domains via an Excel file or manual input
st.subheader("1️⃣ Import Company Domains")
col1, col2 = st.columns(2)
all_comps = []
with col1:
    uploaded_file = st.file_uploader("Upload Excel file with company domains", type=["xlsx", "xls"])
    if uploaded_file:
        df_excel = pd.read_excel(uploaded_file)
        
        # Check for the required column
        if "Company Domain Name" not in df_excel.columns:
            st.error("Excel file must contain a 'Company Domain Name' column.")
            st.info(f"Available columns: {', '.join(df_excel.columns.tolist())}")
        else:
            # Load data from the Company Domain Name column
            all_comps += [n for n in df_excel["Company Domain Name"].dropna().unique()]
with col2:
    manual_companies = st.text_area(
        "Or enter company domains manually (one per line)",
        placeholder="google.com\nmicrosoft.com\napple.com",
        help="Enter domain names (without http:// or www.)"
    )
    if manual_companies:
        all_comps += [n.strip() for n in manual_companies.split("\n") if n.strip()]
# Remove duplicates and empty
all_comps = list({n for n in all_comps if n})
if not all_comps:
    st.warning("Please upload an Excel file with company domains or enter them manually.")
    st.stop()

all_comps = [{"id": i, "name": n, "type": "domains"} for i, n in enumerate(all_comps)]

st.info(f"📊 Total domains loaded: {len(all_comps)}")

# Step 2 – select domains & filters
st.subheader("2️⃣ Select Domains & Filters")
select_all = st.checkbox("Select All Domains")

if select_all:
    selected = [c["name"] for c in all_comps]
else:
    selected = st.multiselect(
        "Select domains",
        options=[c["name"] for c in all_comps],
        default=[]
    )
if len(selected) > 20:
    st.warning("You have selected more than 20 domains. This may take a while and could hit API rate limits.")

locations_input = st.text_input(
    "Location (1 to 2), separated by ; (e.g. London ; Paris)",
)
seniorities = st.multiselect(
    "Seniority (optional, select up to 2)",
    options=[
        "owner", "founder", "c_suite", "partner", "vp", "head",
        "director", "manager", "senior", "entry", "intern"
    ],
    default=[]
)
job_titles_input = st.text_input(
    "Job title (optional, up to 5), separated by ; (e.g. HR Director; Recruiter)"
)

if st.button("Start Search"):
    job_titles = [j.strip() for j in job_titles_input.split(";") if j.strip()]
    locations = [l.strip() for l in locations_input.split(";") if l.strip()]
    
    if not selected or not locations:
        st.error("Please select at least:\n• 1 domain\n• 1 location")
    else:
        try:
            # Clear all previous results and cache
            st.session_state["results"] = []  # Reset stored results
            if "search_cache" in st.session_state:
                del st.session_state["search_cache"]
            
            total_found = 0
            progress = st.progress(0, text="Searching contacts...")
            
            for idx, item in enumerate(selected):
                # st.write(f"🔍 **Now searching domain: {item}**")
                # For domains, we search without specific company name
                people = search_people(
                    company_name="",  # Empty company name when using domains
                    locations=locations,
                    job_titles=job_titles,
                    seniorities=seniorities,
                    domains=[item]
                )
                search_label = item  # Use domain as the label
                
                try:
                    company_results = 0
                    people_from_api = len(people)  # Store original count
                    
                    for p in people:
                        # Add the searched item (company or domain) to each person's data
                        p["searched_company"] = search_label
                        st.session_state["results"].append(p)
                        company_results += 1
                        total_found += 1
                    
                    # Debug info
                    if company_results > 0:
                        st.write(f"✅ {search_label}: Found {company_results} people")
                    else:
                        st.write(f"❌ {search_label}: No people found")
                        
                        # Additional debugging for failed searches
                        st.write(f"   🔍 API returned {people_from_api} people for {search_label}")
                        search_terms = []
                        if job_titles:
                            search_terms.append(f"titles: {', '.join(job_titles)}")
                        search_terms.append(f"locations: {', '.join(locations)}")
                        search_terms.append(f"domain: {item}")
                        st.write(f"   📍 Search terms: {' | '.join(search_terms)}")
                        if seniorities:
                            st.write(f"   👥 Seniorities: {', '.join(seniorities)}")
                        
                except Exception as e:
                    st.warning(f"Error searching {search_label}: {e}")
                progress.progress((idx + 1) / len(selected), text=f"Searched {idx + 1}/{len(selected)} domains")
                time.sleep(0.2)  # Small delay to avoid rate limits
            
            progress.empty()
            st.success(f"Total people found: {total_found}")
        except Exception as e:
            st.error(f"Error during search: {e}")

# Step 3 – Results and Export
if st.session_state.get("results"):
    st.subheader("3️⃣ Search Results")

# Pagination for results
def get_page(items, page, page_size):
    start = page * page_size
    end = start + page_size
    return items[start:end]

if st.session_state.get("results"):
    data = st.session_state["results"]
    rows = []
    for p in data:
        rows.append({
            "Name": p.get("name"),
            "Title": p.get("title"),
            "Company": p.get("searched_company"),  # Use the company that was searched for
            "Location": p.get("present_raw_address") or f"{p.get('city')}, {p.get('country')}",
            "LinkedIn": p.get("linkedin_url")
        })
    # Pagination controls
    page_size = 10
    total_pages = (len(rows) - 1) // page_size + 1
    
    # Initialize page in session state if not exists
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
    
    # Ensure current page is within valid range
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = 1
    
    # Top pagination control
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    with col1:
        if st.button("⬅️ Previous", key="prev_top", disabled=st.session_state.current_page <= 1):
            st.session_state.current_page -= 1
            st.rerun()
    with col3:
        top_page = st.number_input("Page", min_value=1, max_value=total_pages, value=st.session_state.current_page, step=1, key="page_top")
        if top_page != st.session_state.current_page:
            st.session_state.current_page = top_page
            st.rerun()
    with col5:
        if st.button("Next ➡️", key="next_top", disabled=st.session_state.current_page >= total_pages):
            st.session_state.current_page += 1
            st.rerun()
    
    page = st.session_state.current_page - 1  # Convert to 0-based for indexing
    paged_rows = get_page(rows, page, page_size)
    
    # Show results count
    start_idx = page * page_size + 1
    end_idx = min((page + 1) * page_size, len(rows))
    st.write(f"Showing {start_idx}-{end_idx} of {len(rows)} results")
    for i, row in enumerate(paged_rows):
        col1, col2 = st.columns([5, 1])
        with col1:
            linkedin_display = f"👤 [{row['LinkedIn']}]({row['LinkedIn']})" if row['LinkedIn'] else "👤 No LinkedIn profile"
            st.markdown(f"**{row['Name']}** – {row['Title']}  \n"
                        f"🏢 {row['Company']}  \n"
                        f"📍 {row['Location']}  \n"
                        f"{linkedin_display}")
        with col2:
            if st.button("Export to HubSpot", key=f"export_{page}_{i}"):
                try:
                    props = {
                        "firstname": row["Name"].split()[0] if row["Name"] else "",
                        "lastname": " ".join(row["Name"].split()[1:]) if row["Name"] and len(row["Name"].split()) > 1 else "",
                        "jobtitle": row["Title"] or "",
                        "company": row["Company"] or "",  # This now uses the searched company name
                        "linkedinbio": row["LinkedIn"] or "",
                        "city": row["Location"] or ""
                    }
                    hubspot_client.crm.contacts.basic_api.create(simple_public_object_input={"properties": props})
                    st.success(f"{row['Name']} exported to HubSpot.")
                except Exception as e:
                    st.error(f"Failed to export {row['Name']} to HubSpot: {e}")
    
    # Bottom pagination control
    st.divider()
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    with col1:
        if st.button("⬅️ Previous", key="prev_bottom", disabled=st.session_state.current_page <= 1):
            st.session_state.current_page -= 1
            st.rerun()
    with col3:
        bottom_page = st.number_input("Page", min_value=1, max_value=total_pages, value=st.session_state.current_page, step=1, key="page_bottom")
        if bottom_page != st.session_state.current_page:
            st.session_state.current_page = bottom_page
            st.rerun()
    with col5:
        if st.button("Next ➡️", key="next_bottom", disabled=st.session_state.current_page >= total_pages):
            st.session_state.current_page += 1
            st.rerun()
    
    # Show pagination info at bottom too
    st.write(f"Showing {start_idx}-{end_idx} of {len(rows)} results")
            