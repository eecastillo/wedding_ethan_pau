import streamlit as st
from supabase import create_client, Client
from streamlit_extras.let_it_rain import rain
from datetime import datetime, timezone, timedelta
import uuid

# Define your deadline: Year, Month, Day, Hour, Minute
DEADLINE = datetime(2026, 8, 26, 20, 56, 0)

def format_names_spanish(names):
    """Formats a list of names into a Spanish string: 'A, B y C' or 'A e Isabel'"""
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    
    last_name = names[-1]
    conjunction = "e" if last_name.lower().startswith(('i', 'hi')) and not last_name.lower().startswith(('hia', 'hie', 'hio', 'hiu')) else "y"
    
    return ", ".join(names[:-1]) + f" {conjunction} " + last_name

# Page Config
st.set_page_config(page_title="Confirmación de Asistencia", page_icon="💍", layout="centered")

# --- INITIALIZE SESSION STATE ---
if 'attendance_selection' not in st.session_state:
    st.session_state.attendance_selection = None

# --- CSS INJECTION (100% COMPATIBLE CON TODOS LOS NAVEGADORES) ---
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stAppDeployButton { display: none; }
[data-testid="stToolbar"] { visibility: hidden !important; }
.viewerBadge_container { display: none !important; }
.viewerBadge_link { display: none !important; }
            
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500&family=Montserrat:wght@300;400;500&display=swap');

