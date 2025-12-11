# 🤖 Info EMI - Sistema de Bot Universitario

Sistema completo de bot de Telegram para la Escuela Militar de Ingeniería (EMI) con panel de administración web.

## 🚀 Características

### 🤖 Bot de Telegram (@emicbba_bot)
- Consulta de carreras universitarias
- Información de programas preuniversitarios
- Eventos y actividades
- Preguntas frecuentes (FAQ)
- Contactos por departamento
- Becas y descuentos
- Calendario académico
- Información de inscripciones

### 🛠️ Panel de Administración Web
- Gestión completa de contenidos (CRUD)
- Autenticación segura
- Estadísticas del sistema
- Logs de auditoría
- Interfaz intuitiva y responsive

### 🗄️ Base de Datos PostgreSQL
- Esquema relacional completo
- Datos de ejemplo incluidos
- Backup automático
- Migraciones fáciles

## 📁 Estructura del Proyecto
info-emi-project/
- ├── backend/ # Backend FastAPI
- │ ├── app.py # API principal
- │ ├── bot_worker.py # Bot de Telegram
- │ ├── keep_alive.py # Mantener servicios activos
- │ ├── requirements.txt # Dependencias Python
- │ ├── Procfile # Configuración para Render
- │ ├── runtime.txt # Versión de Python
- │ └── .env # Variables de entorno
- ├── frontend/ # Panel web
- │ ├── panel.html # Interfaz principal
- │ └── static/
- │ └── style.css # Estilos CSS
- ├── database/ # Scripts de BD
- │ ├── init.sql # Esquema y datos iniciales
- │ └── setup_db.py # Configurador de BD local
- ├── scripts/ # Scripts de utilidad
- │ ├── backup.py # Sistema de backup
- │ └── restore.py # Restauración de BD
- └── README.md # Este archivo


## 🛠️ Instalación Local

### Prerrequisitos
1. **Python 3.11+**
2. **PostgreSQL 15+**
3. **Git**