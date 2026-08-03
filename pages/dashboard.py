import uuid
import io
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import altair as alt
import json
import os
from datetime import datetime
from connectors.whatsapp import send_whatsapp_template
from supabase import create_client, Client


# --- DIALOG DEFINITION ---
@st.dialog("¿Actualizar Estatus RSVP?")
def confirm_swap_dialog(target_id, payload):
    st.markdown("""
    **Has modificado los datos de este invitado.** 
    
    Si estás reasignando este lugar a una nueva persona, ¿cómo deseas registrar su estatus de asistencia?
    """)
    
    col1, col2 = st.columns(2)
    
    if col1.button("⏳ Dejar en Pendiente", use_container_width=True):
        payload["rsvp_status"] = "pending"
        execute_db_update(target_id, payload)
        
    if col2.button("✅ Marcar como Confirmado", type="primary", use_container_width=True):
        payload["rsvp_status"] = "confirmed"
        execute_db_update(target_id, payload)

def execute_db_update(target_id, payload):
    try:
        supabase.table("guests").update(payload).eq("guest_id", str(target_id)).execute()
        st.success("✅ Datos actualizados correctamente.")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Error al actualizar la base de datos: {e}")


# --- 1. SUPABASE INITIALIZATION ---
#@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 2. AUTHENTICATION (SUPABASE) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.authenticated:
    st.markdown('<h2 style="text-align:center; font-family:Playfair Display;">Acceso Restringido</h2>', unsafe_allow_html=True)
    
    email = st.text_input("Correo electrónico del Planner")
    pw = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        try:
            # Authenticate directly via Supabase Auth
            response = supabase.auth.sign_in_with_password({"email": email, "password": pw})
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        except Exception as e:
            st.error("Credenciales incorrectas o usuario no encontrado.")
            
    st.stop() # Halts rendering of the dashboard if not logged in

# --- 3. SESSION MANAGEMENT (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"**Usuario:** {st.session_state.user.email}")
    if st.button("Cerrar Sesión"):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

# --- 4. CONFIG & SCHEDULER STORAGE ---
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

# --- 4. DATA LOADING & EVENT SELECTION (SUPABASE) ---

# Fetch the events belonging to the logged-in planner
@st.cache_data(ttl=60)
def get_planner_events(planner_uuid):
    response = supabase.table("events").select("event_id, event_name, event_date").eq("planner_id", planner_uuid).execute()
    return response.data

# Fetch the guests strictly for the selected event
@st.cache_data(ttl=60)
def get_event_guests(event_uuid):
    response = supabase.table("guests").select("*").eq("event_id", event_uuid).execute()
    # We load it into a Pandas DataFrame to keep your Altair charting logic intact
    return pd.DataFrame(response.data)


st.markdown('<div class="host-header">HOST DASHBOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Overview</div>', unsafe_allow_html=True)

