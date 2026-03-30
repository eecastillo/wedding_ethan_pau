import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_extras.let_it_rain import rain

# Page Config
st.set_page_config(page_title="Confirmación de Asistencia", page_icon="💍", layout="centered")

# --- INITIALIZE SESSION STATE ---
if 'selected_guest_idx' not in st.session_state:
    st.session_state.selected_guest_idx = None
if 'attendance_selection' not in st.session_state:
    st.session_state.attendance_selection = None

def clear_selection():
    """Clears the selection and goes back to the list if the search box is modified"""
    st.session_state.selected_guest_idx = None
    st.session_state.attendance_selection = None

# --- CSS INJECTION ---
st.markdown("""
<style>

            
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500&family=Montserrat:wght@300;400;500&display=swap');

.stApp { background-color: #FCFBF9; }
.block-container { padding-top: 4rem; padding-bottom: 2rem; }

.pre-title {
    font-family: 'Montserrat', sans-serif; font-size: 0.75rem;
    letter-spacing: 0.3em; color: #9E9E9E; text-align: center; margin-bottom: -10px;
}

.main-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.5rem, 12vw, 4.5rem); 
    color: #2D2D2D; text-align: center; font-weight: 400; margin-top: 0; margin-bottom: 25px;
}

.custom-divider { display: flex; align-items: center; justify-content: center; margin-bottom: 40px; }
.custom-divider::before, .custom-divider::after { content: ""; height: 1px; background-color: #D3D3D3; width: 50px; }
.custom-divider .dot { height: 5px; width: 5px; background-color: #BDBDBD; border-radius: 50%; margin: 0 15px; }

div[data-testid="stTextInput"] { max-width: 80%; margin: 0 auto; }
div[data-baseweb="input"] { background-color: white; border-radius: 8px; border: 1px solid #E0E0E0; }

.error-text { font-family: 'Montserrat', sans-serif; color: #9E9E9E; text-align: center; font-size: 0.9rem; margin-top: 25px; }
.footer { font-family: 'Montserrat', sans-serif; color: #BDBDBD; text-align: center; font-size: 0.8rem; margin-top: 100px; padding-bottom: 20px; }

/* "SELECCIONA TU NOMBRE" text */
.select-name-title {
    font-family: 'Montserrat', sans-serif; font-size: 0.7rem; letter-spacing: 0.2em;
    color: #9E9E9E; text-align: center; margin-top: 40px; margin-bottom: 20px; text-transform: uppercase;
}

/* Guest Cards (Search Results) */
div[data-testid="stButton"] { display: flex; justify-content: center; width: 100%; }
div[data-testid="stButton"] button[kind="secondary"] {
    width: 100%; background-color: #FFFFFF; border: 1px solid #E0E0E0;
    border-radius: 10px; padding: 18px 25px; margin-bottom: 5px;
    box-shadow: 0px 2px 4px rgba(0,0,0,0.02); transition: border-color 0.3s ease;
}
div[data-testid="stButton"] button[kind="secondary"]:hover { border-color: #6D5C4F; color: #2D2D2D; }
div[data-testid="stButton"] button[kind="secondary"] p {
    font-family: 'Playfair Display', serif; font-size: 1.25rem; color: #4A4A4A; margin: 0; width: 100%; text-align: left;
}

/* --- THE MAIN CONTAINER CARD STYLING --- */
/* Replaces the old stForm targeting */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF;
    border: 1px solid #EAEAEA;
    border-radius: 15px;
    padding: 40px 30px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.03);
    max-width: 80%;
    margin: 20px auto 0 auto; 
}

.guest-role {
    font-family: 'Montserrat', sans-serif; font-size: 0.65rem; letter-spacing: 0.25em;
    color: #9E9E9E; text-align: center; text-transform: uppercase; margin-bottom: 10px; margin-top: 10px;
}

.guest-name-large {
    font-family: 'Playfair Display', serif; font-size: 2.2rem; color: #2D2D2D;
    text-align: center; margin-bottom: 30px; line-height: 1.2;
}

.companion-container {
    display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin-bottom: 30px;
}

.companion-pill {
    background-color: #F3EFE9; color: #4A4A4A; font-family: 'Playfair Display', serif;
    font-size: 1.1rem; padding: 8px 25px; border-radius: 12px; border: 1px solid #EAE5DE;
}

/* Input Labels with SVG Icons */
.form-label {
    font-family: 'Montserrat', sans-serif; font-size: 0.85rem; color: #7D7D7D;
    margin-bottom: 5px; display: flex; align-items: center; gap: 8px; font-weight: 400;
}

/* Style for the active/selected buttons (Primary) */
div[data-testid="stButton"] button[kind="primary"] {
    width: 100% !important;
    background-color: #A89F91 !important;
    color: white !important;
    border: 1px solid #A89F91 !important; /* 1px border to match the secondary button */
    border-radius: 10px !important;
    padding: 18px 25px !important; /* Exactly matches the secondary button padding */
    margin-bottom: 5px !important; /* Exactly matches the secondary button margin */
    font-family: 'Montserrat', sans-serif !important;
    transition: background-color 0.3s;
    box-shadow: 0px 2px 4px rgba(0,0,0,0.02) !important;
}

div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #8C847A !important;
    border-color: #8C847A !important;
}

div[data-testid="stButton"] button[kind="primary"] p { 
    color: white !important; 
    font-weight: 500 !important; 
    font-size: 1.25rem !important; /* Matches the text size of the secondary button */
}
</style>
""", unsafe_allow_html=True)

