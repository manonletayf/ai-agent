import os
import streamlit as st
import requests
from dotenv import load_dotenv
import pandas as pd
import time
from urllib.parse import urlencode
import hubspot
from hubspot.crm.companies import BatchReadInputSimplePublicObjectId

load_dotenv()
if "results" not in st.session_state:
    st.session_state["results"] = []
if "selected_contacts" not in st.session_state:
    st.session_state["selected_contacts"] = []
if "hubspot_lists" not in st.session_state:
    st.session_state["hubspot_lists"] = pd.DataFrame()
if "hubspot_companies" not in st.session_state:
    st.session_state["hubspot_companies"] = []


def enrich_contact_email(person_id):
    """Enrich contact with email using Apollo API"""
    if not person_id:
        return None
        
    url = f"https://api.apollo.io/api/v1/people/match?id={person_id}"
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("APOLLO_API_KEY")
    }
    
    try:
        print(f"🔍 Enriching contact ID: {person_id}")
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        email = data.get("person", {}).get("email")
        print(f"📧 Email found: {email if email else 'No email available'}")
        return email
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to enrich contact {person_id}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error processing enrichment response for {person_id}: {e}")
        return None


def get_hubspot_company_lists():
    """Get all company lists from HubSpot using Context7 method"""
    
    access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    if not access_token:
        st.error("HUBSPOT_ACCESS_TOKEN not found in environment variables")
        return pd.DataFrame()
    
    client = hubspot.Client.create(access_token=access_token)
    
    # Method 1: Try SDK get_all() method with proper response handling
    try:
        lists_response = client.crm.lists.lists_api.get_all()
        
        # Based on Context7 findings, check for 'lists' attribute
        if hasattr(lists_response, 'lists') and lists_response.lists:
            all_lists = []
            for list_obj in lists_response.lists:
                list_data = {
                    "list_id": list_obj.list_id,
                    "name": list_obj.name,
                    "object_type_id": list_obj.object_type_id,
                    "size": list_obj.size,
                    "processing_status": list_obj.processing_status,
                    "created_at": list_obj.created_at,
                    "updated_at": list_obj.updated_at
                }
                all_lists.append(list_data)
            
            df = pd.DataFrame(all_lists)
            company_lists = df[df['object_type_id'] == '0-2'].copy()
            
            if len(company_lists) > 0:
                return company_lists
            
    except Exception as e:
        pass  # Continue to next method
    
    # Method 2: Try direct API request with pagination (Context7 recommended pattern)
    try:
        all_lists_data = []
        after = None
        page_count = 0
        
        while True:
            page_count += 1
            
            # Build request path with pagination
            path = "/crm/v3/lists?limit=100"
            if after:
                path += f"&after={after}"
            
            response = client.api_request({
                "path": path,
                "method": "GET"
            })
            
            if hasattr(response, 'json'):
                data = response.json()
                
                if 'lists' in data and data['lists']:
                    lists_on_page = data['lists']
                    
                    for list_obj in lists_on_page:
                        list_data = {
                            "list_id": list_obj['listId'],
                            "name": list_obj['name'],
                            "object_type_id": list_obj['objectTypeId'],
                            "size": list_obj['size'],
                            "processing_status": list_obj['processingStatus'],
                            "created_at": list_obj.get('createdAt', ''),
                            "updated_at": list_obj.get('updatedAt', '')
                        }
                        all_lists_data.append(list_data)
                    
                    # Check for next page
                    paging = data.get('paging', {})
                    if 'next' in paging and 'after' in paging['next']:
                        after = paging['next']['after']
                    else:
                        break
                else:
                    break
            else:
                break
        
        if all_lists_data:
            df = pd.DataFrame(all_lists_data)
            company_lists = df[df['object_type_id'] == '0-2'].copy()
            
            if len(company_lists) > 0:
                return company_lists
            
    except Exception as e:
        pass  # Continue to next method
    
    # Method 3: Search API as fallback (Context7 breakthrough method)
    try:
        all_lists_data = []
        offset = 0
        limit = 20
        
        while True:
            search_response = client.api_request({
                "path": "/crm/v3/lists/search",
                "method": "POST",
                "body": {
                    "query": "",
                    "limit": limit,
                    "offset": offset
                }
            })
            
            if hasattr(search_response, 'json'):
                search_data = search_response.json()
                
                # The search API returns lists in 'lists' key, not 'results'
                if 'lists' in search_data and search_data['lists']:
                    lists_on_page = search_data['lists']
                    
                    for list_obj in lists_on_page:
                        # Handle different response structure - some fields might be in additionalProperties
                        size = list_obj.get('size', 0)
                        if size == 0 and 'additionalProperties' in list_obj:
                            # Try to get size from additionalProperties
                            size_str = list_obj['additionalProperties'].get('hs_list_size', '0')
                            try:
                                size = int(size_str)
                            except (ValueError, TypeError):
                                size = 0
                        
                        list_data = {
                            "list_id": list_obj['listId'],
                            "name": list_obj['name'],
                            "object_type_id": list_obj['objectTypeId'],
                            "size": size,
                            "processing_status": list_obj['processingStatus'],
                            "created_at": list_obj.get('createdAt', ''),
                            "updated_at": list_obj.get('updatedAt', '')
                        }
                        all_lists_data.append(list_data)
                    
                    # Check if there are more results using hasMore
                    if not search_data.get('hasMore', False):
                        break
                    
                    offset += limit
                else:
                    break
            else:
                break
        
        if all_lists_data:
            df = pd.DataFrame(all_lists_data)
            company_lists = df[df['object_type_id'] == '0-2'].copy()
            
            if len(company_lists) > 0:
                return company_lists
            
    except Exception as e:
        pass  # Continue to next method
    
    # Method 4: Known lists as last resort
    try:
        known_company_lists = [20329]  # Add more known IDs here
        found_lists = []
        
        for list_id in known_company_lists:
            try:
                list_response = client.crm.lists.lists_api.get_by_id(list_id=list_id)
                
                if hasattr(list_response, 'list'):
                    list_obj = list_response.list
                    
                    if list_obj.object_type_id == '0-2':  # Company list
                        list_data = {
                            "list_id": list_obj.list_id,
                            "name": list_obj.name,
                            "object_type_id": list_obj.object_type_id,
                            "size": list_obj.size,
                            "processing_status": list_obj.processing_status,
                            "created_at": list_obj.created_at,
                            "updated_at": list_obj.updated_at
                        }
                        found_lists.append(list_data)
                        
            except Exception as e:
                pass  # Continue with next list ID
        
        if found_lists:
            df = pd.DataFrame(found_lists)
            return df
            
    except Exception as e:
        st.error(f"Error getting company lists: {e}")
    
    # If all methods fail, return empty DataFrame
    return pd.DataFrame()

