import os
import sys
from pathlib import Path
import google.generativeai as genai

sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, time, datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import json
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="Info EMI API",
    description="API para el bot de información universitaria",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL no configurada")
    DATABASE_URL = "postgresql://localhost:5432/info_emi"

def get_db_connection():
    """Establecer conexión a PostgreSQL"""
    try:
        if "render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
            conn_string = DATABASE_URL + "?sslmode=require"
        else:
            conn_string = DATABASE_URL
            
        conn = psycopg2.connect(conn_string, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a DB: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")

def get_university_context():
    conn = get_db_connection()
    cur = conn.cursor()
    context = "Información oficial de la Universidad:\n\n"
    
    try:
        cur.execute("SELECT name, code FROM careers WHERE is_active = TRUE")
        careers = cur.fetchall()
        context += "🎓 Carreras ofertadas:\n" + "\n".join([f"- {c['name']} ({c['code']})" for c in careers]) + "\n\n"

        cur.execute("SELECT title, date, start_time FROM events WHERE date >= CURRENT_DATE AND is_active = TRUE LIMIT 5")
        events = cur.fetchall()
        if events:
            context += "📅 Próximos eventos:\n" + "\n".join([f"- {e['title']} el {e['date']} a las {e['start_time']}" for e in events]) + "\n\n"

        cur.execute("SELECT question, answer FROM faqs WHERE is_active = TRUE")
        faqs = cur.fetchall()
        context += "❓ Preguntas Frecuentes:\n" + "\n".join([f"P: {f['question']} R: {f['answer']}" for f in faqs]) + "\n\n"
        
        return context
    except Exception as e:
        logger.error(f"Error construyendo contexto IA: {e}")
        return "Información no disponible temporalmente."
    finally:
        cur.close()
        conn.close()

class CareerCreate(BaseModel):
    code: str
    name: str
    campus: Optional[str] = None
    duration: Optional[str] = None
    modality: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    is_active: bool = True

class EventCreate(BaseModel):
    title: str
    event_type: str
    description: Optional[str] = None
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    organizer: Optional[str] = None
    registration_link: Optional[str] = None
    is_active: bool = True

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    priority: int = 1
    is_active: bool = True

class ContactCreate(BaseModel):
    department: str
    phone: Optional[str] = None
    email: Optional[str] = None
    office: Optional[str] = None
    schedule: Optional[str] = None
    responsible: Optional[str] = None
    is_active: bool = True
    priority: int = 1

class ScholarshipCreate(BaseModel):
    name: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    coverage: Optional[str] = None
    amount: Optional[float] = None
    application_link: Optional[str] = None
    is_active: bool = True

class AcademicCalendarCreate(BaseModel):
    event_name: str
    event_type: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    academic_period: Optional[str] = None
    is_active: bool = True

class PreUniversityCreate(BaseModel):
    program_name: str
    description: str
    duration: Optional[str] = None
    schedule: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cost: Optional[float] = None
    requirements: Optional[str] = None
    registration_link: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True

class CalendarEventCreate(BaseModel):
    event_name: str
    event_type: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    academic_period: Optional[str] = None
    is_active: bool = True

class InscriptionInfoCreate(BaseModel):
    period: str
    start_date: date
    end_date: date
    requirements: str
    process_steps: Optional[str] = None
    costs: Optional[str] = None
    documents_required: Optional[str] = None
    contact_info: Optional[str] = None
    is_active: bool = True


class LoginRequest(BaseModel):
    username: str
    password: str

class AskRequest(BaseModel):
    question: str

@app.post("/api/login")
async def login(request: LoginRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, password_hash FROM admins WHERE username = %s", 
                   (request.username,))
        admin = cur.fetchone()
        
        if not admin:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        input_hash = hashlib.sha256(request.password.encode()).hexdigest()
        
        if input_hash != admin['password_hash']:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        
        import base64
        auth_string = f"{request.username}:{request.password}"
        token = base64.b64encode(auth_string.encode()).decode()
        
        return {
            "status": "success", 
            "message": "Login exitoso",
            "token": token 
        }
    finally:
        cur.close()
        conn.close()

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, password_hash FROM admins WHERE username = %s", 
                   (credentials.username,))
        admin = cur.fetchone()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
        
        if password_hash != admin['password_hash']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        cur.execute("UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE id = %s", 
                   (admin['id'],))
        conn.commit()
        
        return {"id": admin['id'], "username": credentials.username}
    finally:
        cur.close()
        conn.close()

