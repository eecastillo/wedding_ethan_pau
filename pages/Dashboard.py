import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import altair as alt
import json
import os
from datetime import datetime
from connectors.whatsapp import send_whatsapp_template

# --- 1. AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<h2 style="text-align:center; font-family:Playfair Display;">Acceso Restringido</h2>', unsafe_allow_html=True)
    pw = st.text_input("Ingresa la contraseña de Administrador", type="password")
    if st.button("Entrar"):
        if pw == st.secrets["admin_password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# --- 2. CONFIG & SCHEDULER STORAGE ---
st.set_page_config(page_title="Host Dashboard", page_icon="📊", layout="centered")

SCHEDULE_FILE = "blast_schedule.json"

def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Default fallback dates if file is missing or corrupt
    return [
        {"Date": "2026-03-20 10:00", "Status": "ENVIADO"},
        {"Date": "2026-04-25 10:00", "Status": "AGENDADO"},
        {"Date": "2026-05-05 10:00", "Status": "AGENDADO"}
    ]

def save_schedule(new_dates):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(new_dates, f)

# --- 3. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500&family=Montserrat:wght@300;400;500&display=swap');
    .host-header { font-family: 'Montserrat', sans-serif; font-size: 0.8rem; letter-spacing: 0.3em; color: #9E9E9E; text-align: center; text-transform: uppercase; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3.5rem; color: #2D2D2D; text-align: center; margin-top: -10px; margin-bottom: 30px; }
    .metric-container { text-align: center; padding: 10px; }
    .metric-value { font-family: 'Playfair Display', serif; font-size: 2.5rem; color: #2D2D2D; margin-bottom: 0px; }
    .metric-label { font-family: 'Montserrat', sans-serif; font-size: 0.7rem; letter-spacing: 0.1em; color: #9E9E9E; text-transform: uppercase; }
    .sent-badge { background-color: #E8F4F0; color: #4F8C78; padding: 4px 12px; border-radius: 15px; font-size: 0.7rem; font-weight: 500; }
    .scheduled-badge { background-color: #F9F8F6; color: #9E9E9E; padding: 4px 12px; border-radius: 15px; font-size: 0.7rem; font-weight: 500; border: 1px solid #EAEAEA; }
</style>
""", unsafe_allow_html=True)

# --- 4. DATA LOADING ---
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("invitados").sheet1

@st.cache_data(ttl=60)
def get_data():
    return pd.DataFrame(sheet.get_all_records())

df = get_data()
df['# DE PERSONAS'] = pd.to_numeric(df['# DE PERSONAS'], errors='coerce').fillna(0)

# --- 5. METRICS & CHART ---
st.markdown('<div class="host-header">HOST DASHBOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Overview</div>', unsafe_allow_html=True)

confirmed_count = int(df[df['ESTATUS'].str.contains("Confirmado", na=False)]['# DE PERSONAS'].sum())
declined_count = int(df[df['ESTATUS'].str.contains("Cancelado", na=False)]['# DE PERSONAS'].sum())
pending_count = int(df[~df['ESTATUS'].str.contains("Confirmado|Cancelado", na=False)]['# DE PERSONAS'].sum())

m1, m2, m3 = st.columns(3)
m1.markdown(f'<div class="metric-container"><div class="metric-value">{confirmed_count}</div><div class="metric-label">Confirmados</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-container"><div class="metric-value">{declined_count}</div><div class="metric-label">Cancelados</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-container"><div class="metric-value">{pending_count}</div><div class="metric-label">Pendientes</div></div>', unsafe_allow_html=True)

chart_data = pd.DataFrame({
    'Estado': ['Confirmados', 'Cancelados', 'Pendientes'],
    'Personas': [confirmed_count, declined_count, pending_count]
})
color_scale = alt.Scale(domain=['Confirmados', 'Cancelados', 'Pendientes'], range=['#4F8C78', '#BC8F8F', '#D3D3D3'])

base_chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
    x=alt.X('Estado:N', sort=None, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=11, labelColor='#9E9E9E')),
    y=alt.Y('Personas:Q', title=None, axis=alt.Axis(grid=False, labels=False)),
    color=alt.Color('Estado:N', scale=color_scale, legend=None),
    tooltip=['Estado', 'Personas']
).properties(height=250).configure_view(strokeOpacity=0).configure_axis(domain=False)

st.altair_chart(base_chart, use_container_width=True)

# ==========================================
# GESTIÓN DE ENVÍOS (DASHBOARD SECTION)
# ==========================================

# 1. Initialize session state for editing
if "editing_row" not in st.session_state:
    st.session_state.editing_row = None

st.markdown('<div style="text-align:center; color:#9E9E9E; font-size:0.7rem; letter-spacing:0.2em; margin-top:50px;">ENVIO DE INVITACIONES AGENDADAS</div>', unsafe_allow_html=True)

# 2. Load the current schedule from your JSON file
display_data = load_schedule()

# 3. Iterate and build the rows
for i, item in enumerate(display_data):
    dt_obj = datetime.strptime(item["Date"], "%Y-%m-%d %H:%M")
    
    # Columns for: Icon, Date Text, Status
    c_btn, c_date, c_status = st.columns([0.5, 3, 1])
    
    with c_btn:
        # Toggle edit mode for this specific row
        if st.button("✏️", key=f"edit_btn_{i}"):
            st.session_state.editing_row = i
            st.rerun()

    with c_date:
        if st.session_state.editing_row == i:
            # --- EDIT MODE ---
            new_date = st.date_input("Nueva fecha", value=dt_obj.date(), key=f"picker_{i}", label_visibility="collapsed")
            col_save, col_cancel = st.columns(2)
            
            if col_save.button("💾", key=f"save_{i}"):
                # Update logic: keep original time, update date
                new_full_dt = datetime.combine(new_date, dt_obj.time())
                new_status = "ENVIADO" if new_full_dt < datetime.now() else "AGENDADO"
                
                # Overwrite and save
                display_data[i] = {
                    "Date": new_full_dt.strftime("%Y-%m-%d %H:%M"),
                    "Status": new_status
                }
                save_schedule(display_data)
                st.session_state.editing_row = None
                st.rerun()
                
            if col_cancel.button("❌", key=f"cancel_{i}"):
                st.session_state.editing_row = None
                st.rerun()
        else:
            # --- DISPLAY MODE ---
            display_str = dt_obj.strftime("%d de %B, %Y")
            st.markdown(f'<div style="font-family:Playfair Display; font-size:1.1rem; color:#4A4A4A; padding:5px 0;">{display_str}</div>', unsafe_allow_html=True)

    with c_status:
        badge = "sent-badge" if item["Status"] == "ENVIADO" else "scheduled-badge"
        st.markdown(f'<div style="padding:10px 0;"><span class="{badge}">{item["Status"]}</span></div>', unsafe_allow_html=True)
    
    st.divider()

# --- 8. ACTIONS ---
st.write("")
template_url = st.secrets["template_drive_url"]
st.markdown(f'<a href="{template_url}" target="_blank" style="text-decoration: none;"><div style="text-align: center; border: 1px solid #EAEAEA; border-radius: 15px; padding: 15px; color: #4A4A4A; font-family: Playfair Display; font-size: 1.2rem;">📥 Descargar plantilla de invitados</div></a>', unsafe_allow_html=True)

st.write("")
if st.button("🚀 Prueba de Envío (WhatsApp)", type="primary", use_container_width=True):
    success, error_msg = send_whatsapp_template(recipient_phone="523118765918")
    if success:
        st.toast("✅ Mensaje enviado correctamente")
    else:
        st.error(f"❌ Error: {error_msg}")