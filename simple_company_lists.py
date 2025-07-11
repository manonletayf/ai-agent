#!/usr/bin/env python3
"""
Simple script to get all company lists using working methods
"""

import os
import pandas as pd
import hubspot
from dotenv import load_dotenv
from datetime import datetime
from hubspot.crm.companies import BatchReadInputSimplePublicObjectId

load_dotenv()

def get_all_company_lists_with_context7():
    """
    Retrieve all company lists from HubSpot using Context7 MCP findings.
    
    This function uses multiple methods based on HubSpot API documentation:
    1. SDK get_all() method with proper response handling
    2. Direct API request with pagination support
    3. Search API as fallback
    
    Returns:
        pd.DataFrame: DataFrame containing company lists with columns:
                     - list_id: HubSpot list ID
                     - name: List name
                     - object_type_id: Object type (0-2 for companies)
                     - size: Number of companies in list
                     - processing_status: Current processing status
                     - created_at: Creation timestamp
                     - updated_at: Last update timestamp
    """
    
    print("🚀 RETRIEVING ALL COMPANY LISTS FROM HUBSPOT (Context7 Method)")
    print("=" * 70)
    
    access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    if not access_token:
        print("❌ HUBSPOT_ACCESS_TOKEN not found in environment variables")
        return pd.DataFrame()
    
    # Initialize HubSpot client using Context7 recommended pattern
    client = hubspot.Client.create(access_token=access_token)
    
    # Method 1: Use SDK get_all() method with proper response handling
    print("\n1. 🔍 Trying SDK get_all() method...")
    try:
        lists_response = client.crm.lists.lists_api.get_all()
        
        # Based on Context7 findings, check for 'lists' attribute
        if hasattr(lists_response, 'lists') and lists_response.lists:
            print(f"   ✅ SDK method found {len(lists_response.lists)} lists")
            
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
                print(f"   🏢 Found {len(company_lists)} company lists via SDK")
                return company_lists
            else:
                print("   ℹ️  No company lists found via SDK")
        else:
            print("   ℹ️  SDK method returned no lists")
            
    except Exception as e:
        print(f"   ❌ SDK method failed: {e}")
    
    # Method 2: Direct API request with pagination (Context7 recommended pattern)
    print("\n2. 🔍 Trying direct API request with pagination...")
    try:
        all_lists_data = []
        after = None
        page_count = 0
        
        while True:
            page_count += 1
            print(f"   📄 Fetching page {page_count}...")
            
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
                    print(f"   ✅ Page {page_count}: {len(lists_on_page)} lists")
                    
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
                    print(f"   ℹ️  Page {page_count}: No lists found")
                    break
            else:
                print(f"   ❌ Page {page_count}: No JSON response")
                break
        
        if all_lists_data:
            df = pd.DataFrame(all_lists_data)
            company_lists = df[df['object_type_id'] == '0-2'].copy()
            
            print(f"   📊 Total lists found: {len(df)}")
            print(f"   🏢 Company lists: {len(company_lists)}")
            
            if len(company_lists) > 0:
                return company_lists
            else:
                print("   ℹ️  No company lists found via direct API")
        else:
            print("   ℹ️  No lists data retrieved via direct API")
            
    except Exception as e:
        print(f"   ❌ Direct API method failed: {e}")
    
    # Method 3: Search API as fallback
    print("\n3. 🔍 Trying search API as fallback...")
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
                    print(f"   📄 Page {offset//limit + 1}: Found {len(lists_on_page)} lists")
                    
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
                    print(f"   📄 Page {offset//limit + 1}: No lists found")
                    break
            else:
                print("   ❌ Search API: No JSON response")
                break
        
        if all_lists_data:
            df = pd.DataFrame(all_lists_data)
            company_lists = df[df['object_type_id'] == '0-2'].copy()
            
            print(f"   ✅ Search API found {len(all_lists_data)} total lists")
            print(f"   🏢 Found {len(company_lists)} company lists via search API")
            
            if len(company_lists) > 0:
                return company_lists
            else:
                print("   ℹ️  No company lists found via search API")
        else:
            print("   ℹ️  Search API returned no results")
            
    except Exception as e:
        print(f"   ❌ Search API method failed: {e}")
    
    # Method 4: Known lists as last resort (from previous testing)
    print("\n4. 🔍 Checking known company lists as last resort...")
    try:
        known_company_lists = [20329]  # Add more known IDs here
        found_lists = []
        
        for list_id in known_company_lists:
            try:
                print(f"   📋 Checking list ID {list_id}...")
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
                        print(f"   ✅ Found company list: {list_obj.name} (Size: {list_obj.size})")
                    else:
                        print(f"   ℹ️  List {list_id} is not a company list (Type: {list_obj.object_type_id})")
                        
            except Exception as e:
                print(f"   ❌ Error checking list {list_id}: {e}")
        
        if found_lists:
            df = pd.DataFrame(found_lists)
            print(f"   🏢 Found {len(found_lists)} known company lists")
            return df
        else:
            print("   ℹ️  No known company lists found")
            
    except Exception as e:
        print(f"   ❌ Known lists method failed: {e}")
    
    print("\n❌ All methods failed - no company lists found")
    return pd.DataFrame()