# Require the user to be logged in
if "user" in st.session_state and st.session_state.user:
    planner_id = st.session_state.user.id
    
    # Get the planner's events
    events_list = get_planner_events(planner_id)
    if not events_list:
        st.warning("No tienes eventos registrados aún. Crea uno para comenzar.")
        st.stop()
        
    # Create a mapping dictionary: "Event Name (Date)" -> "event_id"
    event_options = {f"{ev['event_name']} ({ev['event_date']})": ev['event_id'] for ev in events_list}
    
    # The Dropdown UI
    selected_event_label = st.selectbox("Selecciona un Evento para visualizar:", list(event_options.keys()))
    selected_event_id = event_options[selected_event_label]
    
    # Fetch the guest list for the chosen event
    df = get_event_guests(selected_event_id)

    # --- 1. FILE INGESTION ---
    st.markdown('<div class="host-header">📥 IMPORTACIÓN DE INVITADOS</div>', unsafe_allow_html=True)
    st.write("Asegúrate de utilizar la plantilla oficial. Las columnas requeridas son: **Nombre, Apellido, Número de Personas, Teléfono de Contacto**")

    uploaded_file = st.file_uploader("Sube tu lista de invitados (CSV o Excel)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            # Parse the file based on its extension
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
                
            # Strict Column Validation
            required_cols = ["NOMBRE(S)", "APELLIDO(S)", "# DE PERSONAS", "CONTACTO: CELULAR"]
            missing_cols = [col for col in required_cols if col not in df_upload.columns]
            
            if missing_cols:
                st.error(f"❌ Error: Faltan las siguientes columnas en tu archivo: {', '.join(missing_cols)}")
            else:
                # --- 2. STAGING & REVIEW ---
                st.info("💡 Revisa los datos. Puedes editar las celdas directamente o desmarcar la casilla 'Importar' para ignorar una fila.")
                
                # Add a control column for the planner to select rows
                df_upload.insert(0, "Importar", True)
                
                # Render the interactive data editor
                edited_df = st.data_editor(
                    df_upload,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Importar": st.column_config.CheckboxColumn(
                            "Importar",
                            help="Selecciona las filas que deseas subir a la base de datos",
                            default=True,
                        )
                    }
                )
                
                # --- 3. EXECUTION & DATABASE INSERTION ---
                if st.button("🚀 Confirmar y Subir a Supabase", type="primary"):
                    with st.spinner('Procesando invitados y generando enlaces seguros...'):
                        
                        # Filter down to only the rows marked for import
                        final_df = edited_df[edited_df["Importar"] == True].copy()
                        
                        if final_df.empty:
                            st.warning("⚠️ No hay filas seleccionadas para importar.")
                            st.stop()

                        # Initialize a fallback UUID just in case the planner's very first row is malformed
                        current_party_id = str(uuid.uuid4())
                        records_to_insert = []
                        
                        for index, row in final_df.iterrows():
    
                            # 1. Evaluate the trigger signal: Is there a value in '# DE PERSONAS'?
                            raw_personas = row.get("# DE PERSONAS")
                            
                            # We use pd.notna() to safely handle NaN/Null values from Excel, 
                            # and check that it's not just an empty string or zero.
                            is_lead = False
                            party_size = None

                            if pd.notna(raw_personas) and str(raw_personas).strip() != "" and str(raw_personas).strip() != "0":
                                is_lead = True
                                try:
                                    # Excel often imports integers as floats ('4.0'). 
                                    # Casting to float first, then int, safely normalizes it to '4'.
                                    party_size = int(float(raw_personas))
                                except ValueError:
                                    # Fallback in case a planner typed a string like "Cuatro" by accident
                                    party_size = None
                                
                            # 2. State Transition: If this row is a lead, generate a fresh UUID for the new group
                            if is_lead:
                                current_party_id = str(uuid.uuid4())
                            # If is_lead is False, current_party_id remains unchanged, inheriting the ID from the row above
                            
                            # 3. Safely extract and clean the phone number
                            raw_phone = row.get("CONTACTO: CELULAR")

                            # Check if the value is a Pandas NaN, a string "nan", or just empty space
                            if pd.isna(raw_phone) or str(raw_phone).strip().lower() == "nan" or str(raw_phone).strip() == "":
                                final_phone = None
                            else:
                                # It's a real number. Clean the formatting.
                                clean_phone = str(raw_phone).replace(" ", "").replace("+", "").replace("-", "").replace(".0", "").strip()
                                
                                # One final check to ensure we don't pass an empty string
                                final_phone = clean_phone if clean_phone else None
                            # 4. Map to the strict Supabase schema
                            record = {
                                "event_id": selected_event_id, 
                                "party_id": current_party_id, # Uses the newly generated ID, or the inherited one
                                "first_name": str(row.get("NOMBRE(S)", "")).strip(),
                                "last_name": str(row.get("APELLIDO(S)", "")).strip(),
                                "party_size": party_size,
                                "phone_number": final_phone,
                                "is_party_lead": is_lead, # Strictly mapped to our boolean evaluation
                                "rsvp_status": "pending", 
                                "is_vegan": 0,
                                "dietary_comments": ""
                            }
                            records_to_insert.append(record)
                        
                        # Bulk Insert via Supabase
                        try:
                            # Passing a list of dictionaries executes a single bulk INSERT query
                            response = supabase.table("guests").insert(records_to_insert).execute()
                            
                            st.success(f"¡Éxito! Se han cargado {len(records_to_insert)} invitados al evento.")
                            st.balloons()
                            
                            # Clear the cache so metrics and charts update instantly
                            st.cache_data.clear()
                            # 2. INSTANT UI UPDATE: Force the page to run from the top again
                            st.rerun()
                        except Exception as e:
                            # Catch constraint violations (e.g., duplicate phone numbers within the same event)
                            st.error(f"❌ Error al subir a la base de datos: {e}")
                            
        except Exception as e:
            st.error(f"❌ No se pudo procesar el archivo. Verifica que no esté corrupto. Detalle: {e}")


    # --- ASSUMING df CONTAINS THE GUESTS FOR THE SELECTED EVENT ---
    # Ensure this is placed after your database fetch where 'df' is defined.

    st.divider()
    st.markdown('<div class="host-header">⚙️ GESTIÓN DE INVITADOS</div>', unsafe_allow_html=True)

    if not df.empty:
        # Check if the Supabase primary key 'guest_id' exists in the dataframe
        if 'guest_id' not in df.columns:
            st.error("Error de arquitectura: La tabla debe incluir la columna de clave primaria 'guest_id'.")
        else:
            # Create a clean tabbed interface for the two scenarios
            tab_add, tab_edit = st.tabs(["➕ Añadir Acompañante a Grupo", "✏️ Reasignar / Editar Invitado"])

            # ==========================================
            # SCENARIO 1: ADD TO EXISTING PARTY
            # ==========================================
            with tab_add:
                st.write("Selecciona al titular del grupo para añadirle un nuevo acompañante. No requiere número de teléfono.")
                
                # Filter only leads to represent the "Party"
                leads_df = df[df['is_party_lead'] == True]
                
                # Create a user-friendly dictionary mapping the visual name to the hidden party_id
                lead_options = {
                    f"{row.get('first_name', '')} {row.get('last_name', '')}": row['party_id'] 
                    for _, row in leads_df.iterrows()
                }
                
                selected_lead_label = st.selectbox(
                    "Familia / Titular del Grupo:", 
                    options=list(lead_options.keys()), 
                    key="add_guest_select"
                )
                
                with st.form("form_add_companion"):
                    new_first = st.text_input("Nombre(s) del Acompañante")
                    new_last = st.text_input("Apellido(s) del Acompañante")
                    
                    if st.form_submit_button("Añadir Acompañante", type="primary"):
                        if new_first and new_last:
                            target_party_id = lead_options[selected_lead_label]
                            
                            # Build the dependent record matching your schema
                            new_record = {
                                "event_id": selected_event_id,
                                "party_id": target_party_id,
                                "first_name": new_first.strip(),
                                "last_name": new_last.strip(),
                                "phone_number": None, # Dependents bypass the phone requirement
                                "is_party_lead": False,
                                "party_size": None,
                                "rsvp_status": "pending",
                                "is_vegan": 0,
                                "dietary_comments": ""
                            }
                            
                            try:
                                # 1. Insert the new guest
                                supabase.table("guests").insert(new_record).execute()
                                
                                # 2. Update the Lead's party_size metric by +1
                                lead_row = leads_df[leads_df['party_id'] == target_party_id].iloc[0]
                                if pd.notna(lead_row.get('party_size')):
                                    new_size = int(lead_row['party_size']) + 1
                                    supabase.table("guests").update({"party_size": new_size}) \
                                        .eq("party_id", target_party_id) \
                                        .eq("is_party_lead", True).execute()
                                    
                                st.success(f"✅ {new_first} añadido correctamente al grupo.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al añadir a la base de datos: {e}")
                        else:
                            st.warning("⚠️ Por favor, ingresa el nombre y apellido.")

            # ==========================================
            # SCENARIO 2: SWAP/EDIT GUEST
            # ==========================================
            with tab_edit:
                st.write("Modifica los datos de un invitado (Ej: Cambio de nombre si alguien cede su lugar).")
                
                # Create a dictionary for ALL guests mapping their visual name to their unique database row ID
                guest_options = {}
                for _, row in df.iterrows():
                    role = "Titular" if row.get("is_party_lead") else "Acompañante"
                    label = f"{row.get('first_name', '')} {row.get('last_name', '')} ({role})"
                    guest_options[label] = row['guest_id']
                    
                selected_guest_label = st.selectbox(
                    "Selecciona al invitado a modificar:", 
                    options=list(guest_options.keys()), 
                    key="edit_guest_select"
                )
                
                if selected_guest_label:
                    target_guest_id = guest_options[selected_guest_label]
                    current_guest_data = df[df['guest_id'] == target_guest_id].iloc[0]
                    
                    with st.form("form_edit_guest"):
                        edit_first = st.text_input("Nombre(s)", value=str(current_guest_data.get('first_name', '')))
                        edit_last = st.text_input("Apellido(s)", value=str(current_guest_data.get('last_name', '')))
                        
                        # Conditionally show the phone field ONLY if they are the Lead guest
                        new_phone = None
                        if current_guest_data.get('is_party_lead'):
                            phone_val = current_guest_data.get('phone_number')
                            if pd.isna(phone_val) or str(phone_val) == "None": 
                                phone_val = ""
                            new_phone = st.text_input("Teléfono (Solo números)", value=str(phone_val))
                        
                        # The Submit Button intercepts the flow
                        if st.form_submit_button("Guardar Cambios", type="primary"):
                            # Build the dynamic payload with the new names
                            update_payload = {
                                "first_name": edit_first.strip(),
                                "last_name": edit_last.strip()
                            }
                            
                            # Only update the phone if a new valid string was provided for a lead
                            if current_guest_data.get('is_party_lead') and new_phone:
                                update_payload["phone_number"] = new_phone.strip()
                                
                            # Trigger the modal popup instead of saving directly
                            confirm_swap_dialog(target_guest_id, update_payload)
    st.divider()

    # --- 5. METRICS & CHART ---
    if df.empty:
        st.info("No hay invitados registrados para este evento todavía.")
    else:
        # Standardize the column names based on Supabase schema (usually lowercase 'estatus')
        status_col = 'rsvp_status'#'estatus' if 'estatus' in df.columns else 'ESTATUS'
        
        # NOTE: Since our relational database architecture creates 1 row per person, 
        # we calculate totals by counting the rows (len) instead of summing a party size column.
        df[status_col] = df[status_col].astype(str)
        
        confirmed_count = len(df[df[status_col].str.contains("confirmed", case=False, na=False)])
        declined_count = len(df[df[status_col].str.contains("canceled", case=False, na=False)])
        pending_count = len(df[~df[status_col].str.contains("confirmed|canceled", case=False, na=False)])

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

    # --- ASSUMING df CONTAINS THE GUESTS FOR THE SELECTED EVENT ---
    # This goes in the section where df is already loaded and confirmed not empty.

    st.divider()
    st.markdown('<div class="host-header">📤 EXPORTAR DATOS</div>', unsafe_allow_html=True)

    if not df.empty:
        # 1. Create a copy of the dataframe so we don't alter the live dashboard charts
        export_df = df.copy()

        # 2. Ensure all requested columns exist (prevents KeyErrors if a new column like 'table_number' is missing)
        required_export_cols = [
            "first_name", "last_name", "phone_number", "party_size", 
            "rsvp_status", "is_vegan", "dietary_comments", "table_number", 
            "party_id", "is_party_lead"
        ]
        for col in required_export_cols:
            if col not in export_df.columns:
                export_df[col] = None 

        # 3. The Sorting Magic: 
        # Group by 'party_id' (alphabetically) AND push 'is_party_lead' (True) to the top of each group
        export_df = export_df.sort_values(
            by=["party_id", "is_party_lead"], 
            ascending=[True, False]
        )

        # 4. Filter strictly to the columns the planner wants to see
        final_export_cols = [
            "first_name", "last_name", "phone_number", "party_size", 
            "rsvp_status", "is_vegan", "dietary_comments", "table_number"
        ]
        export_df = export_df[final_export_cols]

        # 5. Rename columns for a premium B2B UI experience
        export_df = export_df.rename(columns={
            "first_name": "Nombre",
            "last_name": "Apellido",
            "phone_number": "Teléfono",
            "party_size": "Total de personas del Grupo",
            "rsvp_status": "Estatus RSVP",
            "is_vegan": "Es vegano",
            "dietary_comments": "Comentarios alimenticios",
            "table_number": "# Mesa"
        })

        # 6. Convert to CSV in memory 
        # CRITICAL: We use 'utf-8-sig' so Excel in Latin America reads accents (á, é, í, ñ) correctly!
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_data = csv_buffer.getvalue()

        # 7. Render the download button
        st.download_button(
            label="📥 Descargar Lista de Invitados (CSV)",
            data=csv_data,
            file_name=f"invitados_{selected_event_label}.csv",
            mime="text/csv",
            type="primary",
            help="Descarga la lista ordenada por familias, con el contacto principal primero."
        )

