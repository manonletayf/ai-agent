import requests

url = "https://api.apollo.io/api/v1/people/match?reveal_personal_emails=true&reveal_phone_number=true"

headers = {
    "accept": "application/json",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)

print(response.text)