# --- SVGS FOR LABELS ---
svg_people = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7D7D7D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
svg_leaf = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7D7D7D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path></svg>'

# --- HTML HEADERS ---
st.markdown('<div class="pre-title">ESTÁS INVITADO</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Confirmación</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-divider"><div class="dot"></div></div>', unsafe_allow_html=True)

# --- REAL DATA ---
# Google Sheets Setup
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("invitados").sheet1

# --- THE MAGIC CACHE ---
@st.cache_data(ttl=600) 
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()
df['FULL_NAME'] = df['NOMBRE(S)'].astype(str).str.strip() + " " + df['APELLIDO(S)'].astype(str).str.strip()

# ==========================================
# APP LOGIC
# ==========================================

# Search bar is always visible.
search_term = st.text_input(
    "Buscar", 
    label_visibility="collapsed", 
    placeholder="🔍 Ingresa tu nombre o apellido...", 
    on_change=clear_selection
)

if search_term and st.session_state.selected_guest_idx is None:
    df['# DE PERSONAS'] = pd.to_numeric(df['# DE PERSONAS'], errors='coerce').fillna(0)
    
    match_condition = (
        df['FULL_NAME'].str.lower().str.contains(search_term.lower().strip(), na=False) & 
        (df['# DE PERSONAS'] > 0)
    )
    matches = df[match_condition]
    
    if not matches.empty:
        st.markdown('<div class="select-name-title">SELECCIONA TU NOMBRE</div>', unsafe_allow_html=True)
        for idx, row in matches.iterrows():
            if st.button(row['FULL_NAME'], key=f"btn_{idx}", use_container_width=True):
                st.session_state.selected_guest_idx = idx
                st.session_state.attendance_selection = None
                st.rerun()
    else:
        st.markdown('<div class="error-text">No se encontraron invitados con ese nombre.</div>', unsafe_allow_html=True)

