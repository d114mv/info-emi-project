#!/usr/bin/env python3
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent))

import telebot
from telebot import types
import requests
import threading
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "8577123738:AAHI75qOoFWJF34may_LJW6oRC1FlcrkNqA")
API_URL = os.getenv("API_URL", "https://info-emi-backend.onrender.com")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


def format_career(career: dict) -> str:
    text = f"<b>🎓 {career['name']}</b>\n"
    text += f"<code>{career['code']}</code>\n\n"
    
    if career.get('campus'):
        text += f"🏛️ <b>Campus:</b> {career['campus']}\n"
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

def post_api_data(endpoint: str, data: dict):
    try:
        url = f"{API_URL}/{endpoint}"
        response = requests.post(url, json=data, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error conectando a API (POST): {e}")
        return None
    

def format_scholarship(item: dict) -> str:
    text = f"💰 <b>{item['name']}</b>\n"
    if item.get('coverage'):
        text += f"💎 Cobertura: {item['coverage']}\n"
    
    if item.get('description'):
        text += f"\n📝 {item['description']}\n"
    
    if item.get('requirements'):
        text += f"\n📋 <b>Requisitos:</b>\n{item['requirements']}\n"
        
    if item.get('application_link'):
        text += f"\n🔗 <a href='{item['application_link']}'>Link de consulta</a>\n"
        
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
def format_calendar_event(item: dict) -> str:
    text = f"🗓 <b>{item['event_name']}</b>\n"
    
    start = datetime.strptime(item['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
    text += f"📅 {start}"
    
    if item.get('end_date'):
        end = datetime.strptime(item['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        text += f" al {end}"
    
    text += "\n"
    if item.get('event_type'): text += f"📌 Tipo: {item['event_type']}\n"
    if item.get('description'): text += f"📝 {item['description']}\n"
    
    return text

def format_inscription_info(item: dict) -> str:
    text = f"📝 <b>INSCRIPCIONES GESTIÓN {item['period']}</b>\n\n"
    
    start = datetime.strptime(item['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
    end = datetime.strptime(item['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
    text += f"📅 <b>Fechas:</b> {start} al {end}\n\n"
    
    if item.get('requirements'): text += f"📋 <b>Requisitos:</b>\n{item['requirements']}\n\n"
    if item.get('documents_required'): text += f"📂 <b>Documentos:</b>\n{item['documents_required']}\n\n"
    if item.get('costs'): text += f"💰 <b>Costos:</b>\n{item['costs']}\n\n"
    if item.get('process_steps'): text += f"👣 <b>Pasos:</b>\n{item['process_steps']}\n\n"
    if item.get('contact_info'): text += f"📞 <b>Contacto:</b> {item['contact_info']}\n"
    
    return text


@bot.message_handler(commands=['start'])
def handle_start(message):
    logger.info(f"Comando /start de {message.chat.id}")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_carreras = types.KeyboardButton("🎓 Carreras")
    btn_pre = types.KeyboardButton("📚 Preuniversitarios")
    btn_eventos = types.KeyboardButton("📅 Eventos")
    btn_becas = types.KeyboardButton("💰 Becas")
    btn_faq = types.KeyboardButton("❓ FAQ")
    btn_contactos = types.KeyboardButton("📞 Contactos")
    btn_calendario = types.KeyboardButton("📆 Calendario")
    btn_ayuda = types.KeyboardButton("ℹ️ Ayuda")
    
    markup.add(btn_carreras, btn_pre, btn_eventos, btn_becas, 
               btn_faq, btn_contactos, btn_calendario, btn_ayuda)

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
    logger.info(f"Comando /carreras de {message.chat.id}")
    
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
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for career in careers[:10]:
        button_text = f"🎓 {career['code']} - {career['name'][:25]}..."
        callback_data = f"career_{career['code']}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
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
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for program in programs[:8]:
        button_text = f"📚 {program['program_name'][:30]}"
        if len(program['program_name']) > 30:
            button_text += "..."
        callback_data = f"preuni_{program['id']}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
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


@bot.message_handler(commands=['becas', 'beca', '💰 Becas'])
def handle_scholarships(message):
    data = get_api_data("api/scholarships")
    
    if not data:
        bot.send_message(message.chat.id, "📭 No hay becas disponibles por ahora.")
        return

    bot.send_message(message.chat.id, "🎓 <b>BECAS Y DESCUENTOS DISPONIBLES</b>", parse_mode="HTML")
    
    for item in data:
        text = format_scholarship(item)
        bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)

@bot.message_handler(commands=['faq', 'preguntas'])
def handle_faq(message):
    data = get_api_data("api/faqs")
    
    if not data:
        bot.send_message(message.chat.id, "📭 No hay preguntas frecuentes registradas.")
        return

    categories = set()
    for item in data:
        cat = item.get('category')
        if not cat or cat.strip() == "":
            cat = "General"
        categories.add(cat)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    for cat in sorted(list(categories)):
        buttons.append(types.InlineKeyboardButton(
            text=f"📂 {cat}", 
            callback_data=f"faq:{cat}" 
        ))
    
    markup.add(*buttons)

    bot.send_message(
        message.chat.id, 
        "❓ <b>PREGUNTAS FRECUENTES</b>\n\nSelecciona una categoría para ver las preguntas:", 
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.message_handler(commands=['contacto', 'contactos', '📞 Contactos'])
def handle_contacts(message):
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
    data = get_api_data("api/calendar")
    
    if not data:
        bot.send_message(message.chat.id, "📅 No hay eventos programados en el calendario académico.")
        return

    bot.send_message(message.chat.id, "📆 <b>CALENDARIO ACADÉMICO</b>", parse_mode="HTML")
    
    for item in data[:10]:
        text = format_calendar_event(item)
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['inscripciones', 'matrícula'])
def handle_inscriptions(message):
    data = get_api_data("api/inscriptions")
    
    if not data:
        bot.send_message(message.chat.id, "📝 No hay información de inscripciones activa por el momento.")
        return

    current_period = data[0]
    text = format_inscription_info(current_period)
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('career_'))
def handle_career_callback(call):
    career_code = call.data.split('_')[1]
    
    if career_code == "more":
        bot.answer_callback_query(call.id, "Función en desarrollo")
        return
    
    data = get_api_data("bot/careers")
    
    if not data or 'careers' not in data:
        bot.answer_callback_query(call.id, "Error al obtener información")
        return
    
    career = next((c for c in data['careers'] if c['code'] == career_code), None)
    
    if not career:
        bot.answer_callback_query(call.id, "Carrera no encontrada")
        return
    
    career_text = format_career(career)
    
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
        bot.send_message(call.message.chat.id, career_text, parse_mode="HTML")
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('preuni_'))
def handle_preuniversity_callback(call):
    data_parts = call.data.split('_')
    
    if len(data_parts) < 2:
        bot.answer_callback_query(call.id, "Error en la solicitud")
        return
    
    program_id = data_parts[1]
    
    if program_id == "all":
        show_all_preuniversity(call)
        return
    
    api_data = get_api_data("bot/preuniversity")
    
    if not api_data or 'programs' not in api_data:
        bot.answer_callback_query(call.id, "Error al obtener información")
        return
    
    try:
        program_id_int = int(program_id)
        program = next((p for p in api_data['programs'] if p['id'] == program_id_int), None)
    except ValueError:
        program = None
    
    if not program:
        bot.answer_callback_query(call.id, "Programa no encontrado")
        return
    
    program_text = format_preuniversity(program)
    
    markup = types.InlineKeyboardMarkup()
    
    if program.get('registration_link'):
        markup.add(
            types.InlineKeyboardButton("📝 Inscribirse en línea", url=program['registration_link'])
        )
    
    markup.add(
        types.InlineKeyboardButton("📞 Contactar", callback_data=f"contact_pre_{program_id}"),
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


@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    text = message.text.lower().strip()
    logger.info(f"Mensaje de texto de {message.chat.id}: {text}")
    
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
    
    handler = text_to_command.get(text)
    
    if handler:
        handler(message)
    else:

        bot.send_chat_action(message.chat.id, 'typing')
        
        response = post_api_data("bot/ask", {"question": message.text})
        
        if response and 'answer' in response:
            bot.reply_to(message, response['answer'])
        else:
            bot.send_message(
                message.chat.id,
                "🤖 Estoy teniendo problemas para pensar ahora mismo. Intenta usar los comandos /help."
            )

def check_api_health():
    while True:
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                logger.info(f"API saludable: {response.json()}")
            else:
                logger.warning(f"API no responde correctamente: {response.status_code}")
        except Exception as e:
            logger.error(f"Error verificando API: {e}")
        
        time.sleep(300)


def start_bot():
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

    health_thread = threading.Thread(target=check_api_health, daemon=True)
    health_thread.start()
    
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Intento {attempt + 1} de {max_retries}...")
            
            bot_info = bot.get_me()
            logger.info(f"Bot conectado: @{bot_info.username} ({bot_info.first_name})")
            
            logger.info("Iniciando polling...")
            bot.polling(none_stop=True, interval=1, timeout=30)
            
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

@bot.callback_query_handler(func=lambda call: call.data.startswith('faq:'))
def handle_faq_click(call):
    """Maneja el clic en una categoría de FAQ"""
    try:
        category_selected = call.data.split(':', 1)[1]
        
        data = get_api_data("api/faqs")
        
        if not data:
            bot.answer_callback_query(call.id, "No se pudo cargar la información.")
            return

        filtered_questions = []
        for item in data:
            item_cat = item.get('category')
            if not item_cat or item_cat.strip() == "":
                item_cat = "General"
            
            if item_cat == category_selected:
                filtered_questions.append(item)
        
        text = f"📂 <b>CATEGORÍA: {category_selected.upper()}</b>\n\n"
        
        filtered_questions.sort(key=lambda x: x.get('priority', 99))
        
        for item in filtered_questions:
            text += f"🔹 <b>{item['question']}</b>\n"
            text += f"💡 <i>{item['answer']}</i>\n\n"
            
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Error en callback FAQ: {e}")
        bot.answer_callback_query(call.id, "Ocurrió un error al cargar.")

if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error crítico: {e}")