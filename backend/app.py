import os
import sys
from pathlib import Path

# Agregar directorio actual al path
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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Crear aplicación FastAPI
app = FastAPI(
    title="Info EMI API",
    description="API para el bot de información universitaria",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seguridad
security = HTTPBasic()

# Obtener variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL no configurada")
    DATABASE_URL = "postgresql://localhost:5432/info_emi"

# Conexión a base de datos
def get_db_connection():
    """Establecer conexión a PostgreSQL"""
    try:
        # Para Render, agregar sslmode
        if "render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
            conn_string = DATABASE_URL + "?sslmode=require"
        else:
            conn_string = DATABASE_URL
            
        conn = psycopg2.connect(conn_string, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a DB: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")

# ========== MODELOS PYDANTIC ==========

class CareerCreate(BaseModel):
    code: str
    name: str
    faculty: Optional[str] = None
    duration: Optional[str] = None
    modality: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    cost: Optional[float] = None
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
    deadline: Optional[date] = None
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

# ========== AUTENTICACIÓN ==========

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Autenticar administrador"""
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
        
        # Verificar contraseña (SHA256)
        password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
        
        if password_hash != admin['password_hash']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        # Actualizar último login
        cur.execute("UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE id = %s", 
                   (admin['id'],))
        conn.commit()
        
        return {"id": admin['id'], "username": credentials.username}
    finally:
        cur.close()
        conn.close()

def log_action(admin_id: int, action: str, table_name: str = None, 
               record_id: int = None, changes: dict = None):
    """Registrar acción en logs de auditoría"""
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

# ========== RUTAS DE SALUD ==========

@app.get("/")
async def root():
    return {"message": "API Info EMI", "status": "online"}

@app.get("/health")
async def health_check():
    """Endpoint de salud para monitoreo"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ========== RUTAS PARA CARRERAS ==========

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
        
        # Convertir tipos de fecha para JSON
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
    """Crear nueva carrera"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO careers (code, name, faculty, duration, modality, 
                               description, requirements, cost, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (career.code, career.name, career.faculty, career.duration, 
              career.modality, career.description, career.requirements, 
              career.cost, career.is_active))
        
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
    """Actualizar carrera existente"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Obtener datos anteriores
        cur.execute("SELECT * FROM careers WHERE id = %s", (career_id,))
        old_data = cur.fetchone()
        
        if not old_data:
            raise HTTPException(status_code=404, detail="Carrera no encontrada")
        
        # Actualizar
        cur.execute("""
            UPDATE careers 
            SET code = %s, name = %s, faculty = %s, duration = %s, 
                modality = %s, description = %s, requirements = %s, 
                cost = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (career.code, career.name, career.faculty, career.duration, 
              career.modality, career.description, career.requirements, 
              career.cost, career.is_active, career_id))
        
        conn.commit()
        
        # Registrar cambios
        changes = {}
        for key, new_value in career.dict().items():
            old_value = old_data.get(key)
            if str(old_value) != str(new_value):
                changes[key] = {"old": old_value, "new": new_value}
        
        log_action(admin['id'], "UPDATE", "careers", career_id, changes)
        
        return {"message": "Carrera actualizada exitosamente"}
    finally:
        cur.close()
        conn.close()

@app.delete("/api/careers/{career_id}")
async def delete_career(career_id: int, admin: dict = Depends(authenticate_admin)):
    """Desactivar carrera"""
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

# ========== RUTAS PARA PREUNIVERSITARIOS ==========

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
        
        # Formatear fechas
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
    """Actualizar programa preuniversitario"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Verificar existencia
        cur.execute("SELECT * FROM pre_university WHERE id = %s", (program_id,))
        existing = cur.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Programa no encontrado")
        
        # Actualizar
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
        
        # Registrar cambios
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
    """Desactivar programa preuniversitario"""
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

# ========== RUTAS PARA EVENTOS ==========

@app.get("/api/events")
async def get_events(upcoming_only: bool = True):
    """Obtener eventos"""
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

# ========== RUTAS PARA EL BOT ==========

@app.get("/bot/careers")
async def get_bot_careers():
    """Obtener carreras para el bot"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT code, name, faculty, duration, modality, description, cost
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
    """Obtener programas preuniversitarios para el bot"""
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
        
        # Formatear fechas
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
    """Obtener eventos para el bot"""
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

# ========== RUTAS PARA PANEL ADMIN ==========

@app.get("/panel", response_class=HTMLResponse)
async def get_panel():
    """Servir panel de administración"""
    try:
        with open("frontend/panel.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        # Panel simple si no existe el archivo
        return HTMLResponse(content="""
        <html>
            <head><title>Panel Info EMI</title></head>
            <body>
                <h1>Panel de Administración</h1>
                <p>Sube el archivo panel.html a la carpeta frontend/</p>
            </body>
        </html>
        """)

# ========== RUTAS PARA ESTADÍSTICAS ==========

@app.get("/api/stats")
async def get_stats(admin: dict = Depends(authenticate_admin)):
    """Obtener estadísticas del sistema"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        stats = {}
        
        # Contar registros activos
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
        
        # Eventos próximos (7 días)
        cur.execute("""
            SELECT COUNT(*) as count FROM events 
            WHERE date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
            AND is_active = TRUE
        """)
        stats['upcoming_events'] = cur.fetchone()['count']
        
        # Actividad reciente
        cur.execute("""
            SELECT COUNT(*) as count FROM audit_logs 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)
        stats['recent_activity'] = cur.fetchone()['count']
        
        return stats
    finally:
        cur.close()
        conn.close()

# ========== INICIALIZACIÓN ==========

@app.on_event("startup")
async def startup_event():
    """Evento al iniciar la aplicación"""
    logger.info("Iniciando API Info EMI...")
    
    # Verificar conexión a BD
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

# Montar archivos estáticos
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except:
    logger.warning("No se encontró carpeta static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)