else:
    st.error("Por favor, inicia sesión para ver tus eventos.")

# ==========================================
# GESTIÓN DE ENVÍOS (DASHBOARD SECTION)
# ==========================================
#
## 1. Initialize session state for editing
#if "editing_row" not in st.session_state:
#    st.session_state.editing_row = None
#
#st.markdown('<div style="text-align:center; color:#9E9E9E; font-size:0.7rem; letter-spacing:0.2em; margin-top:50px;">ENVIO DE INVITACIONES AGENDADAS</div>', unsafe_allow_html=True)
#
## 2. Load the current schedule from your JSON file
#display_data = load_schedule()
#
## 3. Iterate and build the rows
#for i, item in enumerate(display_data):
#    dt_obj = datetime.strptime(item["Date"], "%Y-%m-%d %H:%M")
#    
#    # Columns for: Icon, Date Text, Status
#    c_btn, c_date, c_status = st.columns([0.5, 3, 1])
#    
#    with c_btn:
#        # Toggle edit mode for this specific row
#        if st.button("✏️", key=f"edit_btn_{i}"):
#            st.session_state.editing_row = i
#            st.rerun()
#
#    with c_date:
#        if st.session_state.editing_row == i:
#            # --- EDIT MODE ---
#            new_date = st.date_input("Nueva fecha", value=dt_obj.date(), key=f"picker_{i}", label_visibility="collapsed")
#            col_save, col_cancel = st.columns(2)
#            
#            if col_save.button("💾", key=f"save_{i}"):
#                # Update logic: keep original time, update date
#                new_full_dt = datetime.combine(new_date, dt_obj.time())
#                new_status = "ENVIADO" if new_full_dt < datetime.now() else "AGENDADO"
#                
#                # Overwrite and save
#                display_data[i] = {
#                    "Date": new_full_dt.strftime("%Y-%m-%d %H:%M"),
#                    "Status": new_status
#                }
#                save_schedule(display_data)
#                st.session_state.editing_row = None
#                st.rerun()
#                
#            if col_cancel.button("❌", key=f"cancel_{i}"):
#                st.session_state.editing_row = None
#                st.rerun()
#        else:
#            # --- DISPLAY MODE ---
#            display_str = dt_obj.strftime("%d de %B, %Y")
#            st.markdown(f'<div style="font-family:Playfair Display; font-size:1.1rem; color:#4A4A4A; padding:5px 0;">{display_str}</div>', unsafe_allow_html=True)
#
#    with c_status:
#        badge = "sent-badge" if item["Status"] == "ENVIADO" else "scheduled-badge"
#        st.markdown(f'<div style="padding:10px 0;"><span class="{badge}">{item["Status"]}</span></div>', unsafe_allow_html=True)
#    
#    st.divider()