def log_action(admin_id: int, action: str, table_name: str = None, 
               record_id: int = None, changes: dict = None):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO audit_logs (admin_id, action, table_name, record_id, changes)
            VALUES (%s, %s, %s, %s, %s)
        """, (admin_id, action, table_name, record_id, 
              json.dumps(changes) if changes else None))
        conn.commit()
    except Exception as e:
        logger.error(f"Error en log_action: {e}")
    finally:
        cur.close()
        conn.close()


@app.get("/")
async def root():
    return {"message": "API Info EMI", "status": "online"}

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/api/careers")
async def get_careers(active_only: bool = True):
    """Obtener todas las carreras"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if active_only:
            cur.execute("SELECT * FROM careers WHERE is_active = TRUE ORDER BY name")
        else:
            cur.execute("SELECT * FROM careers ORDER BY name")
        
        careers = cur.fetchall()
        
        for career in careers:
            for key in ['created_at', 'updated_at']:
                if career.get(key):
                    career[key] = career[key].isoformat()
        
        return careers
    finally:
        cur.close()
        conn.close()

@app.post("/api/careers")
async def create_career(career: CareerCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""INSERT INTO careers (code, name, campus, duration, description, is_active) 
    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""", 
    (career.code, career.name, career.campus, career.duration, career.description, career.is_active))
        
        career_id = cur.fetchone()['id']
        conn.commit()
        
        log_action(admin['id'], "CREATE", "careers", career_id, career.dict())
        
        return {"message": "Carrera creada exitosamente", "id": career_id}
    except psycopg2.IntegrityError as e:
        raise HTTPException(status_code=400, detail="El código de carrera ya existe")
    finally:
        cur.close()
        conn.close()


@app.put("/api/careers/{career_id}")
async def update_career(career_id: int, career: CareerCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM careers WHERE id = %s", (career_id,))
        if not cur.fetchone():
             raise HTTPException(status_code=404, detail="Carrera no encontrada")

        cur.execute("""
            UPDATE careers 
            SET code=%s, name=%s, campus=%s, duration=%s, description=%s, is_active=%s
            WHERE id=%s
        """, (
            career.code, 
            career.name, 
            career.campus, 
            career.duration, 
            career.description, 
            career.is_active, 
            career_id
        ))
        conn.commit()
        
        log_action(admin['id'], "UPDATE", "careers", career_id)
        
        return {"message": "Carrera actualizada exitosamente"}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error actualizando carrera: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.delete("/api/careers/{career_id}")
async def delete_career(career_id: int, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE careers 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (career_id,))
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        
        conn.commit()
        log_action(admin['id'], "DELETE", "careers", career_id)
        
        return {"message": "Carrera desactivada exitosamente"}
    finally:
        cur.close()
        conn.close()

@app.get("/api/calendar")
async def get_calendar(active_only: bool = True):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = "SELECT * FROM academic_calendar"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY start_date ASC"
        cur.execute(query)
        
        items = []
        for row in cur.fetchall():
            item = dict(row)
            item['start_date'] = str(item['start_date'])
            if item['end_date']: item['end_date'] = str(item['end_date'])
            items.append(item)
        return items
    finally:
        cur.close(); conn.close()

@app.post("/api/calendar")
async def create_calendar_event(item: CalendarEventCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO academic_calendar (
                event_name, event_type, start_date, end_date, 
                description, academic_period, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            item.event_name, item.event_type, item.start_date, item.end_date, 
            item.description, item.academic_period, item.is_active
        ))
        conn.commit()
        return {"message": "Evento creado"}
    finally:
        cur.close(); conn.close()

@app.put("/api/calendar/{id}")
async def update_calendar_event(id: int, item: CalendarEventCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE academic_calendar SET 
                event_name=%s, event_type=%s, start_date=%s, end_date=%s, 
                description=%s, academic_period=%s, is_active=%s
            WHERE id=%s
        """, (
            item.event_name, item.event_type, item.start_date, item.end_date, 
            item.description, item.academic_period, item.is_active, id
        ))
        conn.commit()
        return {"message": "Evento actualizado"}
    finally:
        cur.close(); conn.close()

