import os
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URI = os.environ.get("DB_URI")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not DB_URI or not GOOGLE_API_KEY:
    raise ValueError("❌ Error Crítico: Faltan las variables de entorno DB_URI o GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

class ChatRequest(BaseModel):
    message: str

KNOWLEDGE_CACHE = ""

def load_knowledge():
    global KNOWLEDGE_CACHE
    try:
        print("🔄 Conectando a Neon para actualizar conocimiento...")
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute("SELECT question, answer FROM knowledge_base")
        rows = cur.fetchall()
        conn.close()
        
        context = "INFORMACIÓN OFICIAL EMI UAC:\n"
        for q, a in rows:
            context += f"Pregunta: {q}\nRespuesta Oficial: {a}\n---\n"
        
        KNOWLEDGE_CACHE = context
        print("✅ Base de conocimiento cargada en memoria RAM exitosamente.")
    except Exception as e:
        print(f"🔴 Error al cargar DB: {e}")
        if not KNOWLEDGE_CACHE: 
            KNOWLEDGE_CACHE = "Error: No se pudo acceder a la información oficial."

@app.on_event("startup")
async def startup_event():
    load_knowledge()

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_msg = request.message
    
    if not KNOWLEDGE_CACHE:
        load_knowledge()

    system_instruction = f"""
    Actúa como el Asistente Virtual Oficial de la EMI (Escuela Militar de Ingeniería).
    
    INFORMACIÓN DE REFERENCIA (ÚSALAS COMO VERDAD ABSOLUTA):
    {KNOWLEDGE_CACHE}
    
    INSTRUCCIONES:
    1. Tu objetivo es responder dudas usando SOLO la información de referencia; puedes usar emojis referentes al contexto al momento de responder.
    2. Si el usuario saluda, sé cordial y breve.
    3. FORMATO: Usa Markdown para que se vea bonito (usa **negritas** para resaltar datos clave y listas con guiones para enumerar requisitos).
    4. AL FINAL DE CADA RESPUESTA: Agrega siempre un salto de línea y el siguiente texto exacto:
    "Para mayor información, acércate a nuestras oficinas en Calle Lanza #811, entre Oruro y La Paz o escríbenos a los WhatsApp 71420764 / 71532851."
    5. RESTRICCIÓN: Si la pregunta NO tiene relación con la EMI, o con la información provista (ej: recetas, clima, chistes), O si la información no es suficiente, DEBES responder textualmente con:

    "Para ayudarte mejor, selecciona una de las preguntas frecuentes listadas arriba 👆 o puedes acercarte a nuestras oficinas ubicadas en la calle Lanza, entre Oruro y La Paz, o comunicarte a los números de Whatsapp 71420764 y 71532851."
    
    Pregunta del estudiante: {user_msg}
    """

    try:
        response = model.generate_content(system_instruction)
        return {"response": response.text}
    except Exception as e:
        print(f"🔴 ERROR REAL DE GEMINI: {e}")
        return {"response": "Lo siento, hubo un error de conexión con mi cerebro digital. Intenta de nuevo en unos segundos."}