.stApp { background-color: #FCFBF9 !important; }
.block-container { padding-top: 4rem; padding-bottom: 2rem; }

.pre-title { font-family: 'Montserrat', sans-serif; font-size: 0.75rem; letter-spacing: 0.3em; color: #9E9E9E; text-align: center; margin-bottom: -10px; }
.main-title { font-family: 'Playfair Display', serif; font-size: clamp(2.5rem, 12vw, 4.5rem); color: #2D2D2D; text-align: center; font-weight: 400; margin-top: 0; margin-bottom: 25px; }
.custom-divider { display: flex; align-items: center; justify-content: center; margin-bottom: 40px; }
.custom-divider::before, .custom-divider::after { content: ""; height: 1px; background-color: #D3D3D3; width: 50px; }
.custom-divider .dot { height: 5px; width: 5px; background-color: #BDBDBD; border-radius: 50%; margin: 0 15px; }
.error-text { font-family: 'Montserrat', sans-serif; color: #9E9E9E; text-align: center; font-size: 0.9rem; margin-top: 40px; line-height: 1.6; padding: 0 20px;}
.footer { font-family: 'Montserrat', sans-serif; color: #BDBDBD; text-align: center; font-size: 0.8rem; margin-top: 100px; padding-bottom: 20px; }

/* ========================================================= */
/* 1. TARJETA PRINCIPAL BLANCA (Estilo Base)                 */
/* ========================================================= */
div[data-testid="stVerticalBlockBorderWrapper"] { 
    background-color: #FFFFFF !important; 
    border: 1px solid #E2E2E2 !important; 
    border-radius: 15px !important; 
    padding: 40px 30px !important; 
    box-shadow: 0px 8px 25px rgba(0,0,0,0.06) !important; 
    max-width: 80% !important; 
    margin: 20px auto 0 auto !important; 
}

/* ========================================================= */
/* 2. TARJETAS BEIGE DE INVITADOS (Tarjetas Anidadas)        */
/* ========================================================= */
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #F0EAE1 !important;  /* Beige contrastante */
    border: 1px solid #DFD8CC !important; 
    border-radius: 12px !important; 
    padding: 20px 20px 5px 20px !important; 
    margin-top: 0px !important; 
    margin-bottom: 15px !important; 
    box-shadow: inset 0px 2px 4px rgba(0,0,0,0.02) !important; 
    max-width: 100% !important; /* Resetea el 80% heredado de la tarjeta padre */
}

/* Tipografía de nombres */
.guest-role { font-family: 'Montserrat', sans-serif; font-size: 0.65rem; letter-spacing: 0.25em; color: #9E9E9E; text-align: center; text-transform: uppercase; margin-bottom: 10px; margin-top: 10px; }
.guest-name-large { font-family: 'Playfair Display', serif; font-size: 2.2rem; color: #2D2D2D; text-align: center; margin-bottom: 30px; line-height: 1.2; }
.companion-container { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; }
.companion-pill { background-color: #F3EFE9; color: #4A4A4A; font-family: 'Playfair Display', serif; font-size: 1.1rem; padding: 8px 25px; border-radius: 12px; border: 1px solid #EAE5DE; }
.form-label { font-family: 'Montserrat', sans-serif; font-size: 0.85rem; color: #7D7D7D; margin-bottom: 5px; display: flex; align-items: center; gap: 8px; font-weight: 400; }

/* Botones */
div[data-testid="stButton"] button[kind="secondary"] { width: 100% !important; background-color: #FFFFFF !important; border: 1px solid #E0E0E0 !important; border-radius: 10px !important; padding: 18px 25px !important; margin-bottom: 5px !important; box-shadow: 0px 2px 4px rgba(0,0,0,0.02) !important; transition: border-color 0.3s ease !important; }
div[data-testid="stButton"] button[kind="secondary"]:hover { border-color: #6D5C4F !important; color: #2D2D2D !important; }
div[data-testid="stButton"] button[kind="secondary"] p { font-family: 'Playfair Display', serif !important; font-size: 1.25rem !important; color: #4A4A4A !important; margin: 0 !important; width: 100% !important; text-align: center !important; }
div[data-testid="stButton"] button[kind="primary"] { width: 100% !important; background-color: #A89F91 !important; color: white !important; border: 1px solid #A89F91 !important; border-radius: 10px !important; padding: 18px 25px !important; margin-bottom: 5px !important; font-family: 'Montserrat', sans-serif !important; transition: background-color 0.3s !important; box-shadow: 0px 2px 4px rgba(0,0,0,0.02) !important; }
div[data-testid="stButton"] button[kind="primary"]:hover { background-color: #8C847A !important; border-color: #8C847A !important; }
div[data-testid="stButton"] button[kind="primary"] p { color: white !important; font-weight: 500 !important; font-size: 1.25rem !important; margin: 0 !important; text-align: center !important; }
div[data-testid="stButton"] button[key^="submit_"] p { font-family: 'Montserrat', sans-serif !important; font-size: 1rem !important; }

/* Contraste en Inputs y Alertas */
div[data-testid="stCheckbox"] label p { color: #4A4A4A !important; font-family: 'Montserrat', sans-serif !important; font-size: 1.05rem !important; }
div[data-testid="stAlert"] p { color: #4A4A4A !important; font-family: 'Montserrat', sans-serif !important; font-weight: 500 !important; }
input[type="text"] { color: #4A4A4A !important; background-color: #FFFFFF !important; border: 1px solid #EAEAEA !important; }
input[type="text"]::placeholder { color: #9E9E9E !important; opacity: 1 !important; }
div[data-testid="stTextInput"] label p { font-family: 'Montserrat', sans-serif !important; font-size: 0.85rem !important; color: #7D7D7D !important; font-weight: 400 !important; }

/* ========================================================= */
/* 3. ESTILOS DE CHECKBOX (CHECKBOX PERSONALIZADO INFALIBLE) */
/* ========================================================= */

/* 1. Esconder la cajita roja y negra nativa de Streamlit por completo */
div[data-testid="stCheckbox"] label > div:not(:has([data-testid="stMarkdownContainer"])),
div[data-testid="stCheckbox"] label > span {
    display: none !important;
}

div[data-testid="stCheckbox"] input[type="checkbox"] {
    position: absolute !important;
    opacity: 0 !important; /* Mantiene la funcionalidad de click, pero invisible */
}

/* 2. Alinear el contenedor de texto para preparar nuestro propio checkbox */
div[data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] {
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
}
div[data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important; /* Quita espacios extra alrededor del texto */
}

/* 3. DIBUJAR NUESTRO PROPIO CHECKBOX (Estado: NO seleccionado) */
div[data-testid="stCheckbox"] label:has(input[type="checkbox"]:not(:checked)) div[data-testid="stMarkdownContainer"]::before {
    content: "";
    display: block;
    width: 20px;
    height: 20px;
    background-color: #FFFFFF;
    border: 2px solid #000000;
    border-radius: 4px;
    margin-right: 12px;
    flex-shrink: 0;
    transition: all 0.2s ease;
}

/* 4. DIBUJAR NUESTRO PROPIO CHECKBOX (Estado: SÍ seleccionado) */
div[data-testid="stCheckbox"] label:has(input[type="checkbox"]:checked) div[data-testid="stMarkdownContainer"]::before {
    content: "✓";
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    background-color: #4CAF50;
    border: 2px solid #000000;
    border-radius: 4px;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 16px;
    margin-right: 12px;
    flex-shrink: 0;
    transition: all 0.2s ease;
}
</style>
""", unsafe_allow_html=True)

# --- SVGS FOR LABELS ---
svg_people = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7D7D7D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
svg_leaf = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7D7D7D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path></svg>'

# --- HTML HEADERS ---
st.markdown('<div class="pre-title">ESTÁS INVITADO</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Confirmación</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-divider"><div class="dot"></div></div>', unsafe_allow_html=True)

# --- REVISED COUNTDOWN LOGIC ---
now = datetime.now()
diff = DEADLINE - now

if diff.total_seconds() <= 0:
    st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <div style="color: #A89F91; font-family: 'Playfair Display', serif; font-size: 1.2rem;">
                El tiempo para confirmar ha terminado.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()
else:
    seconds_left = int(diff.total_seconds())
    days = seconds_left // 86400
    hours = (seconds_left % 86400) // 3600
    minutes = (seconds_left % 3600) // 60
    st.markdown(f"""
        <div style="text-align: center; font-family: 'Montserrat', sans-serif; margin-bottom: 30px; padding: 15px; border-radius: 12px; background-color: #F9F8F6; border: 1px solid #F1EFEF;">
            <div style="color: #9E9E9E; letter-spacing: 0.2em; font-size: 0.65rem; text-transform: uppercase; margin-bottom: 8px;">
                Límite para confirmar
            </div>
            <div style="color: #4A4A4A; font-size: 1.2rem; font-weight: 400; letter-spacing: 0.05em;">
                {days}d <span style="color: #A89F91;">•</span> {hours}h <span style="color: #A89F91;">•</span> {minutes}m
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- REAL DATA ---
#scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
#creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
#client = gspread.authorize(creds)
#sheet = client.open("invitados").sheet1
#
#@st.cache_data(ttl=600) 
#def load_data():
#    data = sheet.get_all_records()
#    return pd.DataFrame(data)

#df = load_data()
#df['FULL_NAME'] = df['NOMBRE(S)'].astype(str).str.strip() + " " + df['APELLIDO(S)'].astype(str).str.strip()

# ==========================================
# APP LOGIC - ROUTING BY URL PARAMETER
# ==========================================

# --- 1. INITIALIZATION & SECRETS ---
# Assuming supabase client is already initialized as 'supabase'
target_event_id = st.secrets["app_config"]["ACTIVE_EVENT_ID"]


query_params = st.query_params
guest_url_token = query_params.get("id")

def is_valid_uuid(val):
    """Strictly checks if the provided string is a valid UUID v4."""
    try:
        # If it's not a valid UUID format, this throws a ValueError
        uuid_obj = uuid.UUID(str(val), version=4)
        return str(uuid_obj) == str(val)
    except ValueError:
        return False

# If there is no ID, or if someone tried to type "?id=CAXH6" or "?id=DROP TABLE guests"
if not guest_url_token or not is_valid_uuid(guest_url_token):
    st.markdown('<div class="error-text">¡Hola! Para confirmar tu asistencia, por favor utiliza el enlace personalizado que te enviamos por mensaje. 🤍</div>', unsafe_allow_html=True)
    st.stop() # Halts all execution. The database is never touched.


# --- SUPABASE INITIALIZATION ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- FETCH FROM SUPABASE ---
@st.cache_data(ttl=60)
def fetch_party_for_event(party_uuid, event_uuid):
    try:
        # Strict dual-filtering: Must match the URL's party AND the Secret's event
        response = supabase.table("guests") \
            .select("*") \
            .eq("party_id", party_uuid) \
            .eq("event_id", event_uuid) \
            .order("is_party_lead", desc=True) \
            .execute()
            
        return response.data
    except Exception as e:
        return None

party_data = fetch_party_for_event(guest_url_token, target_event_id)

if not party_data:
    st.markdown('<div class="error-text">No pudimos encontrar tu invitación. Por favor verifica que el enlace sea correcto o comunícate con nosotros.</div>', unsafe_allow_html=True)
    st.stop()

# --- PREPARE ALL PARTY MEMBERS ---
# Find the lead guest (assuming you have a boolean column 'is_party_lead')
lead_guest = next((g for g in party_data if g.get('is_party_lead')), party_data[0])
main_guest_name = f"{lead_guest['first_name']} {lead_guest['last_name']}".strip()

party_members = []
companion_names = []

for person in party_data:
    full_name = f"{person['first_name']} {person['last_name']}".strip()
    # We store the unique database 'id' instead of the DataFrame index
    party_members.append({"name": full_name, "db_id": person["guest_id"], "rsvp_status": person.get("rsvp_status", "")})
    
    if person["guest_id"] != lead_guest["guest_id"]:
        companion_names.append(full_name)

# --- NUEVA LÓGICA: EVALUAR A TODA LA FAMILIA ---
confirmed_names = []
canceled_names = []

for member in party_members:
    status = str(member["rsvp_status"]).strip()
    if "confirmed" in status:
        confirmed_names.append(member["name"])
    elif "canceled" in status:
        canceled_names.append(member["name"])

# CASO 1: Si al menos UNA persona va a asistir
if len(confirmed_names) > 0:
    with st.container(border=True):
        st.markdown(f'<div class="guest-name-large">¡Hola, {main_guest_name}!</div>', unsafe_allow_html=True)
        st.markdown('<div class="custom-divider"><div class="dot"></div></div>', unsafe_allow_html=True)
        
        # Mensaje dinámico dependiendo de si el invitado principal asiste o no
        if main_guest_name in confirmed_names:
            if len(confirmed_names) == 1:
                msg = "Tu asistencia ya ha sido confirmada."
            else:
                others = [name for name in confirmed_names if name != main_guest_name]
                names_str = format_names_spanish(others)
                msg = f"Tu asistencia y la de {names_str} ya ha sido confirmada."
        else:
            names_str = format_names_spanish(confirmed_names)
            msg = f"Hemos recibido la respuesta. La asistencia de {names_str} ya ha sido confirmada."

        # Pequeño mensaje para mencionar a los que no asisten (Buen toque de UX)
        # Pequeño mensaje para mencionar a los que no asisten (Buen toque de UX)
        cancel_msg = ""
        if len(canceled_names) > 0:
            if main_guest_name in canceled_names:
                if len(canceled_names) == 1:
                    # Solo canceló el invitado principal
                    cancel_msg = "<br><br><span style='font-size: 0.95rem;'><i>Lamentamos mucho que tú no puedas acompañarnos, pero nos alegra que los demás sí asistan.</i></span>"
                else:
                    # Canceló el invitado principal Y alguien más
                    others_canceled = [name for name in canceled_names if name != main_guest_name]
                    cancel_str = format_names_spanish(others_canceled)
                    cancel_msg = f"<br><br><span style='font-size: 0.95rem;'><i>Lamentamos mucho que tú y {cancel_str} no puedan acompañarnos, pero nos alegra que los demás sí asistan.</i></span>"
            else:
                # El invitado principal asiste, pero otros cancelaron
                # El invitado principal asiste, pero otros cancelaron
                cancel_str = format_names_spanish(canceled_names)
                pueda_verb = "puedan" if len(canceled_names) > 1 else "pueda"
                cancel_msg = f"<br><br><span style='font-size: 0.95rem;'><i>Lamentamos que {cancel_str} no {pueda_verb} acompañarnos.</i></span>"
        st.markdown(f"""
            <div class="error-text" style="color: #4A4A4A; font-size: 1.2rem; font-family: 'Playfair Display', serif;">
                {msg}
                {cancel_msg}<br><br>
                <b>¡Gracias por confirmar! ✨</b><br>
                Estamos muy emocionados y nos encantará compartir este día tan especial.
            </div>
        """, unsafe_allow_html=True)

# CASO 2: Si TODOS cancelaron
elif len(canceled_names) == len(party_members) and len(party_members) > 0:
    with st.container(border=True):
        st.markdown(f'<div class="guest-name-large">¡Hola, {main_guest_name}!</div>', unsafe_allow_html=True)
        st.markdown('<div class="custom-divider"><div class="dot"></div></div>', unsafe_allow_html=True)
        
        if len(party_members) > 1:
            others = [m["name"] for m in party_members if m["name"] != main_guest_name]
            names_str = format_names_spanish(others)
            msg = f"Hemos recibido tu respuesta y la de {names_str}."
            # Plural: La familia no puede ir, pero "tú" nos avisaste
            lamento_msg = "Lamentamos mucho que no puedan acompañarnos, pero agradecemos sinceramente que nos lo hicieras saber."
        else:
            msg = "Hemos recibido tu respuesta."
            # Singular: Tú no puedes ir y tú nos avisaste
            lamento_msg = "Lamentamos mucho que no puedas acompañarnos, pero agradecemos sinceramente que nos lo hicieras saber."

        st.markdown(f"""
            <div class="error-text" style="color: #4A4A4A; font-size: 1.1rem; font-family: 'Playfair Display', serif;">
                {msg}<br><br>
                <b>Gracias por avisarnos. 🤍</b><br>
                {lamento_msg}
            </div>
        """, unsafe_allow_html=True)

# CASO 3: Nadie ha respondido aún -> Mostrar el formulario
else:
    with st.container(border=True):
        # (Aquí debe quedarse el resto de tu código que pinta los botones y checkboxes)
        st.markdown('<div class="guest-role">INVITADO PRINCIPAL</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="guest-name-large">{main_guest_name}</div>', unsafe_allow_html=True)

        n = len(party_members)
        
        if n > 1:
            st.markdown('<div class="guest-role">ACOMPAÑANTES</div>', unsafe_allow_html=True)
            pills_html = '<div class="companion-container">'
            for name in companion_names:
                pills_html += f'<div class="companion-pill">{name}</div>'
            pills_html += '</div>'
            st.markdown(pills_html, unsafe_allow_html=True)
            
        st.markdown('<div class="custom-divider" style="margin-bottom: 25px;"><div class="dot"></div></div>', unsafe_allow_html=True)

        # 1. Define dynamic display text based on guest count (n)
        question_text = "¿Podrán acompañarnos?" if n > 1 else "¿Podrás acompañarnos?"
        yes_label = "✓ Sí, continuar" if n > 1 else "✓ Sí, continuar"
        no_label = "✗ No podremos" if n > 1 else "✗ No podré"

        # 2. Keep the state variables static so you don't break your downstream 'if' statements
        yes_state_val = "Sí, confirmamos"
        no_state_val = "No, lamentablemente no podremos"

        # 3. Render the dynamic markdown question
        st.markdown(f'<div class="form-label" style="justify-content: center; font-size: 1.1rem; margin-bottom: 20px; font-weight: 500; color: #4A4A4A;">{question_text}</div>', unsafe_allow_html=True)

        def set_attendance(status):
            st.session_state.attendance_selection = status

        _, col1, col2, _ = st.columns([1, 4, 4, 1])

        # 4. Render the buttons with dynamic labels but static args
        with col1:
            is_yes = st.session_state.attendance_selection == yes_state_val
            st.button(
                yes_label, 
                type="primary" if is_yes else "secondary", 
                key="btn_yes", 
                on_click=set_attendance, 
                args=(yes_state_val,), 
                use_container_width=True
            )

        with col2:
            is_no = st.session_state.attendance_selection == no_state_val
            st.button(
                no_label, 
                type="primary" if is_no else "secondary", 
                key="btn_no", 
                on_click=set_attendance, 
                args=(no_state_val,), 
                use_container_width=True
            )

        attendance = st.session_state.attendance_selection
        
        if attendance == "Sí, confirmamos":
            st.write("") 
            st.markdown(f'<div class="form-label" style="font-size: 1.15rem; margin-top: 15px; margin-bottom: 15px;">{svg_people} Confirma asistencia y restricciones por persona:</div>', unsafe_allow_html=True)                    
            # --- DYNAMIC PER-PERSON UI LOOP ---
            attendance_results = {}
            vegan_results = {}
            allergy_results = {}
            
            for member in party_members:
                chk_key = f"chk_{member['db_id']}"
                
                if chk_key not in st.session_state:
                    st.session_state[chk_key] = False
                    
                is_going_state = st.session_state[chk_key]
                
                with st.container(border=True): 
                    label = f"**{member['name']}**"                            
                    is_going = st.checkbox(label, key=chk_key)
                    attendance_results[member["db_id"]] = is_going
                    
                    if is_going:
                        st.write("") # Small visual gap
                        col_v, col_a = st.columns([1, 1.5]) 
                        with col_v:
                            vegan_results[member["db_id"]] = st.checkbox("🌱 Deseo menú vegano", key=f"veg_{member['db_id']}")
                        with col_a:
                            allergy_results[member["db_id"]] = st.text_input(
                                "Alergias o Restricciones Alimenticias", 
                                placeholder="Ej: Nueces, mariscos, gluten...", 
                                key=f"alg_{member['db_id']}"
                            )
                    else:
                        vegan_results[member["db_id"]] = False
                        allergy_results[member["db_id"]] = ""

            st.write("") 
            
            # Confirmados sigue siendo necesario para habilitar/deshabilitar el botón de submit
            confirmados = sum(attendance_results.values())

            # --- SUBMISSION LOGIC ---
            if confirmados == 0:
                st.warning("⚠️ Debes seleccionar al menos a un invitado. Si nadie asistirá, por favor cambia tu respuesta principal a 'No podremos'.")
            
            submit = st.button(
                "✓ Confirmar mi asistencia", 
                key="submit_yes", 
                use_container_width=True, 
                type="primary",
                disabled=(confirmados == 0)
            )
            
            if submit:
                if datetime.now() >= DEADLINE:
                    st.error("Lo sentimos, el tiempo para confirmar ha expirado.")
                    st.stop()
                else:
                    # GUARDADO INDIVIDUAL: Update via Supabase API
                    for member in party_members:
                        db_id = member["db_id"]
                        
                        is_going = attendance_results.get(db_id, False)
                        is_vegan = vegan_results.get(db_id, False)
                        allergy_text = allergy_results.get(db_id, "").strip()
                        
                        update_payload = {
                            "rsvp_status": "confirmed" if is_going else "canceled",
                            #"confirmacion": 1 if is_going else 0,
                            "is_vegan": (is_going and is_vegan),
                            "dietary_comments": f"Alergias: {allergy_text}" if (is_going and allergy_text) else ""
                        }
                        
                        # Push update to Supabase
                        supabase.table("guests").update(update_payload).eq("guest_id", db_id).execute()

                    fetch_party.clear() # Clear the cache to reflect updates
                    st.success("¡Tu confirmación ha sido guardada exitosamente!")
                    rain(emoji="🕊️", font_size=40, falling_speed=5, animation_length=2)
                    
        elif attendance == "No, lamentablemente no podremos":
            st.write("") 
            submit_cancel = st.button("✗ Confirmar mi cancelación", key="submit_no", use_container_width=True, type="primary")
            
            if submit_cancel:
                if datetime.now() >= DEADLINE:
                    st.error("Lo sentimos, el tiempo para confirmar ha expirado.")
                    st.stop()
                else:
                    # CANCELACIÓN INDIVIDUAL: Update via Supabase API
                    for member in party_members:
                        db_id = member["db_id"]
                        
                        update_payload = {
                            "rsvp_status": "canceled",
                            #"confirmacion": 0,
                            "is_vegan": False,
                            "dietary_comments": ""
                        }
                        
                        supabase.table("guests").update(update_payload).eq("guest_id", db_id).execute()
                    
                    fetch_party.clear() # Clear the cache to reflect updates
                    st.info("Gracias por informarnos. Lamentamos que no puedan asistir.")

# Custom Footer
st.markdown('<div class="footer">Con amor, los novios ♥</div>', unsafe_allow_html=True)