import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Page Config
st.set_page_config(page_title="Confirmación de Asistencia", page_icon="💍")
st.title("Confirmación de Invitados")

# Google Sheets Setup
#scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
#creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
#client = gspread.authorize(creds)

# Open the Sheet (Replace with your actual file name)
#sheet = client.open("Wedding_RSVP_List").sheet1
#data = sheet.get_all_records()
#df = pd.DataFrame(data)

# Create a concatenated full name column for flexible searching
#df['FULL_NAME'] = df['NOMBRE'].astype(str).str.strip() + " " + df['APELLIDO'].astype(str).str.strip()

# Search Box
search_term = st.text_input("Ingresa tu nombre para buscar tu invitación:")