def get_companies_from_hubspot_list(client, list_id, list_name):
    """Get companies from a specific HubSpot list"""
    try:
        # Get memberships
        memberships = client.crm.lists.memberships_api.get_page(list_id=list_id)
        
        if not memberships.results:
            return pd.DataFrame()
        
        company_ids = [m.record_id for m in memberships.results]
        
        # Get company details
        batch_input = BatchReadInputSimplePublicObjectId(
            inputs=[{"id": str(cid)} for cid in company_ids],
            properties=["name", "domain", "city", "industry", "phone", "website"]
        )
        
        response = client.crm.companies.batch_api.read(
            batch_read_input_simple_public_object_id=batch_input
        )
        
        companies = []
        for company in response.results:
            company_data = {
                "list_id": list_id,
                "list_name": list_name,
                "company_id": company.id,
                "name": company.properties.get('name', '') if company.properties else '',
                "domain": company.properties.get('domain', '') if company.properties else '',
                "city": company.properties.get('city', '') if company.properties else '',
                "industry": company.properties.get('industry', '') if company.properties else '',
                "phone": company.properties.get('phone', '') if company.properties else '',
                "website": company.properties.get('website', '') if company.properties else ''
            }
            companies.append(company_data)
        
        return pd.DataFrame(companies)
        
    except Exception as e:
        st.error(f"Error getting companies from list {list_name}: {e}")
        return pd.DataFrame()

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
            print(f"   ID: {first_person.get('id', 'N/A')}")
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

# Step 1 – get the list of company domains via an Excel file, manual input, or HubSpot lists
st.subheader("1️⃣ Import Company Domains")
col1, col2, col3 = st.columns(3)
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

