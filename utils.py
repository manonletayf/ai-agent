import os
import streamlit as st
import requests
from dotenv import load_dotenv
import pandas as pd
import time
from urllib.parse import urlencode
import hubspot
from hubspot.crm.companies import BatchReadInputSimplePublicObjectId

def check_authentication():
    """Check if user is authenticated with passcode"""
    # Get passcode from environment variable or use default
    correct_passcode = os.getenv("APP_PASSCODE", "contacts2024")
    
    if not st.session_state["authenticated"]:
        st.title("🔐 Access Protected")
        st.write("Please enter the passcode to access the Contacts Finder application.")
        
        # Create columns for better layout
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            passcode_input = st.text_input(
                "Enter Passcode:",
                type="password",
                placeholder="Enter your passcode",
                key="passcode_input"
            )
            
            if st.button("🔓 Access App", type="primary", use_container_width=True):
                if passcode_input == correct_passcode:
                    st.session_state["authenticated"] = True
                    st.success("✅ Access granted! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Incorrect passcode. Please try again.")
            
        
        # Add some styling and info
        st.markdown("---")
        st.info("💡 **Tip:** Contact your administrator if you don't have the passcode.")
        
        # Stop execution here if not authenticated
        return False
    
    return True

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


def export_contacts_to_hubspot(df, list_name="AI Agent Contacts", verify_membership=False, verbose=False):
    """
    Complete workflow to export contacts from a DataFrame to a HubSpot list.
    
    Args:
        df (pd.DataFrame): DataFrame with contact data. Expected columns:
                          Name, Title, Company, Location, Email, LinkedIn, ID
        list_name (str): Name of the HubSpot list to create/use
        verify_membership (bool): Whether to verify contacts were added to the list
        verbose (bool): Whether to show detailed progress messages
    
    Returns:
        dict: Summary of export results
    """
    access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    if not access_token:
        print("❌ HUBSPOT_ACCESS_TOKEN not found in environment variables")
        return {"success": False, "error": "Missing access token"}
    
    client = hubspot.Client.create(access_token=access_token)
    
    # Initialize results tracking
    results = {
        "success": True,
        "list_id": None,
        "list_name": list_name,
        "total_contacts": 0,
        "created_contacts": 0,
        "existing_contacts": 0,
        "updated_contacts": 0,
        "added_to_list": 0,
        "verification": {},
        "errors": []
    }
    
    try:
        # Step 1: Get or create the list
        if verbose:
            print(f"🔍 Checking if list '{list_name}' exists...")
        
        list_id = None
        
        # Check if list exists using search API
        try:
            search_response = client.api_request({
                "path": "/crm/v3/lists/search",
                "method": "POST",
                "body": {
                    "query": list_name,
                    "limit": 100,
                    "offset": 0
                }
            })
            
            if hasattr(search_response, 'json'):
                search_data = search_response.json()
                if 'lists' in search_data and search_data['lists']:
                    for existing_list in search_data['lists']:
                        if existing_list.get('name') == list_name and existing_list.get('objectTypeId') == '0-1':
                            list_id = existing_list['listId']
                            if verbose:
                                print(f"✅ List '{list_name}' found with ID: {list_id}")
                            break
        except Exception as e:
            if verbose:
                print(f"⚠️ Could not search for existing lists: {e}")
        
        # Create list if it doesn't exist
        if not list_id:
            if verbose:
                print(f"📝 Creating new contacts list '{list_name}'...")
            
            create_response = client.api_request({
                "path": "/crm/v3/lists",
                "method": "POST",
                "body": {
                    "name": list_name,
                    "objectTypeId": "0-1",  # 0-1 is for contacts
                    "processingType": "MANUAL"  # Required for membership operations
                }
            })
            
            if hasattr(create_response, 'json'):
                response_data = create_response.json()
                list_id = response_data.get('listId') or response_data.get('list', {}).get('listId')
                
                if list_id:
                    if verbose:
                        print(f"✅ Created contacts list '{list_name}' with ID: {list_id}")
                else:
                    raise Exception(f"Failed to create list: {response_data}")
        
        if not list_id:
            raise Exception("Failed to create or find contacts list")
        
        results["list_id"] = list_id
        
        # Step 2: Validate DataFrame and filter contacts
        # Check for required columns - either separate First/Last Name or combined Name
        has_separate_names = 'First Name' in df.columns and 'Last Name' in df.columns
        has_combined_name = 'Name' in df.columns
        
        if not has_separate_names and not has_combined_name:
            raise Exception("Missing required name columns: Either 'First Name' and 'Last Name' or 'Name' is required")
        
        if 'Email' not in df.columns:
            raise Exception("Missing required column: 'Email'")
        
        # Filter valid contacts
        valid_contacts = df[df['Email'].notna() & (df['Email'] != 'Not available') & (df['Email'] != '')].copy()
        
        if len(valid_contacts) == 0:
            raise Exception("No valid contacts with email addresses found")
        
        results["total_contacts"] = len(valid_contacts)
        
        if verbose:
            print(f"📊 Processing {len(valid_contacts)} contacts...")
        
        # Step 3: Process each contact
        contacts_to_add_to_list = []
        
        for index, row in valid_contacts.iterrows():
            try:
                email = row['Email']
                
                # Use separate First Name and Last Name fields if available, otherwise split Name
                if 'First Name' in row and 'Last Name' in row:
                    firstname = row['First Name'] if pd.notna(row['First Name']) else ''
                    lastname = row['Last Name'] if pd.notna(row['Last Name']) else ''
                    name = f"{firstname} {lastname}".strip()
                else:
                    # Fallback to splitting Name field for backward compatibility
                    name = row['Name']
                    name_parts = name.split(' ', 1) if isinstance(name, str) else ['', '']
                    firstname = name_parts[0] if len(name_parts) > 0 else ''
                    lastname = name_parts[1] if len(name_parts) > 1 else ''
                
                if verbose:
                    print(f"🔍 Processing: {name} ({email})")
                
                # Check if contact exists
                existing_contact = None
                try:
                    search_response = client.api_request({
                        "path": "/crm/v3/objects/contacts/search",
                        "method": "POST",
                        "body": {
                            "filterGroups": [
                                {
                                    "filters": [
                                        {
                                            "propertyName": "email",
                                            "operator": "EQ",
                                            "value": email
                                        }
                                    ]
                                }
                            ],
                            "properties": ["email", "firstname", "lastname", "jobtitle", "company"],
                            "limit": 1
                        }
                    })
                    
                    if hasattr(search_response, 'json'):
                        search_data = search_response.json()
                        if 'results' in search_data and len(search_data['results']) > 0:
                            existing_contact = search_data['results'][0]
                            results["existing_contacts"] += 1
                            
                except Exception as e:
                    if verbose:
                        print(f"⚠️ Error searching for contact {email}: {e}")
                
                # Create or update contact
                contact_id = None
                
                if existing_contact:
                    # Update existing contact
                    contact_id = existing_contact['id']
                    
                    # Prepare update properties
                    update_properties = {}
                    if 'Title' in row and pd.notna(row['Title']) and row['Title']:
                        update_properties["jobtitle"] = str(row['Title'])
                    if 'Company' in row and pd.notna(row['Company']) and row['Company']:
                        update_properties["company"] = str(row['Company'])
                    if 'Location' in row and pd.notna(row['Location']) and row['Location']:
                        update_properties["city"] = str(row['Location'])
                    
                    if update_properties:
                        try:
                            client.api_request({
                                "path": f"/crm/v3/objects/contacts/{contact_id}",
                                "method": "PATCH",
                                "body": {"properties": update_properties}
                            })
                            results["updated_contacts"] += 1
                            if verbose:
                                print(f"✅ Updated contact: {contact_id}")
                        except Exception as e:
                            results["errors"].append(f"Failed to update contact {email}: {str(e)}")
                    
                else:
                    # Create new contact
                    properties = {
                        "email": email,
                        "firstname": firstname,
                        "lastname": lastname
                    }
                    
                    # Add optional properties
                    if 'Title' in row and pd.notna(row['Title']) and row['Title']:
                        properties["jobtitle"] = str(row['Title'])
                    if 'Company' in row and pd.notna(row['Company']) and row['Company']:
                        properties["company"] = str(row['Company'])
                    if 'Location' in row and pd.notna(row['Location']) and row['Location']:
                        properties["city"] = str(row['Location'])
                    
                    try:
                        create_response = client.api_request({
                            "path": "/crm/v3/objects/contacts",
                            "method": "POST",
                            "body": {"properties": properties}
                        })
                        
                        if hasattr(create_response, 'json'):
                            contact_data = create_response.json()
                            contact_id = contact_data.get('id')
                            if contact_id:
                                results["created_contacts"] += 1
                                if verbose:
                                    print(f"✅ Created contact: {contact_id}")
                            else:
                                raise Exception("No contact ID in response")
                    except Exception as e:
                        results["errors"].append(f"Failed to create contact {email}: {str(e)}")
                        continue
                
                # Add contact ID to list if we have one
                if contact_id:
                    contacts_to_add_to_list.append(contact_id)
                        
            except Exception as e:
                results["errors"].append(f"Error processing contact {row.get('Name', 'Unknown')}: {str(e)}")
        
        # Step 4: Add all contacts to the list
        if contacts_to_add_to_list:
            try:
                if verbose:
                    print(f"🎯 Adding {len(contacts_to_add_to_list)} contacts to list {list_id}...")
                
                # Import the MembershipChangeRequest class
                from hubspot.crm.lists import MembershipChangeRequest
                
                # Create membership change request
                membership_change_request = MembershipChangeRequest(
                    record_ids_to_add=contacts_to_add_to_list,
                    record_ids_to_remove=[]
                )
                
                # Add contacts to list
                api_response = client.crm.lists.memberships_api.add_and_remove(
                    list_id=list_id, 
                    membership_change_request=membership_change_request
                )
                
                # Count added contacts
                if hasattr(api_response, 'records_ids_added'):
                    added_count = len(api_response.records_ids_added) if api_response.records_ids_added else 0
                    results["added_to_list"] = added_count
                else:
                    results["added_to_list"] = len(contacts_to_add_to_list)
                
                if verbose:
                    print(f"✅ {results['added_to_list']} contacts added to list")
                    
            except Exception as e:
                results["errors"].append(f"Failed to add contacts to list: {str(e)}")
                results["added_to_list"] = 0
        
        # Step 5: Optional verification
        if verify_membership:
            try:
                if verbose:
                    print(f"🔍 Verifying list membership...")
                
                # Get list memberships
                memberships_response = client.api_request({
                    "path": f"/crm/v3/lists/{list_id}/memberships",
                    "method": "GET",
                    "params": {"limit": 100}
                })
                
                verification_data = {
                    "total_members": 0,
                    "verified_contacts": [],
                    "verification_errors": []
                }
                
                if hasattr(memberships_response, 'json'):
                    membership_data = memberships_response.json()
                    
                    if 'results' in membership_data and membership_data['results']:
                        memberships = membership_data['results']
                        verification_data["total_members"] = len(memberships)
                        
                        # Get contact details for verification
                        for membership in memberships:
                            contact_id = membership.get('recordId')
                            try:
                                contact_response = client.api_request({
                                    "path": f"/crm/v3/objects/contacts/{contact_id}",
                                    "method": "GET",
                                    "params": {"properties": "email,firstname,lastname,jobtitle,company"}
                                })
                                
                                if hasattr(contact_response, 'json'):
                                    contact_data = contact_response.json()
                                    props = contact_data.get('properties', {})
                                    
                                    contact_info = {
                                        "id": contact_id,
                                        "email": props.get('email', ''),
                                        "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                                        "title": props.get('jobtitle', ''),
                                        "company": props.get('company', '')
                                    }
                                    verification_data["verified_contacts"].append(contact_info)
                                    
                            except Exception as e:
                                verification_data["verification_errors"].append(f"Failed to get contact {contact_id}: {str(e)}")
                
                results["verification"] = verification_data
                
                if verbose:
                    print(f"✅ Verification complete: {verification_data['total_members']} members found")
                    
            except Exception as e:
                results["errors"].append(f"Verification failed: {str(e)}")
        
        # Print summary
        print(f"\n📊 Export Summary:")
        print(f"   List: {results['list_name']} (ID: {results['list_id']})")
        print(f"   Total contacts processed: {results['total_contacts']}")
        print(f"   New contacts created: {results['created_contacts']}")
        print(f"   Existing contacts found: {results['existing_contacts']}")
        print(f"   Contacts updated: {results['updated_contacts']}")
        print(f"   Contacts added to list: {results['added_to_list']}")
        
        if verify_membership and results['verification']:
            print(f"   Verified list members: {results['verification']['total_members']}")
        
        if results['errors']:
            print(f"   Errors: {len(results['errors'])}")
            if verbose:
                for error in results['errors']:
                    print(f"     - {error}")
        
        return results
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Export failed: {str(e)}")
        print(f"❌ Export failed: {e}")
        return results

