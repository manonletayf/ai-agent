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

st.title("🔍 People search via Apollo for HubSpot")

# Step 1 – get the list of companies via an Excel file or manual input
col1, col2 = st.columns(2)
all_comps = []
with col1:
    uploaded_file = st.file_uploader("Upload Excel file with company data", type=["xlsx", "xls"])
    if uploaded_file:
        df_excel = pd.read_excel(uploaded_file)
        
        # Check available columns
        available_columns = df_excel.columns.tolist()
        company_columns = []
        if "Company name" in available_columns:
            company_columns.append("Company name")
        if "Company Domain Name" in available_columns:
            company_columns.append("Company Domain Name")
        
        if not company_columns:
            st.error("Excel file must contain either 'Company name' or 'Company Domain Name' column.")
        else:
            # Let user choose which column to use
            selected_column = st.radio(
                "Choose data source:",
                company_columns,
                help="Select whether to use company names or domain names from your Excel file"
            )
            
            # Load data from selected column
            all_comps += [n for n in df_excel[selected_column].dropna().unique()]
            
            # Store the column type for later use
            st.session_state["excel_column_type"] = selected_column
with col2:
    # Determine if user is using domains from Excel to adjust manual input
    using_domains_excel = st.session_state.get("excel_column_type") == "Company Domain Name"
    
    if using_domains_excel:
        manual_input_label = "Or enter company domains manually (one per line)"
        manual_input_placeholder = "google.com\nmicrosoft.com\napple.com"
        manual_input_help = "Enter domain names (without http:// or www.)"
    else:
        manual_input_label = "Or enter company names manually (one per line)"
        manual_input_placeholder = "Company A\nCompany B\nCompany C"
        manual_input_help = "Enter full company names"
    
    manual_companies = st.text_area(
        manual_input_label,
        placeholder=manual_input_placeholder,
        help=manual_input_help
    )
    if manual_companies:
        all_comps += [n.strip() for n in manual_companies.split("\n") if n.strip()]
# Remove duplicates and empty
all_comps = list({n for n in all_comps if n})
if not all_comps:
    st.warning("Please upload an Excel file or enter company names manually.")
    st.stop()
# Determine if we're using domains or company names
using_domains = st.session_state.get("excel_column_type") == "Company Domain Name"
data_type = "domains" if using_domains else "companies"

all_comps = [{"id": i, "name": n, "type": data_type} for i, n in enumerate(all_comps)]

st.info(f"📊 Total {data_type} loaded: {len(all_comps)}")

# Step 2 – select companies & filters
select_all_label = f"Select All {data_type.title()}"
select_all = st.checkbox(select_all_label)

if select_all:
    selected = [c["name"] for c in all_comps]
else:
    multiselect_label = f"Select {data_type}"
    selected = st.multiselect(
        multiselect_label,
        options=[c["name"] for c in all_comps],
        default=[]
    )
if len(selected) > 20:
    st.warning("You have selected more than 20 companies. This may take a while and could hit API rate limits.")

job_titles_input = st.text_input(
    "Job title filters (optional, up to 5), separated by ; (e.g. HR Director; Recruiter)"
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
    
    # Check what type of data we're using
    using_domains = st.session_state.get("excel_column_type") == "Company Domain Name"
    data_type = "domains" if using_domains else "companies"
    
    if not selected or not locations:
        st.error(f"Please select at least:\n• 1 {data_type[:-1]}\n• 1 location")
    else:
        try:
            # Clear all previous results and cache
            st.session_state["results"] = []  # Reset stored results
            if "search_cache" in st.session_state:
                del st.session_state["search_cache"]
            
            total_found = 0
            progress = st.progress(0, text="Searching contacts...")
            
            st.write("🔍 **Search Parameters:**")
            if using_domains:
                st.write(f"• Domains: {selected}")
                st.write(f"• Job titles: {job_titles if job_titles else 'Any position'}")
                st.write(f"• Locations: {locations}")
                st.write(f"• Seniorities: {seniorities if seniorities else 'Any level'}")
            else:
                st.write(f"• Companies: {selected}")
                st.write(f"• Job titles: {job_titles if job_titles else 'Any position'}")
                st.write(f"• Locations: {locations}")
                st.write(f"• Seniorities: {seniorities if seniorities else 'Any level'}")
            
            for idx, item in enumerate(selected):
                if using_domains:
                    st.write(f"🔍 **Now searching domain: {item}**")
                    # For domains, we search without specific company name
                    people = search_people(
                        company_name="",  # Empty company name when using domains
                        locations=locations,
                        job_titles=job_titles,
                        seniorities=seniorities,
                        domains=[item]
                    )
                    search_label = item  # Use domain as the label
                else:
                    st.write(f"🔍 **Now searching company: {item}**")
                    people = search_people(
                        company_name=item,
                        locations=locations,
                        job_titles=job_titles,
                        seniorities=seniorities
                    )
                    search_label = item  # Use company name as the label
                
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
                        if using_domains:
                            search_terms.append(f"domain: {item}")
                        st.write(f"   📍 Search terms: {' | '.join(search_terms)}")
                        if seniorities:
                            st.write(f"   👥 Seniorities: {', '.join(seniorities)}")
                        
                except Exception as e:
                    st.warning(f"Error searching {search_label}: {e}")
                progress.progress((idx + 1) / len(selected), text=f"Searched {idx + 1}/{len(selected)} {data_type}")
                time.sleep(0.2)  # Small delay to avoid rate limits
            
            progress.empty()
            st.success(f"Total people found: {total_found}")
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
            "Company": p.get("searched_company"),  # Use the company that was searched for
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
                        "company": row["Company"] or "",  # This now uses the searched company name
                        "linkedinbio": row["LinkedIn"] or "",
                        "city": row["Location"] or ""
                    }
                    hubspot_client.crm.contacts.basic_api.create(simple_public_object_input={"properties": props})
                    st.success(f"{row['Name']} exported to HubSpot.")
                except Exception as e:
                    st.error(f"Failed to export {row['Name']} to HubSpot: {e}")
            