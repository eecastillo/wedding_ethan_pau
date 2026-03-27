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


# Mock data simulating sheet.get_all_records()
data = [
    # Group 1: Couple (Main Guest + 1 Companion -> NO_PERSONAS = 1)
    {
        "NOMBRE": "Carlos", "APELLIDO": "García", "NO_PERSONAS": 1, 
        "CELULAR": "5551234567", "ESTATUS": "Pendiente_de_Confirmar", 
        "PERSONAS_CONFIRMADAS": 0, "PLATILLOS_VEGANOS": 0, "COMENTARIOS": "", "NO_MESA": 1
    },
    {
        "NOMBRE": "María", "APELLIDO": "López", "NO_PERSONAS": 0, 
        "CELULAR": "", "ESTATUS": "", 
        "PERSONAS_CONFIRMADAS": 0, "PLATILLOS_VEGANOS": 0, "COMENTARIOS": "", "NO_MESA": 1
    },
    
    # Group 2: Family (Main Guest + 2 Companions -> NO_PERSONAS = 2)
    {
        "NOMBRE": "Roberto", "APELLIDO": "Martínez", "NO_PERSONAS": 2, 
        "CELULAR": "5559876543", "ESTATUS": "Mensaje_enviado", 
        "PERSONAS_CONFIRMADAS": 0, "PLATILLOS_VEGANOS": 0, "COMENTARIOS": "", "NO_MESA": 2
    },
    {
        "NOMBRE": "Ana", "APELLIDO": "Martínez", "NO_PERSONAS": 0, 
        "CELULAR": "", "ESTATUS": "", 
        "PERSONAS_CONFIRMADAS": 0, "PLATILLOS_VEGANOS": 0, "COMENTARIOS": "", "NO_MESA": 2
    },
    {
        "NOMBRE": "Luis", "APELLIDO": "Martínez", "NO_PERSONAS": 0, 
        "CELULAR": "", "ESTATUS": "", 
        "PERSONAS_CONFIRMADAS": 0, "PLATILLOS_VEGANOS": 0, "COMENTARIOS": "", "NO_MESA": 2
    },
    
    # Group 3: Single Guest (Main Guest + 0 Companions -> NO_PERSONAS = 0)
    {
        "NOMBRE": "Sofia", "APELLIDO": "Ramírez", "NO_PERSONAS": 0, 
        "CELULAR": "5556667777", "ESTATUS": "Pendiente_de_Confirmar", 
        "PERSONAS_CONFIRMADAS": 0, "PLATILLOS_VEGANOS": 0, "COMENTARIOS": "", "NO_MESA": 3
    }
]

df = pd.DataFrame(data)

# Create a concatenated full name column for flexible searching
df['FULL_NAME'] = df['NOMBRE'].astype(str).str.strip() + " " + df['APELLIDO'].astype(str).str.strip()

# Search Box
search_term = st.text_input("Ingresa tu nombre para buscar tu invitación:")

if search_term:
    # Partial, case-insensitive match
    match_condition = df['FULL_NAME'].str.lower().str.contains(search_term.lower().strip(), na=False)
    matches = df[match_condition]
    
    if not matches.empty:
        # Get the index and data of the first matched row
        matched_idx = matches.index[0]
        matched_row = matches.iloc[0]
        
        main_guest_name = matched_row['FULL_NAME']
        
        # Read NO_PERSONAS, default to 0 if empty
        try:
            n = int(matched_row['NO_PERSONAS'])
        except ValueError:
            n = 0
            
        st.write("---")
        st.subheader(f"Invitado Principal: {main_guest_name}")
        
        # If N > 0, print the labels for the following N rows
        if n > 0:
            st.write("**Acompañantes en esta invitación:**")
            # Calculate the boundary to avoid index errors at the end of the sheet
            max_idx = min(matched_idx + n, len(df) - 1)
            
            for i in range(matched_idx + 1, max_idx + 1):
                companion_name = f"{df.loc[i, 'NOMBRE']} {df.loc[i, 'APELLIDO']}".strip()
                st.write(f"- {companion_name}")
                
        # Dropdown options
        invitados_options = list(range(1, n + 2)) # Goes from 1 to 1+N
        veganos_options = list(range(0, n + 2))   # Goes from 0 to 1+N
        
        with st.form("confirmation_form"):
            confirmados = st.selectbox("Invitados Confirmados", options=invitados_options)
            platillos_veganos = st.selectbox("Platillos veganos", options=veganos_options)
            
            submit = st.form_submit_button("Confirmar")
            
            if submit:
                # Row index in Google Sheets is matched_idx + 2 
                # (+1 because pandas is 0-indexed, +1 because Sheets has a header row)
                gsheet_row = int(matched_idx) + 2
                
                # Column mapping based on your structure (1-indexed for gspread):
                # Col 5 = ESTATUS
                # Col 6 = PERSONAS_CONFIRMADAS
                # Col 7 = PLATILLOS_VEGANOS
                
                #sheet.update_cell(gsheet_row, 5, "Confirmado_web")
                #sheet.update_cell(gsheet_row, 6, confirmados)
                #sheet.update_cell(gsheet_row, 7, platillos_veganos)
                
                st.success("¡Tu confirmación ha sido guardada exitosamente!")
                st.balloons()
    else:
        st.error("No encontramos una invitación con ese nombre. Por favor intenta de nuevo.")