import requests
import json

# API URL
url = "https://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live"

# Payload for the request
payload = [{
    "bid": 999,
    "match": "exact",
    "keywords": ["roofers"],  # Replace with your desired keyword
    "location_code": 2840             # Example: US location code

}]

# Headers with Authorization and Content-Type
headers = {
    'Authorization': 'Basic aW5mb0BxdWFudHVtcmVhY2htYXJrZXRpbmcuY29tOjZhYWRhODIzYjczNjljZmE=',
    'Content-Type': 'application/json'
}

# Send the POST request
response = requests.post(url, json=payload, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=4))  # Pretty print the JSON response

    # Check if there is an error code or empty data
    if data.get('status_code') != 20000 or not data.get('tasks')[0].get('result'):
        print(f"Error or No Data Found: {data.get('status_message')}")
else:
    print(f"HTTP Error: {response.status_code}")
    print(response.text)  # Print error details
