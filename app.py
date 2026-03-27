import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="Confirmación de Asistencia", page_icon="💍", layout="centered")

# --- INITIALIZE SESSION STATE ---
if 'selected_guest_idx' not in st.session_state:
    st.session_state.selected_guest_idx = None

# --- CSS INJECTION ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500&family=Montserrat:wght@300;400&display=swap');

.stApp { background-color: #FCFBF9; }
.block-container { padding-top: 4rem; padding-bottom: 2rem; }

.pre-title {
    font-family: 'Montserrat', sans-serif; font-size: 0.75rem;
    letter-spacing: 0.3em; color: #9E9E9E; text-align: center; margin-bottom: -10px;
}

.main-title {
    font-family: 'Playfair Display', serif; font-size: 4.5rem; color: #2D2D2D;
    text-align: center; font-weight: 400; margin-top: 0; margin-bottom: 5px;
}

.custom-divider { display: flex; align-items: center; justify-content: center; margin-bottom: 40px; }
.custom-divider::before, .custom-divider::after { content: ""; height: 1px; background-color: #D3D3D3; width: 50px; }
.custom-divider .dot { height: 5px; width: 5px; background-color: #BDBDBD; border-radius: 50%; margin: 0 15px; }

/* Constrain and Center the Search Bar */
div[data-testid="stTextInput"] {
    max-width: 80%;
    margin: 0 auto;
}

div[data-baseweb="input"] { background-color: white; border-radius: 8px; border: 1px solid #6D5C4F; }

.error-text { font-family: 'Montserrat', sans-serif; color: #9E9E9E; text-align: center; font-size: 0.9rem; margin-top: 25px; }
.footer { font-family: 'Montserrat', sans-serif; color: #BDBDBD; text-align: center; font-size: 0.8rem; margin-top: 100px; padding-bottom: 20px; }

/* "SELECCIONA TU NOMBRE" text */
.select-name-title {
    font-family: 'Montserrat', sans-serif; font-size: 0.7rem; letter-spacing: 0.2em;
    color: #9E9E9E; text-align: center; margin-top: 40px; margin-bottom: 20px; text-transform: uppercase;
}

/* Ensure the button container allows full width */
div[data-testid="stButton"] {
    display: flex;
    justify-content: center;
    width: 100%;
}

/* Styling the clickable guest cards */
div[data-testid="stButton"] button {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 10px;
    padding: 15px 25px;
    margin-bottom: 5px;
    box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
    transition: border-color 0.3s ease;
}

div[data-testid="stButton"] button:hover {
    border-color: #6D5C4F;
    color: #2D2D2D;
}

/* Forces the text inside the wide button to align left */
div[data-testid="stButton"] button p {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    color: #4A4A4A;
    margin: 0;
    width: 100%;
    text-align: left; 
}
            
/* Styling the Confirm and Back Buttons */
div[data-testid="stFormSubmitButton"] button, 
.back-btn-container button {
    font-family: 'Montserrat', sans-serif;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- HTML HEADERS ---
st.markdown('<div class="pre-title">ESTÁS INVITADO</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Confirmación</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-divider"><div class="dot"></div></div>', unsafe_allow_html=True)

# --- MOCK DATA ---
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
df['FULL_NAME'] = df['NOMBRE'].astype(str).str.strip() + " " + df['APELLIDO'].astype(str).str.strip()


# ==========================================
# APP LOGIC
# ==========================================

if st.session_state.selected_guest_idx is None:
    
    search_term = st.text_input("Buscar", label_visibility="collapsed", placeholder="🔍 Ingresa tu nombre o apellido...")
    
    if search_term:
        match_condition = df['FULL_NAME'].str.lower().str.contains(search_term.lower().strip(), na=False)
        matches = df[match_condition]
        
        if not matches.empty:
            st.markdown('<div class="select-name-title">SELECCIONA TU NOMBRE</div>', unsafe_allow_html=True)
            
            for idx, row in matches.iterrows():
                if st.button(row['FULL_NAME'], key=f"btn_{idx}", use_container_width=True):
                    st.session_state.selected_guest_idx = idx
                    st.rerun()
        else:
            st.markdown('<div class="error-text">No se encontraron invitados con ese nombre.</div>', unsafe_allow_html=True)


else:
    if st.button("← Volver a buscar", key="back_btn", type="primary"):
        st.session_state.selected_guest_idx = None
        st.rerun()

    matched_idx = st.session_state.selected_guest_idx
    matched_row = df.loc[matched_idx]
    
    main_guest_name = matched_row['FULL_NAME']
    
    try:
        n = int(matched_row['NO_PERSONAS'])
    except ValueError:
        n = 0
        
    st.write("---")
    st.subheader(f"¡Hola, {main_guest_name}!")
    
    if n > 0:
        st.write("**Acompañantes en tu invitación:**")
        max_idx = min(matched_idx + n, len(df) - 1)
        
        for i in range(matched_idx + 1, max_idx + 1):
            companion_name = f"{df.loc[i, 'NOMBRE']} {df.loc[i, 'APELLIDO']}".strip()
            st.write(f"- {companion_name}")
            
    invitados_options = list(range(1, n + 2)) 
    veganos_options = list(range(0, n + 2))   
    
    with st.form("confirmation_form"):
        confirmados = st.selectbox("Invitados Confirmados", options=invitados_options)
        platillos_veganos = st.selectbox("Platillos veganos", options=veganos_options)
        
        submit = st.form_submit_button("Confirmar", type="primary")
        
        if submit:
            st.success("¡Tu confirmación ha sido guardada exitosamente!")
            st.balloons()

# Custom Footer
st.markdown('<div class="footer">Con amor, los novios ♥</div>', unsafe_allow_html=True)