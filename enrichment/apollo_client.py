import requests

url = "https://api.apollo.io/api/v1/mixed_people/search?person_titles[]=&person_titles[]=&person_titles[]=&person_titles[]=&person_titles[]=&person_locations[]=&person_locations[]=&person_seniorities[]=&person_seniorities[]=&q_organization_domains_list[]="

headers = {
    "accept": "application/json",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json"
}

payload = {
    "q_organization_names": [company_name],
    "person_titles": [job_title],
    "person_locations": [location],
    "page": 1,
    "per_page": 5
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)

if __name__ == "__main__":
    companies = get_companies_from_hubspot(limit=5)
    print(f"Entreprises trouvées dans HubSpot: {companies}")

    job_filter = "HR Director"
    location_filter = "London"

    for company in companies:
        people = search_people_on_apollo(company, job_filter, location_filter)
        print(f"\n👤 Résultats pour {company}:")
        for person in people:
            name = person.get('name')
            email = person.get('email')
            title = person.get('title')
            print(f"- {name}, {title}, {email}")