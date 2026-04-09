# connectors/whatsapp.py
import requests
import json
import streamlit as st

def send_whatsapp_template(recipient_phone, template_name="hello_world", language_code="en_US"):
    """
    Sends a WhatsApp template message using the Meta Cloud API.
    """
    # Pull credentials securely from secrets.toml
    ACCESS_TOKEN = st.secrets["META_ACCESS_TOKEN"]
    PHONE_NUMBER_ID = st.secrets["META_PHONE_NUMBER_ID"]

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        # Return True if successful, False + error message if it failed
        if response.status_code == 200:
            return True, "Success"
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)