def main_app():
    """Main application content"""
    # Add logout option in sidebar
    with st.sidebar:
        st.markdown("### 🔐 Session")
        if st.button("🚪 Logout", type="secondary"):
            st.session_state["authenticated"] = False
            st.success("Logged out successfully!")
            time.sleep(1)
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ App Info")
        st.write("**Contacts Finder**")
        st.write("Find and enrich contacts from company domains")

    # — Interface Streamlit —

    st.title("Contacts Finder")

    # Step 1 – get the list of company domains via an Excel file, manual input, or HubSpot lists
    st.subheader("1️⃣ Import Company Domains")
    col1, col2, col3 = st.columns(3)

    # Use session state to persist imported companies across re-runs
    all_comps = st.session_state["all_companies"].copy()

    with col1:
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"], help="Upload an Excel file with a 'Company Domain Name' column")
        if uploaded_file:
            df_excel = pd.read_excel(uploaded_file)
            
            # Check for the required column
            if "Company Domain Name" not in df_excel.columns:
                st.error("Excel file must contain a 'Company Domain Name' column.")
                st.info(f"Available columns: {', '.join(df_excel.columns.tolist())}")
            else:
                # Load data from the Company Domain Name column
                excel_domains = [n for n in df_excel["Company Domain Name"].dropna().unique()]
                all_comps += excel_domains
                # Update session state
                st.session_state["all_companies"] = all_comps

    with col2:
        manual_companies = st.text_area(
            "Type manually (one per line)",
            placeholder="google.com\nmicrosoft.com\napple.com",
            help="Enter domain names (without http:// or www.)",
            key="manual_text_area",
            height=135
        )
        if manual_companies:
            manual_domains = [n.strip() for n in manual_companies.split("\n") if n.strip()]
            all_comps += manual_domains
            # Update session state
            st.session_state["all_companies"] = all_comps

    with col3:
        
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
            
            # Show details and import button when a list is selected
            if selected_list and selected_list != "-- Select a HubSpot list --":
                # Extract list name from the formatted string
                list_name = selected_list.split(" (")[0]
                
                # Find the corresponding list_id and details
                list_row = hubspot_lists_df[hubspot_lists_df['name'] == list_name]
                if not list_row.empty:
                    list_data = list_row.iloc[0]
                    
                    # Import button
                    if st.button("Import company domains", key="import_hubspot_list", use_container_width=True):
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
                                    # Update session state
                                    st.session_state["all_companies"] = all_comps
                                    # st.success(f"Imported {len(domains)} company domains")
                                    
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
    unique_domains = list({n for n in all_comps if n})
    # Update session state with cleaned list
    st.session_state["all_companies"] = unique_domains

    if not unique_domains:
        st.warning("Please upload an Excel file with company domains or enter them manually.")
        st.stop()

    all_comps = [{"id": i, "name": n, "type": "domains"} for i, n in enumerate(unique_domains)]

    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Total domains loaded: {len(all_comps)}")
    with col2:
        if len(all_comps) > 0 and st.button("🗑️ Clear All Domains", type="secondary"):
            st.session_state["all_companies"] = []
            st.session_state["selected_domains"] = []
            # Clear manual text area
            if "manual_text_area" in st.session_state:
                del st.session_state["manual_text_area"]
            st.success("All domains cleared!")
            st.rerun()

    # Step 2 – select domains & filters
    st.subheader("2️⃣ Select Domains & Filters")

    # Get available domain names
    available_domains = [c["name"] for c in all_comps]

    # Clean up selected domains - only keep those still available
    valid_selected = [domain for domain in st.session_state["selected_domains"] if domain in available_domains]

    # Select all checkbox
    select_all = st.checkbox("Select All Domains")

    # Handle select all logic
    if select_all:
        selected = available_domains
        # Only update session state when select all is used
        st.session_state["selected_domains"] = selected
    else:
        # Use the multiselect widget without immediate session state updates
        selected = st.multiselect(
            "Select domains",
            options=available_domains,
            default=valid_selected
        )
        # Don't update session state immediately - let the widget handle its own state
        # Only update session state when we actually need persistence (like before search)
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
        
        # Update session state with current selections for persistence
        st.session_state["selected_domains"] = selected
        
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
            # Extract first_name and last_name separately
            first_name = p.get("first_name", "")
            last_name = p.get("last_name", "")
            display_name = f"{first_name} {last_name}".strip()
            
            rows.append({
                "First Name": first_name,
                "Last Name": last_name,
                "Display Name": display_name,  # For UI display compatibility
                "Name": display_name,  # Keep for backward compatibility
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
                            "First Name": row["First Name"],
                            "Last Name": row["Last Name"],
                            "Name": row["Display Name"],  # Combined name for display
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
        column_order = ['First Name', 'Last Name', 'Title', 'Company', 'Location', 'Email', 'LinkedIn', 'ID']
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
            
        # Export options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="Download as Excel file",
                data=excel_buffer.getvalue(),
                file_name=f"selected_contacts_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            # Add HubSpot list name input
            hubspot_list_name = st.text_input(
                "HubSpot List Name",
                value="AI Agent Contacts",
                help="Name of the HubSpot list to create or add contacts to",
                key="hubspot_list_name"
            )
            
            if st.button("Export to HubSpot", type="primary", use_container_width=True):
                if st.session_state["selected_contacts"]:
                    with st.spinner("Exporting to HubSpot..."):
                        try:
                            # Convert selected contacts to DataFrame
                            export_df = pd.DataFrame(st.session_state["selected_contacts"])
                            
                            # Call the HubSpot export function
                            results = export_contacts_to_hubspot(
                                df=export_df,
                                list_name=hubspot_list_name or "AI Agent Contacts",
                                verify_membership=True,
                                verbose=True
                            )
                            
                            if results["success"]:
                                st.success(f"Successfully exported to HubSpot")
                                st.info(f"**Export Summary:**\n"
                                        f"- List: {results['list_name']} (ID: {results['list_id']})\n"
                                        f"- Total contacts processed: {results['total_contacts']}\n"
                                        f"- New contacts created: {results['created_contacts']}\n"
                                        f"- Existing contacts found: {results['existing_contacts']}\n"
                                        f"- Contacts updated: {results['updated_contacts']}\n"
                                        f"- Contacts added to list: {results['added_to_list']}")
                                
                                if results['errors']:
                                    st.warning(f"⚠️ {len(results['errors'])} errors occurred:")
                                    for error in results['errors']:
                                        st.warning(f"- {error}")
                            else:
                                st.error(f"❌ Export failed!")
                                if results['errors']:
                                    for error in results['errors']:
                                        st.error(f"- {error}")
                                        
                        except Exception as e:
                            st.error(f"❌ Error during HubSpot export: {e}")
                else:
                    st.warning("No contacts selected to export.") 