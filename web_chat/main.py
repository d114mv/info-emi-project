import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import groq
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ChatMessage(BaseModel):
    message: str
    history: list = []

def get_university_context():
    from psycopg2.extras import RealDictCursor 
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    context = "Información oficial y actualizada de la Universidad (EMI):\n\n"
    
    try:
        cur.execute("""
            SELECT name, code, description, duration, modality, campus 
            FROM careers 
            WHERE is_active = TRUE
        """)
        careers = cur.fetchall()
        if careers:
            context += "🎓 OFERTA ACADÉMICA (CARRERAS):\n"
            for c in careers:
                context += f"--- {c['name']} ({c['code']}) ---\n"
                if c['description']: context += f"Descripción: {c['description']}\n"
                if c['duration']: context += f"Duración: {c['duration']}\n"
                if c['modality']: context += f"Modalidad: {c['modality']}\n"
                if c['campus']: context += f"Sede: {c['campus']}\n"
                context += "\n"

        cur.execute("SELECT question, answer FROM faqs WHERE is_active = TRUE")
        faqs = cur.fetchall()
        if faqs:
            context += "❓ BANCO DE PREGUNTAS FRECUENTES:\n"
            for f in faqs:
                context += f"P: {f['question']} R: {f['answer']}\n"
            context += "\n"

        cur.execute("SELECT config_key, config_value FROM system_config WHERE is_public = TRUE")
        configs = cur.fetchall()
        if configs:
            context += "📍 UBICACIONES Y CONTACTOS OFICIALES:\n"
            for item in configs:
                key_clean = item['config_key'].replace('university_', '').replace('_', ' ').capitalize()
                context += f"- {key_clean}: {item['config_value']}\n"
            context += "\n"

        cur.execute("""
            SELECT name, description, coverage, requirements 
            FROM scholarships 
            WHERE is_active = TRUE
        """)
        becas = cur.fetchall()
        if becas:
            context += "💰 BECAS Y DESCUENTOS DISPONIBLES:\n"
            for b in becas:
                context += f"- {b['name']}: Cobertura del {b['coverage']}\n"
                if b['description']: context += f"  Descripción: {b['description']}\n"
                if b['requirements']: context += f"  Requisitos: {b['requirements']}\n"
            context += "\n"

        cur.execute("""
            SELECT program_name, cost, start_date 
            FROM pre_university 
            WHERE is_active = TRUE
        """)
        preus = cur.fetchall()
        if preus:
            context += "📚 CURSOS PREUNIVERSITARIOS:\n"
            for p in preus:
                context += f"- {p['program_name']}: Costo {p['cost']} Bs.\n"
                if p['start_date']: context += f"  Inicia: {p['start_date']}\n"
            context += "\n"

        return context

    except Exception as e:
        print(f"Error generando contexto IA: {e}")
        return "Información temporalmente no disponible."
    finally:
        cur.close()
        conn.close() 


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(chat: ChatMessage):
    try:
        user_input = chat.message
        
        client = groq.Client(api_key=os.environ.get("GROQ_API_KEY"))
        
        context_data = get_university_context()
        system_prompt = f"""
        Actúa como 'Info_EMI', un asistente de la Escuela Militar de Ingeniería (EMI) Unidad Académica Cochabamba, en la ciudad de Cochabamba-Bolivia.
        Eres amable, profesional y usas emojis para dar vida a la conversación.
        
        TU REGLA DE ORO:
        Usa EXCLUSIVAMENTE la siguiente información de contexto para responder. 
        Si la respuesta no está en el texto de abajo, di cortésmente que no tienes esa información y sugiere contactar a admisiones.
        NO inventes fechas ni datos.
        
        INSTRUCCIÓN DE CONTROL DE INTERFAZ (IMPORTANTE):
        Si el usuario está preguntando específicamente por información detallada de una carrera (malla, plan de estudios, materias, o detalles generales de la carrera),
        DEBES incluir al final de tu respuesta una etiqueta oculta con el CÓDIGO de la carrera.
        
        El formato es: [[SEND_IMAGE: CODIGO]]
        
        Extrae el CODIGO de los paréntesis en la sección de "OFERTA ACADÉMICA" del contexto (ej: SIS, CIV, MCT, COM).
        
        Ejemplo:
        Usuario: "Háblame de Sistemas"
        Tú: "La carrera de Ingeniería de Sistemas... (toda la info)...
        [[SEND_IMAGE: SIS]]"
        
        --- INFORMACIÓN DE CONTEXTO (BASE DE DATOS) ---
        {context_data}
        -----------------------------------------------
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.3-70b-versatile",
        )
        
        ai_response = chat_completion.choices[0].message.content

        image_url = None
        patron = r"\[\[SEND_IMAGE: (\w+)\]\]"
        match = re.search(patron, ai_response)
        
        if match:
            codigo = match.group(1)
            ai_response = ai_response.replace(match.group(0), "").strip()
            image_url = f"/static/mallas/{codigo}.jpg"

        return JSONResponse(content={
            "response": ai_response,
            "image": image_url
        })

    except Exception as e:
        return JSONResponse(content={"response": f"Error del servidor: {str(e)}", "image": None})