@app.delete("/api/calendar/{id}")
async def delete_calendar_event(id: int, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM academic_calendar WHERE id = %s", (id,))
        conn.commit()
        return {"message": "Eliminado"}
    finally:
        cur.close(); conn.close()


@app.get("/api/inscriptions")
async def get_inscriptions(active_only: bool = True):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = "SELECT * FROM inscriptions"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY start_date DESC" 
        cur.execute(query)
        
        items = []
        for row in cur.fetchall():
            item = dict(row)
            item['start_date'] = str(item['start_date'])
            item['end_date'] = str(item['end_date'])
            items.append(item)
        return items
    finally:
        cur.close(); conn.close()

@app.post("/api/inscriptions")
async def create_inscription(item: InscriptionInfoCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO inscriptions (
                period, start_date, end_date, requirements, process_steps, 
                costs, documents_required, contact_info, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            item.period, item.start_date, item.end_date, item.requirements, 
            item.process_steps, item.costs, item.documents_required, 
            item.contact_info, item.is_active
        ))
        conn.commit()
        return {"message": "Información creada"}
    finally:
        cur.close(); conn.close()

@app.put("/api/inscriptions/{id}")
async def update_inscription(id: int, item: InscriptionInfoCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE inscriptions SET 
                period=%s, start_date=%s, end_date=%s, requirements=%s, 
                process_steps=%s, costs=%s, documents_required=%s, 
                contact_info=%s, is_active=%s
            WHERE id=%s
        """, (
            item.period, item.start_date, item.end_date, item.requirements, 
            item.process_steps, item.costs, item.documents_required, 
            item.contact_info, item.is_active, id
        ))
        conn.commit()
        return {"message": "Actualizado"}
    finally:
        cur.close(); conn.close()

@app.delete("/api/inscriptions/{id}")
async def delete_inscription(id: int, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM inscriptions WHERE id = %s", (id,))
        conn.commit()
        return {"message": "Eliminado"}
    finally:
        cur.close(); conn.close()
        
@app.get("/api/preuniversity")
async def get_preuniversity(active_only: bool = True):
    """Obtener programas preuniversitarios"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if active_only:
            cur.execute("""
                SELECT * FROM pre_university 
                WHERE is_active = TRUE 
                ORDER BY start_date NULLS FIRST, program_name
            """)
        else:
            cur.execute("SELECT * FROM pre_university ORDER BY start_date DESC")
        
        programs = cur.fetchall()
        
        for program in programs:
            for date_field in ['start_date', 'end_date', 'created_at', 'updated_at']:
                if program.get(date_field):
                    program[date_field] = program[date_field].isoformat()
        
        return programs
    finally:
        cur.close()
        conn.close()

@app.post("/api/preuniversity")
async def create_preuniversity(
    program: PreUniversityCreate, 
    admin: dict = Depends(authenticate_admin)
):
    """Crear nuevo programa preuniversitario"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO pre_university (
                program_name, description, duration, schedule,
                start_date, end_date, cost, requirements,
                registration_link, contact_email, contact_phone, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            program.program_name, program.description, program.duration,
            program.schedule, program.start_date, program.end_date,
            program.cost, program.requirements, program.registration_link,
            program.contact_email, program.contact_phone, program.is_active
        ))
        
        program_id = cur.fetchone()['id']
        conn.commit()
        
        log_action(admin['id'], "CREATE", "pre_university", program_id, program.dict())
        
        return {"message": "Programa creado exitosamente", "id": program_id}
    except Exception as e:
        logger.error(f"Error creando preuniversitario: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/api/preuniversity/{program_id}")
async def update_preuniversity(
    program_id: int,
    program: PreUniversityCreate,
    admin: dict = Depends(authenticate_admin)
):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM pre_university WHERE id = %s", (program_id,))
        existing = cur.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Programa no encontrado")
        
        cur.execute("""
            UPDATE pre_university 
            SET program_name = %s,
                description = %s,
                duration = %s,
                schedule = %s,
                start_date = %s,
                end_date = %s,
                cost = %s,
                requirements = %s,
                registration_link = %s,
                contact_email = %s,
                contact_phone = %s,
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            program.program_name, program.description, program.duration,
            program.schedule, program.start_date, program.end_date,
            program.cost, program.requirements, program.registration_link,
            program.contact_email, program.contact_phone, program.is_active,
            program_id
        ))
        
        conn.commit()
        
        changes = {}
        for key, new_value in program.dict().items():
            old_value = existing.get(key)
            if str(old_value) != str(new_value):
                changes[key] = {"old": old_value, "new": new_value}
        
        log_action(admin['id'], "UPDATE", "pre_university", program_id, changes)
        
        return {"message": "Programa actualizado exitosamente"}
    finally:
        cur.close()
        conn.close()

