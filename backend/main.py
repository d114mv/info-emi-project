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
    raise ValueError("Faltan las variables de entorno DB_URI o GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class ChatRequest(BaseModel):
    message: str

def get_knowledge():
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute("SELECT question, answer FROM knowledge_base")
        rows = cur.fetchall()
        conn.close()
        
        context = "INFORMACIÓN OFICIAL EMI UAC:\n"
        for q, a in rows:
            context += f"Pregunta: {q}\nRespuesta Oficial: {a}\n---\n"
        return context
    except Exception as e:
        print(f"Error DB: {e}")
        return ""

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_msg = request.message
    knowledge_context = get_knowledge()

    system_instruction = f"""
    Actúa como el Asistente Virtual Oficial de la EMI (Escuela Militar de Ingeniería).
    
    INFORMACIÓN DE REFERENCIA:
    {knowledge_context}
    
    INSTRUCCIONES:
    1. Responde preguntas basándote EXCLUSIVAMENTE en la información de referencia.
    2. Si el usuario saluda, sé cordial y breve.
    3. Si la pregunta NO está relacionada con la información provista (ej: recetas, clima, chistes), O si la información no es suficiente, DEBES responder textualmente con:
    "Para ayudarte mejor, selecciona una de las preguntas frecuentes listadas arriba 👆"
    
    Pregunta del usuario: {user_msg}
    """

    try:
        response = model.generate_content(system_instruction)
        return {"response": response.text}
    except Exception as e:
        return {"response": "Lo siento, hubo un error de conexión."}