def display_company_lists_summary(company_lists_df):
    """
    Display a comprehensive summary of company lists found.
    
    Args:
        company_lists_df (pd.DataFrame): DataFrame containing company lists
    """
    
    if company_lists_df.empty:
        print("\n📋 No company lists to display")
        return
    
    print(f"\n📋 COMPANY LISTS SUMMARY")
    print("=" * 50)
    print(f"Total company lists found: {len(company_lists_df)}")
    
    # Sort by size (descending) to show largest lists first
    sorted_lists = company_lists_df.sort_values('size', ascending=False)
    
    print(f"\n🏆 TOP COMPANY LISTS:")
    for idx, (_, row) in enumerate(sorted_lists.head(10).iterrows(), 1):
        print(f"   {idx:2d}. {row['name']}")
        print(f"       ID: {row['list_id']} | Size: {row['size']} companies")
        print(f"       Status: {row['processing_status']}")
        print(f"       Created: {row['created_at']}")
        print()
    
    # Show statistics
    total_companies = sorted_lists['size'].sum()
    avg_size = sorted_lists['size'].mean()
    
    print(f"📊 STATISTICS:")
    print(f"   Total companies across all lists: {total_companies:,}")
    print(f"   Average list size: {avg_size:.1f} companies")
    print(f"   Largest list: {sorted_lists.iloc[0]['name']} ({sorted_lists.iloc[0]['size']} companies)")
    print(f"   Smallest list: {sorted_lists.iloc[-1]['name']} ({sorted_lists.iloc[-1]['size']} companies)")

