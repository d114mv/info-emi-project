#!/usr/bin/env python3
"""
Worker principal del bot de Telegram
Ejecutar en segundo plano para mantener el bot activo
"""
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Agregar directorio al path
sys.path.append(str(Path(__file__).parent))

# Importar módulos después de configurar path
import telebot
from telebot import types
import requests
import threading
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
TOKEN = os.getenv("BOT_TOKEN", "8577123738:AAEjeNx5cnErCWfm2f1dcpUzhm4Q1xa1qkE")
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Crear instancia del bot
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ========== FUNCIONES AUXILIARES ==========

def format_career(career: dict) -> str:
    """Formatear información de carrera para mostrar"""
    text = f"<b>🎓 {career['name']}</b>\n"
    text += f"<code>{career['code']}</code>\n\n"
    
    if career.get('faculty'):
        text += f"🏛️ <b>Facultad:</b> {career['faculty']}\n"
    if career.get('duration'):
        text += f"⏳ <b>Duración:</b> {career['duration']}\n"
    if career.get('modality'):
        text += f"📚 <b>Modalidad:</b> {career['modality']}\n"
    
    if career.get('description'):
        desc = career['description']
        if len(desc) > 200:
            desc = desc[:200] + "..."
        text += f"\n📝 <b>Descripción:</b>\n{desc}\n"
    
    return text