# --- 8. ACTIONS ---
st.write("")
template_url = st.secrets["template_drive_url"]
st.markdown(f'<a href="{template_url}" target="_blank" style="text-decoration: none;"><div style="text-align: center; border: 1px solid #EAEAEA; border-radius: 15px; padding: 15px; color: #4A4A4A; font-family: Playfair Display; font-size: 1.2rem;">📥 Descargar plantilla de invitados</div></a>', unsafe_allow_html=True)

st.write("")

def register_conversation(guest_id: str, event_id: str, phone: str):
    """Inserts or updates the routing table so the FastAPI router knows this number."""
    payload = {
        "guest_id": guest_id,
        "event_id": event_id,
        "phone_number": phone,
        "last_notified_at": "now()"
    }
    supabase.table("conversations").upsert(payload, on_conflict="guest_id").execute()

# --- 1. THE MODAL DIALOG DEFINITION ---
@st.dialog("Titulares Pendientes de Envío", width="large")
def show_pending_leads_dialog(df):
    st.markdown("### 📋 Resumen de envíos")
    st.write("Los siguientes titulares de grupo están en fila para recibir la plantilla de WhatsApp:")
    
    # Filter for leads who are pending and actually have a phone number
    pending_leads = df[(df['is_party_lead'] == True) & 
                       (df['rsvp_status'] == 'pending') & 
                       (df['phone_number'].notna()) & 
                       (df['phone_number'] != "")]
    
    if pending_leads.empty:
        st.info("No hay titulares de grupo pendientes con número de teléfono registrado.")
        return

    # Show the list so the planner can visually verify the queue before execution
    st.dataframe(
        pending_leads[['first_name', 'last_name', 'phone_number', 'party_size']],
        hide_index=True,
        use_container_width=True
    )
    
    st.write(f"**Total a enviar:** {len(pending_leads)} mensajes.")
    
    # Form to prevent accidental double-clicks
    with st.form("bulk_send_form"):
        st.warning("⚠️ Asegúrate de que la plantilla seleccionada esté aprobada en Meta.")
        submit = st.form_submit_button("🚀 Enviar a Todos los Pendientes", type="primary", use_container_width=True)
        
        if submit:
            success_count = 0
            error_list = []
            
            # Loop through each pending lead and trigger the Meta API
            for _, row in pending_leads.iterrows():
                guest_name = str(row.get('first_name', '')).strip()
                phone = str(row.get('phone_number', ''))
                party_uuid = str(row.get('party_id', ''))
                guest_id = row.get('guest_id','')
                event_id = row.get('event_id','')
                
                # Dynamically generate the capability URL for this specific family
                rsvp_link = f"https://your-app.streamlit.app/rsvp?id={party_uuid}"
                
                pdf_url = "https://res.cloudinary.com/dnsixfadf/image/upload/v1779163670/invitacion_boda_Clara_Esperanza_Pulido_de_Castillo_bujf5x.pdf" 
                
                wedding_components = [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "link": pdf_url,
                                    "filename": "Invitacion_Boda.pdf"
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "parameter_name": "nombre_invitado", 
                                "text": guest_name
                            }
                        ]
                    }
                ]
                
                # Execute the API call
                success, error_msg = send_whatsapp_template(
                    recipient_phone=phone, 
                    template_name="invitacion_boda", 
                    language_code="en", 
                    components=wedding_components
                )
                
                if success:
                    register_conversation(guest_id, event_id, phone)
                    success_count += 1
                    # Execute a quick Supabase update to mark as notified
                    try:
                        supabase.table("guests").update({"rsvp_status": "notified"}).eq("party_id", party_uuid).execute()
                    except Exception as db_err:
                        error_list.append(f"{guest_name} - DB Update Error: {db_err}")
                else:
                    error_list.append(f"{guest_name} ({phone}): {error_msg}")
                    
            if success_count > 0:
                st.success(f"✅ Se enviaron {success_count} mensajes con éxito.")
                st.cache_data.clear() # Clear cache so the main dashboard updates the pending count
            
            if error_list:
                st.error("❌ Hubo errores con los siguientes envíos:")
                for err in error_list:
                    st.write(err)