# THE MAIN CONTAINER CARD
elif st.session_state.selected_guest_idx is not None:
    matched_idx = st.session_state.selected_guest_idx
    matched_row = df.loc[matched_idx]
    main_guest_name = matched_row['FULL_NAME']
    
    try:
        n = int(matched_row['# DE PERSONAS'])
    except ValueError:
        n = 0
        
    invitados_options = list(range(1, n + 1)) 
    veganos_options = list(range(0, n + 1))   
    
    # Using a styled container instead of a restrictive form
    with st.container(border=True):
        # 1. Main Guest Info
        st.markdown('<div class="guest-role">INVITADO PRINCIPAL</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="guest-name-large">{main_guest_name}</div>', unsafe_allow_html=True)
        
        # 2. Companions logic
        if n > 1:
            st.markdown('<div class="guest-role">ACOMPAÑANTES</div>', unsafe_allow_html=True)
            max_idx = min(matched_idx + n-1, len(df) - 1)
            
            pills_html = '<div class="companion-container">'
            for i in range(matched_idx + 1, max_idx + 1):
                companion_name = f"{df.loc[i, 'NOMBRE(S)']} {df.loc[i, 'APELLIDO(S)']}".strip()
                pills_html += f'<div class="companion-pill">{companion_name}</div>'
            pills_html += '</div>'
            st.markdown(pills_html, unsafe_allow_html=True)
            
        # 3. Inner Divider
        st.markdown('<div class="custom-divider" style="margin-bottom: 25px;"><div class="dot"></div></div>', unsafe_allow_html=True)

        # 4. Attendance Question
        st.markdown('<div class="form-label" style="justify-content: center; font-size: 1.1rem; margin-bottom: 20px; font-weight: 500; color: #4A4A4A;">¿Podrán acompañarnos?</div>', unsafe_allow_html=True)

        # Callback to save the button click to session state
        def set_attendance(status):
            st.session_state.attendance_selection = status

        # Use empty outer columns to push the buttons to the center
        _, col1, col2, _ = st.columns([1, 4, 4, 1])

        with col1:
            is_yes = st.session_state.attendance_selection == "Sí, confirmamos"
            st.button(
                "✓ Sí, confirmamos",
                type="primary" if is_yes else "secondary",
                key="btn_yes",
                on_click=set_attendance,
                args=("Sí, confirmamos",),
                use_container_width=True
            )

        with col2:
            is_no = st.session_state.attendance_selection == "No, lamentablemente no podremos"
            st.button(
                "✗ No podremos",
                type="primary" if is_no else "secondary",
                key="btn_no",
                on_click=set_attendance,
                args=("No, lamentablemente no podremos",),
                use_container_width=True
            )

        attendance = st.session_state.attendance_selection
        
        # 5. Conditional Inputs
        confirmados = None
        platillos_veganos = None
        
        if attendance == "Sí, confirmamos":
            st.write("") 
            st.write("") 
            st.markdown(f'<div class="form-label">{svg_people} Invitados Confirmados</div>', unsafe_allow_html=True)
            confirmados = st.selectbox(
                "Invitados Confirmados", 
                options=invitados_options, 
                index=None, 
                placeholder="Seleccionar cantidad", 
                label_visibility="collapsed"
            )
            
            st.markdown(f'<div class="form-label">{svg_leaf} Platillos veganos</div>', unsafe_allow_html=True)
            platillos_veganos = st.selectbox(
                "Platillos veganos", 
                options=veganos_options, 
                index=None, 
                placeholder="Seleccionar cantidad", 
                label_visibility="collapsed"
            )

            st.write("") 
            
            # 6. Styled Confirm Button (Standard button triggers update)
            submit = st.button("✓ Confirmar mi asistencia", use_container_width=True, type="primary")
            
            if submit:
                gsheet_row = int(matched_idx) + 2
                
                if confirmados is None:
                    st.error("Por favor selecciona el número de invitados.")
                elif platillos_veganos is not None and platillos_veganos > confirmados:
                    st.error(f"Solo confirmaste {confirmados} asistente(s). El número de platillos veganos no puede ser mayor.")
                else:
                    # Update Google Sheets
                    sheet.update_cell(gsheet_row, 5, "Confirmado_web")
                    sheet.update_cell(gsheet_row, 6, confirmados)
                    sheet.update_cell(gsheet_row, 7, platillos_veganos)
                    
                    load_data.clear()
                    st.success("¡Tu confirmación ha sido guardada exitosamente!")
                    rain(emoji="🕊️", font_size=40, falling_speed=5, animation_length=2)
                    
        elif attendance == "No, lamentablemente no podremos":
            st.write("") 
            st.write("") 
            submit_cancel = st.button("✗ Confirmar mi cancelación", use_container_width=True, type="primary")
            
            if submit_cancel:
                gsheet_row = int(matched_idx) + 2
                sheet.update_cell(gsheet_row, 5, "Cancelado_web")
                sheet.update_cell(gsheet_row, 6, 0)
                sheet.update_cell(gsheet_row, 7, 0)
                
                load_data.clear()
                st.info("Gracias por informarnos. Lamentamos que no puedan asistir.")

# Custom Footer
st.markdown('<div class="footer">Con amor, los novios ♥</div>', unsafe_allow_html=True)