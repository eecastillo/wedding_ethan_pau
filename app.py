import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_extras.let_it_rain import rain

# Page Config
st.set_page_config(page_title="Confirmación de Asistencia", page_icon="💍", layout="centered")

# --- INITIALIZE SESSION STATE ---
# We no longer need selected_guest_idx because the URL handles the routing!
if 'attendance_selection' not in st.session_state:
    st.session_state.attendance_selection = None

# --- CSS INJECTION ---
st.markdown("""
<style>
/* --- HIDE STREAMLIT DEFAULT UI --- */
[data-testid="stHeader"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stAppDeployButton { display: none; }
            
/* --- HIDE STREAMLIT CLOUD UI ELEMENTS --- */
[data-testid="stToolbar"] { visibility: hidden !important; }
.viewerBadge_container { display: none !important; }
.viewerBadge_link { display: none !important; }
            
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

.error-text { font-family: 'Montserrat', sans-serif; color: #9E9E9E; text-align: center; font-size: 0.9rem; margin-top: 40px; line-height: 1.6; padding: 0 20px;}
.footer { font-family: 'Montserrat', sans-serif; color: #BDBDBD; text-align: center; font-size: 0.8rem; margin-top: 100px; padding-bottom: 20px; }

/* --- THE MAIN CONTAINER CARD STYLING --- */
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

/* Style for the secondary buttons (Unclicked) */
div[data-testid="stButton"] button[kind="secondary"] {
    width: 100% !important; background-color: #FFFFFF !important; border: 1px solid #E0E0E0 !important;
    border-radius: 10px !important; padding: 18px 25px !important; margin-bottom: 5px !important;
    box-shadow: 0px 2px 4px rgba(0,0,0,0.02) !important; transition: border-color 0.3s ease !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover { border-color: #6D5C4F !important; color: #2D2D2D !important; }
div[data-testid="stButton"] button[kind="secondary"] p {
    font-family: 'Playfair Display', serif !important; font-size: 1.25rem !important; color: #4A4A4A !important; margin: 0 !important; width: 100% !important; text-align: center !important;
}

/* Style for the active/selected buttons (Primary) - Fixed Height! */
div[data-testid="stButton"] button[kind="primary"] {
    width: 100% !important; background-color: #A89F91 !important; color: white !important;
    border: 1px solid #A89F91 !important; border-radius: 10px !important;
    padding: 18px 25px !important; margin-bottom: 5px !important;
    font-family: 'Montserrat', sans-serif !important; transition: background-color 0.3s !important;
    box-shadow: 0px 2px 4px rgba(0,0,0,0.02) !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover { background-color: #8C847A !important; border-color: #8C847A !important; }
div[data-testid="stButton"] button[kind="primary"] p { 
    color: white !important; font-weight: 500 !important; font-size: 1.25rem !important; margin: 0 !important; text-align: center !important;
}

/* Specific fix for the submit buttons to match primary style but use Montserrat */
div[data-testid="stButton"] button[key^="submit_"] p {
    font-family: 'Montserrat', sans-serif !important;
    font-size: 1rem !important;
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
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("invitados").sheet1

@st.cache_data(ttl=600) 
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()
df['FULL_NAME'] = df['NOMBRE(S)'].astype(str).str.strip() + " " + df['APELLIDO(S)'].astype(str).str.strip()

# ==========================================
# APP LOGIC - ROUTING BY URL PARAMETER
# ==========================================

# 1. Get the ID from the URL (e.g., ?id=FAM-001)
query_params = st.query_params
guest_id = query_params.get("id")

if not guest_id:
    # No ID in the URL. Show a polite message.
    st.markdown('<div class="error-text">¡Hola! Para confirmar tu asistencia, por favor utiliza el enlace personalizado que te enviamos por mensaje. 🤍</div>', unsafe_allow_html=True)

else:
    # 2. Check if the ID exists in the DataFrame
    if 'ID_UNICO' not in df.columns:
        st.error("Error: La columna 'ID_UNICO' no existe en Google Sheets.")
        st.stop()
        
    # Cast both to string to ensure a perfect match even if IDs look like numbers
    match_condition = df['ID_UNICO'].astype(str) == str(guest_id)
    matches = df[match_condition]
    
    if matches.empty:
        # The ID is in the URL, but it doesn't match anyone in the database
        st.markdown('<div class="error-text">No pudimos encontrar tu invitación. Por favor verifica que el enlace sea correcto o comunícate con nosotros.</div>', unsafe_allow_html=True)
        
    else:
        # 3. We have a match! Load their specific data.
        matched_idx = matches.index[0]
        matched_row = matches.iloc[0]
        main_guest_name = matched_row['FULL_NAME']
        
        # --- NEW: CHECK ESTATUS COLUMN ---
        # We check if the guest has already responded
        current_status = str(matched_row.get('ESTATUS', '')).strip()

        if "Confirmado" in current_status:
            with st.container(border=True):
                st.markdown(f'<div class="guest-name-large" style="margin-bottom:10px;">¡Hola, {main_guest_name}!</div>', unsafe_allow_html=True)
                st.markdown('<div class="custom-divider"><div class="dot"></div></div>', unsafe_allow_html=True)
                st.markdown("""
                    <div class="error-text" style="color: #4A4A4A; font-size: 1.2rem; font-family: 'Playfair Display', serif;">
                        Tu asistencia ya ha sido confirmada.<br><br>
                        <b>¡Gracias por confirmar! ✨</b><br>
                        Estamos muy emocionados y nos encantará compartir este día tan especial contigo.
                    </div>
                """, unsafe_allow_html=True)
                st.write("") # Spacer

        elif "Cancelado" in current_status:
            with st.container(border=True):
                st.markdown(f'<div class="guest-name-large" style="margin-bottom:10px;">¡Hola, {main_guest_name}!</div>', unsafe_allow_html=True)
                st.markdown('<div class="custom-divider"><div class="dot"></div></div>', unsafe_allow_html=True)
                st.markdown("""
                    <div class="error-text" style="color: #4A4A4A; font-size: 1.1rem; font-family: 'Playfair Display', serif;">
                        Hemos recibido tu respuesta.<br><br>
                        <b>Gracias por avisarnos. 🤍</b><br>
                        Lamentamos mucho que no puedan acompañarnos, pero agradecemos sinceramente que nos lo hicieras saber. ¡Esperamos vernos pronto en otra ocasión!
                    </div>
                """, unsafe_allow_html=True)
                st.write("") # Spacer

        else:
            # --- SHOW THE ORIGINAL RSVP FORM ---
            try:
                n = int(matched_row['# DE PERSONAS'])
            except ValueError:
                n = 0
                
            invitados_options = list(range(1, n + 1)) 
            veganos_options = list(range(0, n + 1))   
            
            # Using a styled container
            with st.container(border=True):
                # Main Guest Info
                st.markdown('<div class="guest-role">INVITADO PRINCIPAL</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="guest-name-large">{main_guest_name}</div>', unsafe_allow_html=True)
                
                # Companions logic
                if n > 1:
                    st.markdown('<div class="guest-role">ACOMPAÑANTES</div>', unsafe_allow_html=True)
                    max_idx = min(matched_idx + n-1, len(df) - 1)
                    
                    pills_html = '<div class="companion-container">'
                    for i in range(matched_idx + 1, max_idx + 1):
                        companion_name = f"{df.loc[i, 'NOMBRE(S)']} {df.loc[i, 'APELLIDO(S)']}".strip()
                        pills_html += f'<div class="companion-pill">{companion_name}</div>'
                    pills_html += '</div>'
                    st.markdown(pills_html, unsafe_allow_html=True)
                    
                # Inner Divider
                st.markdown('<div class="custom-divider" style="margin-bottom: 25px;"><div class="dot"></div></div>', unsafe_allow_html=True)

                # Attendance Question
                st.markdown('<div class="form-label" style="justify-content: center; font-size: 1.1rem; margin-bottom: 20px; font-weight: 500; color: #4A4A4A;">¿Podrán acompañarnos?</div>', unsafe_allow_html=True)

                def set_attendance(status):
                    st.session_state.attendance_selection = status

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
                
                # Conditional Inputs
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
                    
                    submit = st.button("✓ Confirmar mi asistencia", key="submit_yes", use_container_width=True, type="primary")
                    
                    if submit:
                        # Plus 2 because matched_idx is 0-indexed and Google Sheets has a header row
                        gsheet_row = int(matched_idx) + 2 
                        
                        if confirmados is None:
                            st.error("Por favor selecciona el número de invitados.")
                        elif platillos_veganos is not None and platillos_veganos > confirmados:
                            st.error(f"Solo confirmaste {confirmados} asistente(s). El número de platillos veganos no puede ser mayor.")
                        else:
                            sheet.update_cell(gsheet_row, 5, "Confirmado_web")
                            sheet.update_cell(gsheet_row, 6, confirmados)
                            sheet.update_cell(gsheet_row, 7, platillos_veganos)
                            
                            load_data.clear()
                            st.success("¡Tu confirmación ha sido guardada exitosamente!")
                            rain(emoji="🕊️", font_size=40, falling_speed=5, animation_length=2)
                            
                elif attendance == "No, lamentablemente no podremos":
                    st.write("") 
                    st.write("") 
                    submit_cancel = st.button("✗ Confirmar mi cancelación", key="submit_no", use_container_width=True, type="primary")
                    
                    if submit_cancel:
                        gsheet_row = int(matched_idx) + 2
                        sheet.update_cell(gsheet_row, 5, "Cancelado_web")
                        sheet.update_cell(gsheet_row, 6, 0)
                        sheet.update_cell(gsheet_row, 7, 0)
                        
                        load_data.clear()
                        st.info("Gracias por informarnos. Lamentamos que no puedan asistir.")

# Custom Footer
st.markdown('<div class="footer">Con amor, los novios ♥</div>', unsafe_allow_html=True)