# --- 2. THE TRIGGER IN YOUR DASHBOARD ---
# Assuming 'df' is your loaded Pandas dataframe for the currently selected event
st.divider()
st.markdown('<div class="host-header">📡 COMUNICACIÓN WABA</div>', unsafe_allow_html=True)



if st.button("🚀 Iniciar Envío de Invitaciones", type="primary"):
    show_pending_leads_dialog(df)

#Here it goes the code for generating a list based on the retrieved intents from the supabase database, extpected <USER>: <INTENT>
# ==========================================
# RSVP LIVE FEED (SUPABASE + GOOGLE SHEETS MERGE)
# ==========================================
#st.markdown('<div class="host-header" style="margin-top: 50px;">RESPUESTAS EN TIEMPO REAL</div>', unsafe_allow_html=True)
#st.markdown('<div class="main-title" style="font-size: 2.5rem;">RSVP Feed</div>', unsafe_allow_html=True)
#
#@st.cache_resource
#def init_supabase():
#    url = st.secrets["SUPABASE_URL"]
#    key = st.secrets["SUPABASE_KEY"]
#    return create_client(url, key)
#
#supabase = init_supabase()
#
#@st.cache_data(ttl=60) 
#def fetch_supabase_intents():
#    if not supabase: return []
#    try:
#        response = supabase.table("guests_data").select("*").order("updated_at", desc=True).execute()
#        return response.data
#    except: return []
#
#guests_intents = fetch_supabase_intents()
#
#if not guests_intents:
#    st.info("No hay respuestas de invitados registradas aún.")
#else:
#    df_intents = pd.DataFrame(guests_intents)
#    df_sheets = df.copy() 
#    
#    # 1. USAMOS EL NOMBRE EXACTO DE TU COLUMNA: 'CONTACTO: CELULAR'
#    if 'CONTACTO: CELULAR' in df_sheets.columns and 'phone_number' in df_intents.columns:
#        df_sheets['match_phone'] = df_sheets['CONTACTO: CELULAR'].astype(str).str.replace(r'\D', '', regex=True).str[-10:]
#        df_intents['match_phone'] = df_intents['phone_number'].astype(str).str.replace(r'\D', '', regex=True).str[-10:]
#        
#        merged_df = pd.merge(df_intents, df_sheets, on='match_phone', how='left')
#        
#        for _, row in merged_df.iterrows():
#            # 2. USAMOS LOS NOMBRES EXACTOS: 'NOMBRE(S)' y 'APELLIDO(S)'
#            first_name = str(row.get('NOMBRE(S)', ''))
#            last_name = str(row.get('APELLIDO(S)', ''))
#            
#            if first_name == 'nan' or first_name.strip() == '':
#                display_name = f"👤 DESCONOCIDO (📱 {row.get('phone_number', 'Sin número')})" 
#            else:
#                clean_first = first_name.replace('nan', '').strip()
#                clean_last = last_name.replace('nan', '').strip()
#                display_name = f"👤 {clean_first} {clean_last}".strip()
#                
#            intent = str(row.get('intent', 'neutral')).upper()
#            last_msg = str(row.get('last_message', '')).replace('nan', '')
#            
#            color, icon, status_text = "#9E9E9E", "⏳", "PENDIENTE"
#            if intent == "GOING": color, icon, status_text = "#4F8C78", "✅", "CONFIRMADO"
#            elif intent == "NOT GOING": color, icon, status_text = "#BC8F8F", "❌", "CANCELADO"
#                
#            st.markdown(f"""
#            <div style="border: 1px solid #EAEAEA; border-radius: 10px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; background-color: #FAFAFA;">
#                <div>
#                    <div style="font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #4A4A4A; font-weight: 500;">{display_name}</div>
#                    <div style="font-family: 'Montserrat', sans-serif; font-size: 0.75rem; color: #9E9E9E; margin-top: 4px; font-style: italic;">"{last_msg}"</div>
#                </div>
#                <div style="color: {color}; font-weight: bold; font-family: 'Montserrat', sans-serif; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.1em;">
#                    {icon} {status_text}
#                </div>
#            </div>
#            """, unsafe_allow_html=True)
#    else:
#        st.error("Error conectando las columnas. Revisa los nombres en el código.")
#            
#    if st.button("🔄 Actualizar Feed", use_container_width=True):
#        st.cache_data.clear()
#        st.rerun()
#