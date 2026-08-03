import requests
import streamlit as st

def send_whatsapp_template(recipient_phone, template_name, language_code="en", components=None):
    ACCESS_TOKEN = st.secrets["META_ACCESS_TOKEN"]
    PHONE_NUMBER_ID = st.secrets["META_PHONE_NUMBER_ID"]

    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
        # 'Content-Type' is handled automatically by the json= parameter
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

    if components:
        payload["template"]["components"] = components

    try:
        # Using json=payload is the most robust way to send this
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return True, "Success"
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)