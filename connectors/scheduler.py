from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from connectors.whatsapp import send_whatsapp_template
import streamlit as st

# Usamos una pequeña base de datos SQLite para que si el servidor se reinicia, 
# las tareas programadas no se borren.
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}

scheduler = BackgroundScheduler(jobstores=jobstores)

def init_scheduler():
    """Inicia el scheduler si no está corriendo."""
    if not scheduler.running:
        scheduler.start()

def schedule_whatsapp(phone, date_time, name):
    """Programa un envío de WhatsApp para una fecha específica."""
    job_id = f"invite_{phone}_{date_time.strftime('%Y%m%d%H%M')}"
    
    # Agregamos la tarea
    scheduler.add_job(
        send_whatsapp_template,
        trigger='date',
        run_date=date_time,
        args=[phone], # Aquí pasarías los argumentos de tu función
        id=job_id,
        replace_existing=True
    )
    return job_id