with col3:
    st.write("**Or import from HubSpot lists:**")
    
    # Auto-load HubSpot lists if not already loaded
    hubspot_lists_df = st.session_state.get("hubspot_lists", pd.DataFrame())
    
    # If lists not loaded yet, load them automatically
    if not isinstance(hubspot_lists_df, pd.DataFrame) or hubspot_lists_df.empty:
        with st.spinner("Loading HubSpot company lists..."):
            hubspot_lists = get_hubspot_company_lists()
            if not hubspot_lists.empty:
                st.session_state["hubspot_lists"] = hubspot_lists
                hubspot_lists_df = hubspot_lists
            else:
                st.session_state["hubspot_lists"] = pd.DataFrame()
                hubspot_lists_df = pd.DataFrame()
    
    # Display dropdown if lists are available
    if isinstance(hubspot_lists_df, pd.DataFrame) and not hubspot_lists_df.empty:
        # Create dropdown options
        list_options = ["-- Select a HubSpot list --"]
        for _, row in hubspot_lists_df.iterrows():
            list_options.append(f"{row['name']} ({row['size']} companies)")
        
        selected_list = st.selectbox(
            "Select a HubSpot company list:",
            options=list_options,
            help="Choose a company list to import domains from"
        )
        
        # Add refresh button as a small secondary option
        if st.button("🔄", help="Refresh HubSpot lists", key="refresh_hubspot_lists"):
            st.session_state["hubspot_lists"] = pd.DataFrame()
            st.rerun()
        
        # Show details and import button when a list is selected
        if selected_list and selected_list != "-- Select a HubSpot list --":
            # Extract list name from the formatted string
            list_name = selected_list.split(" (")[0]
            
            # Find the corresponding list_id and details
            list_row = hubspot_lists_df[hubspot_lists_df['name'] == list_name]
            if not list_row.empty:
                list_data = list_row.iloc[0]
                
                # Import button
                if st.button("📥 Import Companies from List", key="import_hubspot_list"):
                    with st.spinner(f"Importing companies from '{list_data['name']}'..."):
                        access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
                        client = hubspot.Client.create(access_token=access_token)
                        
                        # Get companies from this list
                        companies_df = get_companies_from_hubspot_list(client, list_data['list_id'], list_data['name'])
                        
                        if not companies_df.empty:
                            # Extract domains and add to all_comps
                            domains = companies_df[companies_df['domain'].notna()]['domain'].unique()
                            domains = [d.strip() for d in domains if d.strip()]
                            
                            if domains:
                                all_comps += domains
                                st.success(f"✅ Imported {len(domains)} company domains from '{list_data['name']}'")
                                
                                # Store companies in session state for reference
                                st.session_state["hubspot_companies"] = companies_df.to_dict('records')
                                
                            else:
                                st.warning(f"❌ No domains found for companies in list '{list_data['name']}'")
                        else:
                            st.warning(f"❌ No companies found in list '{list_data['name']}'")
    else:
        # Show message when no lists are available
        if st.session_state.get("hubspot_lists") is not None:
            st.warning("No HubSpot company lists found")
            if st.button("🔄 Try Again", key="retry_hubspot_lists"):
                st.session_state["hubspot_lists"] = pd.DataFrame()
                st.rerun()
        else:
            st.info("Loading HubSpot lists...")
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
            "LinkedIn": p.get("linkedin_url"),
            "ID": p.get("id")  # Keep Apollo API ID for enrichment
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
            linkedin_display = f"👤 [LinkedIn]({row['LinkedIn']})" if row['LinkedIn'] else "👤 No LinkedIn profile"
            st.markdown(f"**{row['Name']}** – {row['Title']}  \n"
                        f"🏢 {row['Company']}  \n"
                        f"📍 {row['Location']}  \n"
                        f"{linkedin_display}")
        with col2:
            # Check if this contact is already selected
            contact_id = f"{row['Name']}_{row['Company']}_{row['Title']}"
            is_selected = any(c.get('contact_id') == contact_id for c in st.session_state["selected_contacts"])
            
            if is_selected:
                if st.button("✅ Selected", key=f"selected_{page}_{i}", disabled=True):
                    pass
            else:
                if st.button("Select and enrich", key=f"select_{page}_{i}"):
                    # Show enrichment progress
                    with st.spinner(f"Enriching {row['Name']}..."):
                        # Enrich contact with email
                        email = enrich_contact_email(row["ID"])
                    
                    # Add contact to selected list
                    contact_data = {
                        "contact_id": contact_id,
                        "ID": row["ID"],  # Apollo API ID for enrichment
                        "Name": row["Name"],
                        "Title": row["Title"], 
                        "Company": row["Company"],
                        "Location": row["Location"],
                        "LinkedIn": row["LinkedIn"],
                        "Email": email if email else "Not available"
                    }
                    st.session_state["selected_contacts"].append(contact_data)
                    
                    if email:
                        st.success(f"{row['Name']} selected! Email: {email}")
                    else:
                        st.success(f"{row['Name']} selected! (No email found)")
                    st.rerun()
    
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

# Step 4 - Selected Contacts & Export
if st.session_state.get("selected_contacts"):
    st.subheader("4️⃣ Selected Contacts")
    
    # Show count and clear button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"📋 **{len(st.session_state['selected_contacts'])} contacts selected**")
    with col2:
        if st.button("Clear All", type="secondary"):
            st.session_state["selected_contacts"] = []
            st.success("All selections cleared!")
            st.rerun()
    
    # Display selected contacts in a more compact format
    selected_df = pd.DataFrame(st.session_state["selected_contacts"])
    
    # Remove the contact_id column for display and reorder columns
    column_order = ['Name', 'Title', 'Company', 'Location', 'Email', 'LinkedIn', 'ID']
    display_df = selected_df[column_order]
    
    # Show the dataframe
    st.dataframe(display_df, use_container_width=True)
    
    # Download button
    if len(st.session_state["selected_contacts"]) > 0:
        # Prepare Excel file
        excel_buffer = pd.io.common.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            display_df.to_excel(writer, sheet_name='Selected Contacts', index=False)
        
        excel_buffer.seek(0)
        
        st.download_button(
            label="📥 Download Selected Contacts (Excel)",
            data=excel_buffer.getvalue(),
            file_name=f"selected_contacts_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
            