def get_all_company_lists():
    """Get all company lists from HubSpot"""
    
    access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    client = hubspot.Client.create(access_token=access_token)
    
    print("🚀 GETTING ALL COMPANY LISTS FROM HUBSPOT")
    print("="*60)
    
    # Method 1: Try get_all() - it might return paginated results
    print("\n1. Trying get_all() method...")
    try:
        lists_response = client.crm.lists.lists_api.get_all()
        
        if hasattr(lists_response, 'results') and lists_response.results:
            print(f"   ✅ Found {len(lists_response.results)} lists")
            
            all_lists = []
            for list_obj in lists_response.results:
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
            
            # Filter for company lists
            company_lists = df[df['object_type_id'] == '0-2'].copy()
            
            print(f"\n🏢 COMPANY LISTS FOUND:")
            print(f"   Total lists: {len(df)}")
            print(f"   Company lists: {len(company_lists)}")
            
            if len(company_lists) > 0:
                print(f"\n📋 COMPANY LISTS DETAILS:")
                for _, row in company_lists.iterrows():
                    print(f"   • {row['name']}")
                    print(f"     ID: {row['list_id']}, Size: {row['size']}")
                    print()
                
                # Save company lists
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"company_lists_{timestamp}.csv"
                company_lists.to_csv(filename, index=False)
                print(f"📁 Company lists saved to: {filename}")
                
                return company_lists
            else:
                print("❌ No company lists found")
                return pd.DataFrame()
        else:
            print("   ❌ No lists returned")
            
    except Exception as e:
        print(f"   ❌ get_all() failed: {e}")
        
    # Method 2: Try direct REST API via client
    print("\n2. Trying direct REST API call...")
    try:
        # This worked in our debug script
        response = client.api_request({
            "path": "/crm/v3/lists",
            "method": "GET"
        })
        
        if hasattr(response, 'json'):
            data = response.json()
            if 'results' in data:
                print(f"   ✅ Found {len(data['results'])} lists via REST API")
                
                all_lists = []
                for list_obj in data['results']:
                    list_data = {
                        "list_id": list_obj['listId'],
                        "name": list_obj['name'],
                        "object_type_id": list_obj['objectTypeId'],
                        "size": list_obj['size'],
                        "processing_status": list_obj['processingStatus'],
                        "created_at": list_obj.get('createdAt', ''),
                        "updated_at": list_obj.get('updatedAt', '')
                    }
                    all_lists.append(list_data)
                
                df = pd.DataFrame(all_lists)
                
                # Filter for company lists
                company_lists = df[df['object_type_id'] == '0-2'].copy()
                
                print(f"\n🏢 COMPANY LISTS FOUND:")
                print(f"   Total lists: {len(df)}")
                print(f"   Company lists: {len(company_lists)}")
                
                if len(company_lists) > 0:
                    print(f"\n📋 COMPANY LISTS DETAILS:")
                    for _, row in company_lists.iterrows():
                        print(f"   • {row['name']}")
                        print(f"     ID: {row['list_id']}, Size: {row['size']}")
                        print()
                    
                    # Save company lists
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"company_lists_{timestamp}.csv"
                    company_lists.to_csv(filename, index=False)
                    print(f"📁 Company lists saved to: {filename}")
                    
                    return company_lists
                else:
                    print("❌ No company lists found")
                    return pd.DataFrame()
            else:
                print("   ❌ No results in response")
        else:
            print("   ❌ No JSON in response")
            
    except Exception as e:
        print(f"   ❌ REST API call failed: {e}")
    
    # Method 3: Manual list - we know 20329 exists
    print("\n3. Manual collection of known lists...")
    try:
        known_lists = [20329]  # Add more if you know them
        
        found_lists = []
        for list_id in known_lists:
            try:
                list_response = client.crm.lists.lists_api.get_by_id(list_id=list_id)
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
                    print(f"   ✅ Found company list: {list_obj.name}")
                    
            except Exception as e:
                print(f"   ❌ Error getting list {list_id}: {e}")
        
        if found_lists:
            df = pd.DataFrame(found_lists)
            return df
        else:
            print("   ❌ No known company lists found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"   ❌ Manual collection failed: {e}")
        return pd.DataFrame()

def get_companies_from_list(client, list_id, list_name):
    """Get companies from a specific list"""
    print(f"\n🔍 Getting companies from: {list_name} (ID: {list_id})")
    
    try:
        # Get memberships
        memberships = client.crm.lists.memberships_api.get_page(list_id=list_id)
        
        if not memberships.results:
            print("   No companies found")
            return pd.DataFrame()
        
        company_ids = [m.record_id for m in memberships.results]
        print(f"   Found {len(company_ids)} company IDs")
        
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
        
        print(f"   ✅ Retrieved {len(companies)} companies")
        return pd.DataFrame(companies)
        
    except Exception as e:
        print(f"   ❌ Error getting companies: {e}")
        return pd.DataFrame()

def test_context7_method():
    """Test the new Context7 method for retrieving company lists"""
    print("🧪 TESTING CONTEXT7 METHOD FOR COMPANY LISTS")
    print("=" * 60)
    
    # Test the new Context7 method
    company_lists = get_all_company_lists_with_context7()
    
    # Display comprehensive summary
    display_company_lists_summary(company_lists)
    
    # Save results if found
    if not company_lists.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"company_lists_context7_{timestamp}.csv"
        company_lists.to_csv(filename, index=False)
        print(f"\n💾 Company lists saved to: {filename}")
        
        # Return the DataFrame for further processing
        return company_lists
    else:
        print("\n❌ No company lists found to save")
        return pd.DataFrame()

def test_context7_only():
    """Test only the Context7 method for retrieving company lists"""
    print("🧪 TESTING CONTEXT7 METHOD ONLY")
    print("=" * 50)
    
    # Test the new Context7 method
    company_lists = get_all_company_lists_with_context7()
    
    # Display comprehensive summary
    display_company_lists_summary(company_lists)
    
    # Save results if found
    if not company_lists.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"company_lists_context7_only_{timestamp}.csv"
        company_lists.to_csv(filename, index=False)
        print(f"\n💾 Company lists saved to: {filename}")
        
        # Show detailed list of all company lists
        print(f"\n📋 ALL COMPANY LISTS FOUND:")
        for idx, (_, row) in enumerate(company_lists.iterrows(), 1):
            print(f"   {idx:2d}. {row['name']}")
            print(f"       📊 ID: {row['list_id']} | Size: {row['size']} companies")
            print(f"       📈 Status: {row['processing_status']}")
            print(f"       📅 Created: {row['created_at']}")
            print(f"       🔄 Updated: {row['updated_at']}")
            print()
        
        return company_lists
    else:
        print("\n❌ No company lists found")
        return pd.DataFrame()

def main():
    """Main function"""
    try:
        # Test the new Context7 method first
        print("🚀 TESTING NEW CONTEXT7 METHOD")
        print("=" * 60)
        
        company_lists = test_context7_method()
        
        # If Context7 method didn't find anything, try the original method
        if company_lists.empty:
            print("\n🔄 FALLING BACK TO ORIGINAL METHOD")
            print("=" * 60)
            company_lists = get_all_company_lists()
        
        if company_lists.empty:
            print("\n❌ No company lists found with any method")
            return
        
        # Get companies from each list
        print(f"\n📤 EXTRACTING COMPANIES FROM ALL COMPANY LISTS...")
        
        client = hubspot.Client.create(access_token=os.getenv("HUBSPOT_ACCESS_TOKEN"))
        
        all_companies = []
        for _, row in company_lists.iterrows():
            companies_df = get_companies_from_list(client, row['list_id'], row['name'])
            if not companies_df.empty:
                all_companies.append(companies_df)
        
        if all_companies:
            # Combine all companies
            combined_df = pd.concat(all_companies, ignore_index=True)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"all_company_lists_contents_{timestamp}.csv"
            combined_df.to_csv(filename, index=False)
            
            print(f"\n📊 FINAL RESULTS:")
            print(f"   Company lists found: {len(company_lists)}")
            print(f"   Total companies: {len(combined_df)}")
            print(f"   📁 Saved to: {filename}")
            
            # Show sample companies
            if 'name' in combined_df.columns:
                print(f"\n🏆 SAMPLE COMPANIES:")
                sample_companies = combined_df[combined_df['name'].notna()]['name'].head(10)
                for i, name in enumerate(sample_companies, 1):
                    print(f"   {i:2d}. {name}")
            
            print(f"\n🎉 SUCCESS! All company lists and their contents extracted!")
            
        else:
            print("\n❌ No companies found in any lists")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    # Check if specific test is requested
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "context7":
            # Test only the Context7 method
            test_context7_only()
        elif test_type == "original":
            # Test only the original method
            print("🔄 TESTING ORIGINAL METHOD ONLY")
            print("=" * 50)
            company_lists = get_all_company_lists()
            if not company_lists.empty:
                display_company_lists_summary(company_lists)
            else:
                print("❌ No company lists found")
        else:
            print("❌ Invalid test type. Use 'context7' or 'original'")
            print("Usage: python simple_company_lists.py [context7|original]")
    else:
        # Run full test suite
        main() 