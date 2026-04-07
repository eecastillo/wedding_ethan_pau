import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import altair as alt

# 1. AUTHENTICATION / PASSWORD CHECK
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
    st.stop() # Stops the page right here if not authenticated

# --- PAGE SETUP (Only runs if authenticated) ---
st.set_page_config(page_title="Host Dashboard", page_icon="📊", layout="centered")

# CSS (Keeping the elegant look from your images)
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

# DATA LOADING
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("invitados").sheet1

def get_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = get_data()

# This converts the column to numbers. Any text or empty cells become 'NaN' (0)
df['# DE PERSONAS'] = pd.to_numeric(df['# DE PERSONAS'], errors='coerce').fillna(0)

# HEADER
st.markdown('<div class="host-header">HOST DASHBOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Overview</div>', unsafe_allow_html=True)

# --- GUEST STATUS (TOTAL SUM OF PEOPLE) ---
# Filter dataframes for counts
confirmed_df = df[df['ESTATUS'].str.contains("Confirmado", na=False)]
declined_df = df[df['ESTATUS'].str.contains("Cancelado", na=False)]

# SUM OF PEOPLE (Assuming column is exactly '# DE PERSONAS')
confirmed_count = confirmed_df['# DE PERSONAS'].sum()
declined_count = declined_df['# DE PERSONAS'].sum()
pending_count = df[~df['ESTATUS'].str.contains("Confirmado|Cancelado", na=False)]['# DE PERSONAS'].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-container"><div class="metric-value">{confirmed_count}</div><div class="metric-label">Confirmed</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-container"><div class="metric-value">{declined_count}</div><div class="metric-label">Declined</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-container"><div class="metric-value">{pending_count}</div><div class="metric-label">Pending</div></div>', unsafe_allow_html=True)

# 1. Create the data for the chart
chart_data = pd.DataFrame({
    'Estado': ['Confirmados', 'Cancelados', 'Pendientes'],
    'Personas': [confirmed_count, declined_count, pending_count]
})

# 2. Define the Color Scale
color_scale = alt.Scale(
    domain=['Confirmados', 'Cancelados', 'Pendientes'],
    range=['#4F8C78', '#BC8F8F', '#D3D3D3'] # Green, Rose, Grey
)

# 3. Build the Stylized Chart
base_chart = alt.Chart(chart_data).mark_bar(
    cornerRadiusTopLeft=8, 
    cornerRadiusTopRight=8
).encode(
    x=alt.X('Estado:N', sort=None, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=11, labelColor='#9E9E9E')),
    y=alt.Y('Personas:Q', title=None, axis=alt.Axis(grid=False, labels=False)), # Hiding Y axis for a cleaner look
    color=alt.Color('Estado:N', scale=color_scale, legend=None), # <--- APPLY COLORS HERE
    tooltip=['Estado', 'Personas']
).properties(
    height=250
).configure_view(
    strokeOpacity=0
).configure_axis(
    domain=False
)

# 4. Display the finished product
st.altair_chart(base_chart, use_container_width=True)

# --- SCHEDULED TABLE (Manual for now) ---
st.markdown('<div style="text-align:center; color:#9E9E9E; font-size:0.7rem; letter-spacing:0.2em; margin-top:50px;">SCHEDULED CONFIRMATIONS SENTS</div>', unsafe_allow_html=True)
scheduled_data = [
    {"Date": "March 20, 2026", "Status": "SENT"},
    {"Date": "April 25, 2026", "Status": "SCHEDULED"},
    {"Date": "May 05, 2026", "Status": "SCHEDULED"},
]

for item in scheduled_data:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f'<div style="font-family:Playfair Display; font-size:1.2rem; color:#4A4A4A; padding:10px 0;">{item["Date"]}</div>', unsafe_allow_html=True)
    with c2:
        badge = "sent-badge" if item["Status"] == "SENT" else "scheduled-badge"
        st.markdown(f'<div style="padding:15px 0;"><span class="{badge}">{item["Status"]}</span></div>', unsafe_allow_html=True)
    st.divider()

# --- DOWNLOAD TEMPLATE BUTTON ---
st.write("")
template_url = st.secrets["template_drive_url"]
st.markdown(f"""
    <a href="{template_url}" target="_blank" style="text-decoration: none;">
        <div style="text-align: center; border: 1px solid #EAEAEA; border-radius: 15px; padding: 15px; color: #4A4A4A; font-family: Playfair Display; font-size: 1.2rem;">
            📥 Download Guestlist Template
        </div>
    </a>
""", unsafe_allow_html=True)