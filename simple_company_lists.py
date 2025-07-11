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

def main():
    """Main function"""
    try:
        # Get all company lists
        company_lists = get_all_company_lists()
        
        if company_lists.empty:
            print("\n❌ No company lists found")
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
    main() 