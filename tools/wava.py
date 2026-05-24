import requests

access_token = "PASTE_YOUR_ACCESS_TOKEN_HERE"
waba_id = "PASTE_YOUR_WABA_ID_HERE" # Make sure this is the WABA ID, not the Phone Number ID!

url = f"https://graph.facebook.com/v25.0/{waba_id}/subscribed_apps"

headers = {
    "Authorization": f"Bearer {access_token}"
}

print("Re-wiring Meta Webhook Routing...")
response = requests.post(url, headers=headers)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")