@app.delete("/api/preuniversity/{program_id}")
async def delete_preuniversity(
    program_id: int,
    admin: dict = Depends(authenticate_admin)
):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE pre_university 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (program_id,))
        
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Programa no encontrada")
        
        conn.commit()
        log_action(admin['id'], "DELETE", "pre_university", program_id)
        
        return {"message": "Programa desactivado exitosamente"}
    finally:
        cur.close()
        conn.close()

@app.get("/api/events")
async def get_events(upcoming_only: bool = True):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if upcoming_only:
            cur.execute("""
                SELECT * FROM events 
                WHERE date >= CURRENT_DATE AND is_active = TRUE
                ORDER BY date, start_time
            """)
        else:
            cur.execute("SELECT * FROM events ORDER BY date DESC")
        
        events = cur.fetchall()
        
        for event in events:
            for date_field in ['date', 'created_at']:
                if event.get(date_field):
                    event[date_field] = event[date_field].isoformat()
            for time_field in ['start_time', 'end_time']:
                if event.get(time_field):
                    event[time_field] = str(event[time_field])
        
        return events
    finally:
        cur.close()
        conn.close()

@app.post("/api/events")
async def create_event(event: EventCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO events (
                title, event_type, description, date, start_time, 
                end_time, location, organizer, registration_link, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            event.title, event.event_type, event.description, event.date, 
            event.start_time, event.end_time, event.location, 
            event.organizer, event.registration_link, event.is_active
        ))
        
        event_id = cur.fetchone()['id']
        conn.commit()
        
        log_action(admin['id'], "CREATE", "events", event_id, event.dict())
        return {"message": "Evento creado exitosamente", "id": event_id}
    except Exception as e:
        logger.error(f"Error creando evento: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.put("/api/events/{event_id}")
async def update_event(event_id: int, event: EventCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        cur.execute("""
            UPDATE events 
            SET title = %s, event_type = %s, description = %s, date = %s, 
                start_time = %s, end_time = %s, location = %s, 
                organizer = %s, registration_link = %s, is_active = %s
            WHERE id = %s
        """, (
            event.title, event.event_type, event.description, event.date, 
            event.start_time, event.end_time, event.location, 
            event.organizer, event.registration_link, event.is_active, 
            event_id
        ))
        
        conn.commit()
        log_action(admin['id'], "UPDATE", "events", event_id)
        return {"message": "Evento actualizado exitosamente"}
    finally:
        cur.close()
        conn.close()

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: int, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
            
        conn.commit()
        log_action(admin['id'], "DELETE", "events", event_id)
        return {"message": "Evento eliminado exitosamente"}
    finally:
        cur.close()
        conn.close()

@app.get("/bot/careers")
async def get_bot_careers():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT code, name, campus, duration, modality, description
            FROM careers 
            WHERE is_active = TRUE
            ORDER BY name
        """)
        
        careers = cur.fetchall()
        return {"careers": careers}
    finally:
        cur.close()
        conn.close()

@app.get("/bot/preuniversity")
async def get_bot_preuniversity(upcoming_only: bool = True):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if upcoming_only:
            cur.execute("""
                SELECT id, program_name, description, duration, schedule,
                       start_date, end_date, cost, requirements,
                       contact_email, contact_phone
                FROM pre_university 
                WHERE is_active = TRUE 
                AND (end_date IS NULL OR end_date >= CURRENT_DATE)
                ORDER BY start_date NULLS FIRST, program_name
            """)
        else:
            cur.execute("""
                SELECT id, program_name, description, duration, schedule,
                       start_date, end_date, cost, requirements,
                       contact_email, contact_phone
                FROM pre_university 
                WHERE is_active = TRUE
                ORDER BY start_date NULLS FIRST, program_name
            """)
        
        programs = cur.fetchall()
        
        for program in programs:
            for date_field in ['start_date', 'end_date']:
                if program.get(date_field):
                    program[date_field] = program[date_field].isoformat()
        
        return {"programs": programs}
    finally:
        cur.close()
        conn.close()

@app.get("/bot/events")
async def get_bot_events(limit: int = 10):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT title, event_type, description, date, start_time, 
                   end_time, location, organizer
            FROM events 
            WHERE date >= CURRENT_DATE AND is_active = TRUE
            ORDER BY date, start_time
            LIMIT %s
        """, (limit,))
        
        events = cur.fetchall()
        
        for event in events:
            if event['date']:
                event['date'] = event['date'].isoformat()
            for time_field in ['start_time', 'end_time']:
                if event.get(time_field):
                    event[time_field] = str(event[time_field])
        
        return {"events": events}
    finally:
        cur.close()
        conn.close()

@app.get("/api/faqs")
async def get_faqs(active_only: bool = True):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = "SELECT * FROM faqs"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY priority, id"
        cur.execute(query)
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

@app.post("/api/faqs")
async def create_faq(faq: FAQCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO faqs (question, answer, category, priority, is_active)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (faq.question, faq.answer, faq.category, faq.priority, faq.is_active))
        conn.commit()
        return {"message": "FAQ creada", "id": cur.fetchone()['id']}
    finally:
        cur.close(); conn.close()

@app.put("/api/faqs/{faq_id}")
async def update_faq(faq_id: int, faq: FAQCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE faqs SET question=%s, answer=%s, category=%s, priority=%s, is_active=%s
            WHERE id=%s
        """, (faq.question, faq.answer, faq.category, faq.priority, faq.is_active, faq_id))
        conn.commit()
        return {"message": "FAQ actualizada"}
    finally:
        cur.close(); conn.close()

@app.delete("/api/faqs/{faq_id}")
async def delete_faq(faq_id: int, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM faqs WHERE id=%s", (faq_id,))
        conn.commit()
        return {"message": "FAQ eliminada"}
    finally:
        cur.close(); conn.close()

@app.get("/api/contacts")
async def get_contacts(active_only: bool = True):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        query = "SELECT * FROM contacts"
        if active_only: query += " WHERE is_active = TRUE"
        query += " ORDER BY priority, department"
        cur.execute(query)
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

@app.post("/api/contacts")
async def create_contact(contact: ContactCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO contacts (department, phone, office, schedule, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (contact.department, contact.phone, contact.office, contact.schedule, contact.is_active))
        
        new_id = cur.fetchone()['id']
        conn.commit()
        log_action(admin['id'], "CREATE", "contacts", new_id)
        return {"message": "Contacto creado", "id": new_id}
    finally:
        cur.close()
        conn.close()

@app.put("/api/contacts/{contact_id}")
async def update_contact(contact_id: int, contact: ContactCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE contacts 
            SET department=%s, phone=%s, office=%s, schedule=%s, is_active=%s
            WHERE id=%s
        """, (contact.department, contact.phone, contact.office, contact.schedule, contact.is_active, contact_id))
        
        conn.commit()
        log_action(admin['id'], "UPDATE", "contacts", contact_id)
        return {"message": "Contacto actualizado"}
    finally:
        cur.close()
        conn.close()

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: int, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM contacts WHERE id=%s", (contact_id,))
        conn.commit()
        return {"message": "Contacto eliminado"}
    finally:
        cur.close(); conn.close()

@app.get("/api/scholarships")
async def get_scholarships(active_only: bool = True):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = "SELECT * FROM scholarships"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY id DESC"
        
        cur.execute(query)
        items = cur.fetchall()
        
        result = []
        for item in items:
            item_dict = dict(item)
            if item_dict.get('deadline'):
                item_dict['deadline'] = str(item_dict['deadline'])
            result.append(item_dict)
            
        return result
    finally:
        cur.close()
        conn.close()

@app.post("/api/scholarships")
async def create_scholarship(sch: ScholarshipCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO scholarships (name, description, requirements, coverage, amount, application_link, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (sch.name, sch.description, sch.requirements, sch.coverage, sch.amount, sch.application_link, sch.is_active))
        conn.commit()
        return {"message": "Beca creada", "id": cur.fetchone()['id']}
    finally:
        cur.close(); conn.close()

@app.put("/api/scholarships/{sch_id}")
async def update_scholarship(sch_id: int, sch: ScholarshipCreate, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE scholarships SET name=%s, description=%s, requirements=%s, coverage=%s, amount=%s, application_link=%s, is_active=%s
            WHERE id=%s
        """, (sch.name, sch.description, sch.requirements, sch.coverage, sch.amount, sch.application_link, sch.is_active, sch_id))
        conn.commit()
        return {"message": "Beca actualizada"}
    finally:
        cur.close(); conn.close()

@app.delete("/api/scholarships/{sch_id}")
async def delete_scholarship(sch_id: int, admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM scholarships WHERE id=%s", (sch_id,))
        conn.commit()
        return {"message": "Beca eliminada"}
    finally:
        cur.close(); conn.close()

@app.get("/panel", response_class=HTMLResponse)
async def get_panel():
    """Servir panel de administración"""
    try:

        base_path = Path(__file__).parent.parent
        file_path = base_path / "frontend" / "panel.html"
        
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="Error: No encuentro el archivo en: " + str(file_path)) # Útil para depurar

@app.get("/api/stats")
async def get_stats(admin: dict = Depends(authenticate_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        stats = {}
        
        tables = [
            'careers', 'events', 'faqs', 'contacts', 
            'scholarships', 'academic_calendar', 'pre_university'
        ]
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) as count FROM {table} WHERE is_active = TRUE")
                stats[table] = cur.fetchone()['count']
            except:
                stats[table] = 0
        
        cur.execute("""
            SELECT COUNT(*) as count FROM events 
            WHERE date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
            AND is_active = TRUE
        """)
        stats['upcoming_events'] = cur.fetchone()['count']
        
        cur.execute("""
            SELECT COUNT(*) as count FROM audit_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)
        stats['recent_activity'] = cur.fetchone()['count']
        
        return stats
    finally:
        cur.close()
        conn.close()

@app.post("/bot/ask")
async def ask_bot_ai(request: AskRequest):
    if not GEMINI_API_KEY:
        return {"answer": "Lo siento, mi cerebro de IA no está configurado (Falta API Key)."}

    try:
        context_data = get_university_context()
        
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Actúa como 'Info_EMI', un asistente universitario amable y útil.
        
        Usa EXCLUSIVAMENTE la siguiente información para responder (si no está aquí, di que no sabes y sugiere contactar a admisiones):
        
        {context_data}
        
        Usuario pregunta: {request.question}
        
        Respuesta (breve, concisa y con emojis si aplica):
        """
        
        response = model.generate_content(prompt)
        return {"answer": response.text}
        
    except Exception as e:
        logger.error(f"Error IA: {e}")
        return {"answer": "Tuve un error procesando tu pregunta. Intenta más tarde."}

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando API Info EMI...")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version()")
        db_version = cur.fetchone()
        logger.info(f"Conectado a PostgreSQL: {db_version['version']}")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")

try:
    static_path = Path(__file__).parent.parent / "frontend" / "static"
    
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Carpeta static montada desde: {static_path}")
except Exception as e:
    logger.warning(f"No se pudo montar static: {e}")