def format_preuniversity(program: dict) -> str:
    """Formatear información de programa preuniversitario"""
    text = f"<b>📚 {program['program_name']}</b>\n\n"
    
    if program.get('description'):
        desc = program['description']
        if len(desc) > 250:
            desc = desc[:250] + "..."
        text += f"📝 <b>Descripción:</b>\n{desc}\n\n"
    
    if program.get('duration'):
        text += f"⏳ <b>Duración:</b> {program['duration']}\n"
    if program.get('schedule'):
        text += f"🕐 <b>Horario:</b> {program['schedule']}\n"
    
    if program.get('start_date'):
        try:
            start_date = datetime.strptime(program['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
            text += f"📅 <b>Inicia:</b> {start_date}\n"
        except:
            text += f"📅 <b>Inicia:</b> {program['start_date']}\n"
    
    if program.get('end_date'):
        try:
            end_date = datetime.strptime(program['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
            text += f"📅 <b>Finaliza:</b> {end_date}\n"
        except:
            text += f"📅 <b>Finaliza:</b> {program['end_date']}\n"
    
    if program.get('cost'):
        text += f"💰 <b>Costo:</b> ${program['cost']:,.2f}\n"
    
    if program.get('requirements'):
        req = program['requirements']
        if len(req) > 150:
            req = req[:150] + "..."
        text += f"\n📋 <b>Requisitos:</b>\n{req}\n"
    
    if program.get('contact_email') or program.get('contact_phone'):
        text += "\n📞 <b>Contacto:</b>\n"
        if program.get('contact_email'):
            text += f"📧 {program['contact_email']}\n"
        if program.get('contact_phone'):
            text += f"📱 {program['contact_phone']}\n"
    
    return text

def get_api_data(endpoint: str, params: dict = None):
    """Obtener datos de la API"""
    try:
        url = f"{API_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error conectando a API: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en get_api_data: {e}")
        return None
# --- FUNCIONES DE FORMATO NUEVAS ---

def format_scholarship(item: dict) -> str:
    text = f"💰 <b>{item['name']}</b>\n"
    if item.get('coverage'):
        text += f"💎 Cobertura: {item['coverage']}\n"
    if item.get('deadline'):
        text += f"📅 Límite: {item['deadline']}\n"
    
    if item.get('description'):
        text += f"\n📝 {item['description']}\n"
    
    if item.get('requirements'):
        text += f"\n📋 <b>Requisitos:</b>\n{item['requirements']}\n"
        
    if item.get('application_link'):
        text += f"\n🔗 <a href='{item['application_link']}'>Link de aplicación</a>\n"
        
    return text

def format_contact(item: dict) -> str:
    text = f"🏢 <b>{item['department']}</b>\n"
    if item.get('responsible'):
        text += f"👤 Resp: {item['responsible']}\n"
    
    text += "\n"
    if item.get('phone'):
        text += f"📞 {item['phone']}\n"
    if item.get('email'):
        text += f"📧 {item['email']}\n"
    if item.get('office'):
        text += f"📍 {item['office']}\n"
    if item.get('schedule'):
        text += f"🕐 {item['schedule']}\n"
        
    return text

def format_faq(item: dict) -> str:
    return f"❓ <b>{item['question']}</b>\n💬 {item['answer']}\n"

# ========== HANDLERS DE COMANDOS ==========

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Manejador del comando /start"""
    logger.info(f"Comando /start de {message.chat.id}")
    welcome_text = """
<b>¡Hola! Soy Info_EMI 🤖</b>
Tu asistente virtual de la universidad.

<b>Puedes usar los botones o comandos:</b>
/carreras - Ver oferta académica
/preuniversitario - Cursos de nivelación
/eventos - Próximas actividades
/becas - Becas disponibles
/faq - Preguntas frecuentes
/contacto - Contactos por área
/calendario - Fechas importantes
/inscripciones - Info de matrícula
/help - Mostrar todos los comandos

<i>Selecciona una opción para comenzar:</i>
"""
    
    try:
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error enviando mensaje de inicio: {e}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Manejador del comando /help"""
    help_text = """
<b>📋 COMANDOS DISPONIBLES</b>

<u>Comandos principales:</u>
/start - Iniciar conversación
/carreras - Ver todas las carreras
/preuniversitario - Cursos preuniversitarios
/eventos - Eventos próximos
/becas - Becas y descuentos
/faq - Preguntas frecuentes
/contacto - Números de contacto
/calendario - Calendario académico
/inscripciones - Información de matrícula

<u>También puedes usar:</u>
• Los botones del teclado
• Escribir directamente: "carreras", "eventos", etc.

<i>¿Necesitas ayuda específica? Escribe tu pregunta.</i>

"""
    
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

@bot.message_handler(commands=['carreras', 'carrera', '🎓 Carreras' ])
def handle_careers(message):
    """Manejador del comando /carreras"""
    logger.info(f"Comando /carreras de {message.chat.id}")
    
    # Obtener datos de la API
    data = get_api_data("bot/careers")
    
    if not data or 'careers' not in data or not data['careers']:
        bot.send_message(
            message.chat.id,
            "⚠️ No hay carreras disponibles en este momento.\n\n"
            "Por favor, intenta más tarde o contacta con admisiones.",
            parse_mode="HTML"
        )
        return
    
    careers = data['careers']
    
    # Crear botones inline para cada carrera
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for career in careers[:10]:  # Máximo 10 para no sobrecargar
        button_text = f"🎓 {career['code']} - {career['name'][:25]}..."
        callback_data = f"career_{career['code']}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Si hay más de 10 carreras, agregar paginación
    if len(careers) > 10:
        markup.add(types.InlineKeyboardButton("▶️ Ver más carreras", callback_data="careers_more"))
    
    bot.send_message(
        message.chat.id,
        f"<b>🎓 OFERTA ACADÉMICA</b>\n\n"
        f"Selecciona una carrera para ver detalles:\n"
        f"<i>(Mostrando {min(len(careers), 10)} de {len(careers)} carreras)</i>",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.message_handler(commands=['preuniversitario', 'preuniversitarios', 'pre', '📚 Preuniversitarios'])
def handle_preuniversity(message):
    """Manejador del comando /preuniversitario"""
    logger.info(f"Comando /preuniversitario de {message.chat.id}")
    
    data = get_api_data("bot/preuniversity")
    
    if not data or 'programs' not in data or not data['programs']:
        bot.send_message(
            message.chat.id,
            "📚 <b>Programas Preuniversitarios</b>\n\n"
            "No hay programas disponibles en este momento.\n"
            "Contacta con el departamento de admisiones para más información.",
            parse_mode="HTML"
        )
        return
    
    programs = data['programs']
    
    # Crear botones inline
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for program in programs[:8]:  # Máximo 8 programas
        button_text = f"📚 {program['program_name'][:30]}"
        if len(program['program_name']) > 30:
            button_text += "..."
        callback_data = f"preuni_{program['id']}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Botón para ver todos los detalles
    if len(programs) > 1:
        markup.add(types.InlineKeyboardButton("📋 Ver resumen de todos", callback_data="preuni_all"))
    
    bot.send_message(
        message.chat.id,
        "<b>📚 PROGRAMAS PREUNIVERSITARIOS</b>\n\n"
        "Cursos de nivelación para ingresar a la universidad:\n\n"
        "<i>Selecciona un programa para ver detalles completos:</i>",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.message_handler(commands=['eventos', 'evento', '📅 Eventos'])
def handle_events(message):
    """Manejador del comando /eventos"""
    data = get_api_data("bot/events", {"limit": 5})
    
    if not data or 'events' not in data or not data['events']:
        bot.send_message(
            message.chat.id,
            "📅 <b>Próximos Eventos</b>\n\n"
            "No hay eventos programados en este momento.\n"
            "¡Vuelve a consultar pronto!",
            parse_mode="HTML"
        )
        return
    
    events = data['events']
    
    response_text = "<b>📅 PRÓXIMOS EVENTOS</b>\n\n"
    
    for i, event in enumerate(events, 1):
        response_text += f"<b>{i}. {event['title']}</b>\n"
        
        if event.get('date'):
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
                response_text += f"📅 <i>Fecha:</i> {event_date}\n"
            except:
                response_text += f"📅 <i>Fecha:</i> {event['date']}\n"
        
        if event.get('start_time'):
            response_text += f"🕐 <i>Hora:</i> {event['start_time'][:5]}\n"
        
        if event.get('location'):
            response_text += f"📍 <i>Lugar:</i> {event['location']}\n"
        
        if event.get('description'):
            desc = event['description']
            if len(desc) > 100:
                desc = desc[:100] + "..."
            response_text += f"📝 {desc}\n"
        
        response_text += "\n"
    
    bot.send_message(message.chat.id, response_text, parse_mode="HTML")

# --- HANDLERS CONECTADOS A LA BD ---

@bot.message_handler(commands=['becas', 'beca', '💰 Becas'])
def handle_scholarships(message):
    """Manejador dinámico de Becas"""
    # 1. Pedir datos a tu API
    data = get_api_data("api/scholarships")
    
    if not data:
        bot.send_message(message.chat.id, "📭 No hay becas disponibles por ahora.")
        return

    # 2. Enviar mensaje
    bot.send_message(message.chat.id, "🎓 <b>BECAS Y DESCUENTOS DISPONIBLES</b>", parse_mode="HTML")
    
    for item in data:
        text = format_scholarship(item)
        bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)

@bot.message_handler(commands=['faq', 'preguntas', '❓ FAQ'])
def handle_faq(message):
    """Manejador dinámico de FAQs"""
    # 1. Pedir datos a tu API
    data = get_api_data("api/faqs")
    
    if not data:
        bot.send_message(message.chat.id, "📭 No hay preguntas frecuentes cargadas.")
        return

    response = "❓ <b>PREGUNTAS FRECUENTES</b>\n\n"
    for item in data:
        response += format_faq(item) + "\n"
    
    # Telegram tiene límite de 4096 caracteres, si es muy largo cortamos
    if len(response) > 4000:
        response = response[:4000] + "\n... (hay más preguntas)"
        
    bot.send_message(message.chat.id, response, parse_mode="HTML")

@bot.message_handler(commands=['contacto', 'contactos', '📞 Contactos'])
def handle_contacts(message):
    """Manejador dinámico de Contactos"""
    # 1. Pedir datos a tu API
    data = get_api_data("api/contacts")
    
    if not data:
        bot.send_message(message.chat.id, "📭 No hay contactos disponibles.")
        return

    bot.send_message(message.chat.id, "📞 <b>DIRECTORIO DE CONTACTOS</b>", parse_mode="HTML")
    
    for item in data:
        text = format_contact(item)
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['calendario', '📆 Calendario'])
def handle_calendar(message):
    """Manejador del comando /calendario"""
    calendar_text = """
<b>📆 CALENDARIO ACADÉMICO 2024</b>

<u>Primer Semestre:</u>
📅 Inscripciones: 15 - 30 Enero
📅 Inicio de clases: 5 Febrero
📅 Exámenes parciales: 25 - 29 Marzo
📅 Vacaciones: 1 - 7 Abril
📅 Exámenes finales: 3 - 14 Junio

<u>Segundo Semestre:</u>
📅 Inscripciones: 1 - 15 Julio
📅 Inicio de clases: 22 Julio
📅 Exámenes parciales: 9 - 13 Septiembre
📅 Vacaciones: 16 - 20 Septiembre
📅 Exámenes finales: 18 - 29 Noviembre

<i>Las fechas están sujetas a cambios. Consulta la página oficial: emi.edu.bo .</i>
"""
    
    bot.send_message(message.chat.id, calendar_text, parse_mode="HTML")

@bot.message_handler(commands=['inscripciones'])
def handle_inscriptions(message):
    """Manejador del comando /inscripciones"""
    inscription_text = """
<b>📝 INFORMACIÓN DE INSCRIPCIONES</b>

<u>Requisitos:</u>
• Fotocopia de cédula de identidad
• Título de bachiller (legalizado)
• Certificado de nacimiento
• 4 fotografías tamaño carnet
• Formulario de inscripción completado

<u>Proceso:</u>
1. Recopilar documentos
2. Completar formulario en línea
3. Pagar matrícula en tesorería
4. Entregar documentos en admisiones
5. Asignación de horarios

<u>Costos:</u>
• Matrícula: $150
• Derecho de inscripción: $50
• Seguro estudiantil: $30

<u>Contacto:</u>
📱 Admisiones: 1234-5678
📧 Email: admisiones@emi.edu
🏢 Oficina: Edificio A, Piso 1

<i>Horario de atención para inscripciones: 8:00 - 16:00</i>
"""
    
    bot.send_message(message.chat.id, inscription_text, parse_mode="HTML")

# ========== HANDLERS DE CALLBACK ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('career_'))
def handle_career_callback(call):
    """Manejador para callback de carreras"""
    career_code = call.data.split('_')[1]
    
    if career_code == "more":
        # Lógica para mostrar más carreras
        bot.answer_callback_query(call.id, "Función en desarrollo")
        return
    
    # Obtener datos de todas las carreras
    data = get_api_data("bot/careers")
    
    if not data or 'careers' not in data:
        bot.answer_callback_query(call.id, "Error al obtener información")
        return
    
    # Buscar la carrera específica
    career = next((c for c in data['careers'] if c['code'] == career_code), None)
    
    if not career:
        bot.answer_callback_query(call.id, "Carrera no encontrada")
        return
    
    # Formatear y enviar información
    career_text = format_career(career)
    
    # Agregar botón para más información
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📞 Contactar Admisiones", callback_data=f"contact_adm_{career_code}")
    )
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=career_text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error editando mensaje: {e}")
        # Enviar como nuevo mensaje si falla la edición
        bot.send_message(call.message.chat.id, career_text, parse_mode="HTML")
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('preuni_'))
def handle_preuniversity_callback(call):
    """Manejador para callback de preuniversitarios"""
    data_parts = call.data.split('_')
    
    if len(data_parts) < 2:
        bot.answer_callback_query(call.id, "Error en la solicitud")
        return
    
    program_id = data_parts[1]
    
    if program_id == "all":
        # Mostrar resumen de todos los programas
        show_all_preuniversity(call)
        return
    
    # Obtener datos de programas
    api_data = get_api_data("bot/preuniversity")
    
    if not api_data or 'programs' not in api_data:
        bot.answer_callback_query(call.id, "Error al obtener información")
        return
    
    # Buscar programa específico
    try:
        program_id_int = int(program_id)
        program = next((p for p in api_data['programs'] if p['id'] == program_id_int), None)
    except ValueError:
        program = None
    
    if not program:
        bot.answer_callback_query(call.id, "Programa no encontrado")
        return
    
    # Formatear información
    program_text = format_preuniversity(program)
    
    # Agregar botones de acción
    markup = types.InlineKeyboardMarkup()
    
    if program.get('registration_link'):
        markup.add(
            types.InlineKeyboardButton("📝 Inscribirse en línea", url=program['registration_link'])
        )
    
    markup.add(
        types.InlineKeyboardButton("📞 Contactar", callback_data=f"contact_pre_{program_id}"),
        types.InlineKeyboardButton("↩️ Volver al listado", callback_data="preuni_back")
    )
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=program_text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error editando mensaje preuniversitario: {e}")
        bot.send_message(call.message.chat.id, program_text, parse_mode="HTML")
        bot.answer_callback_query(call.id)

def show_all_preuniversity(call):
    """Mostrar resumen de todos los programas preuniversitarios"""
    data = get_api_data("bot/preuniversity")
    
    if not data or 'programs' not in data or not data['programs']:
        bot.answer_callback_query(call.id, "No hay programas disponibles")
        return
    
    programs = data['programs']
    
    summary_text = "<b>📚 RESUMEN DE PROGRAMAS PREUNIVERSITARIOS</b>\n\n"
    
    for i, program in enumerate(programs, 1):
        summary_text += f"<b>{i}. {program['program_name']}</b>\n"
        
        if program.get('duration'):
            summary_text += f"   ⏳ {program['duration']}"
        
        if program.get('cost'):
            summary_text += f" | 💰 ${program['cost']:,.2f}"
        
        if program.get('start_date'):
            try:
                start_date = datetime.strptime(program['start_date'], '%Y-%m-%d').strftime('%d/%m')
                summary_text += f" | 📅 Inicia: {start_date}"
            except:
                pass
        
        summary_text += "\n\n"
    
    summary_text += "<i>Selecciona un programa del listado anterior para ver detalles completos.</i>"
    
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=summary_text,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error mostrando resumen: {e}")
        bot.send_message(call.message.chat.id, summary_text, parse_mode="HTML")
        bot.answer_callback_query(call.id)

# ========== HANDLER DE MENSAJES DE TEXTO ==========

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Manejador de mensajes de texto"""
    text = message.text.lower().strip()
    logger.info(f"Mensaje de texto de {message.chat.id}: {text}")
    
    # Mapeo de textos a comandos
    text_to_command = {
        'carreras': handle_careers,
        '🎓 Carreras': handle_careers,
        'preuniversitarios': handle_preuniversity,
        'preuniversitario': handle_preuniversity,
        '📚 Preuniversitarios': handle_preuniversity,
        'pre': handle_preuniversity,
        'eventos': handle_events,
        'evento': handle_events,
        '📅 Eventos': handle_events,
        'becas': handle_scholarships,
        'beca': handle_scholarships,
        '💰 Becas': handle_scholarships,
        'faq': handle_faq,
        '❓ FAQ': handle_faq,
        'preguntas': handle_faq,
        'contactos': handle_contacts,
        'contacto': handle_contacts,
        '📞 Contactos': handle_contacts,
        'calendario': handle_calendar,
        '📆 Calendario': handle_calendar,
        'inscripciones': handle_inscriptions,
        'matrícula': handle_inscriptions,
        'ℹ️ Ayuda': handle_help,
        'ayuda': handle_help,
        'hola': handle_start,
        'inicio': handle_start
    }    
    # Buscar handler correspondiente
    handler = text_to_command.get(text)
    
    if handler:
        handler(message)
    else:
        # Respuesta por defecto
        bot.send_message(
            message.chat.id,
            "🤖 <b>Info_EMI</b>\n\n"
            "No entiendo ese mensaje. Puedes usar:\n"
            "• Los comandos (ej: /carreras)\n"
            "• Los botones del teclado\n"
            "• Escribir: 'carreras', 'eventos', 'faq', etc.\n\n"
            "<i>Escribe /help para ver todos los comandos disponibles.</i>",
            parse_mode="HTML"
        )

# ========== FUNCIONES DE MONITOREO ==========

def check_api_health():
    """Verificar salud de la API periódicamente"""
    while True:
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"API saludable: {response.json()}")
            else:
                logger.warning(f"API no responde correctamente: {response.status_code}")
        except Exception as e:
            logger.error(f"Error verificando API: {e}")
        
        time.sleep(300)  # Verificar cada 5 minutos

# ========== INICIALIZACIÓN ==========

def start_bot():
    """Iniciar el bot con manejo de errores"""
    logger.info("=" * 50)
    logger.info("INICIANDO BOT INFO_EMI")
    logger.info(f"Token: {TOKEN[:10]}...")
    logger.info(f"API URL: {API_URL}")
    logger.info("=" * 50)
    
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        logger.warning(f"No se pudo eliminar webhook: {e}")

    # Iniciar thread para monitoreo de API
    health_thread = threading.Thread(target=check_api_health, daemon=True)
    health_thread.start()
    
    # Intentar conexión con reintentos
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Intento {attempt + 1} de {max_retries}...")
            
            # Obtener información del bot
            bot_info = bot.get_me()
            logger.info(f"Bot conectado: @{bot_info.username} ({bot_info.first_name})")
            
            # Iniciar polling
            logger.info("Iniciando polling...")
            bot.polling(none_stop=True, interval=1, timeout=30)
            
            # Si llega aquí, polling se detuvo
            logger.warning("Polling detenido, reiniciando...")
            
        except telebot.apihelper.ApiException as e:
            logger.error(f"Error de API de Telegram: {e}")
            if "Conflict" in str(e):
                logger.error("Otro proceso está usando el bot. Esperando...")
                time.sleep(30)
            else:
                time.sleep(retry_delay)
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión: {e}")
            time.sleep(retry_delay)
        
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            time.sleep(retry_delay)
    
    logger.error("Máximo de reintentos alcanzado. Deteniendo bot.")

if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error crítico: {e}")