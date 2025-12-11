"""
Script para mantener activos los servicios gratuitos
"""
import os
import time
import requests
from datetime import datetime
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs a mantener activas
SERVICES = [
    os.getenv("API_URL", "http://localhost:8000"),
    "https://api.telegram.org"
]

def ping_service(url):
    """Hacer ping a un servicio"""
    try:
        start_time = time.time()
        
        if "/health" in url or "localhost" in url or "127.0.0.1" in url:
            response = requests.get(url, timeout=10)
        else:
            # Para URLs externas, usar HEAD para menos carga
            response = requests.head(url, timeout=10)
        
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code < 400:
            logger.info(f"✅ {url} - {response.status_code} ({elapsed:.0f}ms)")
            return True
        else:
            logger.warning(f"⚠️ {url} - {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ {url} - Timeout")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 {url} - Connection Error")
        return False
    except Exception as e:
        logger.error(f"❌ {url} - Error: {str(e)[:50]}")
        return False

def keep_alive_loop():
    """Loop principal para mantener servicios activos"""
    logger.info("🚀 Iniciando servicio keep-alive")
    
    while True:
        try:
            logger.info(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("📡 Realizando ping a servicios...")
            
            for service in SERVICES:
                if service:  # Verificar que no sea None o vacío
                    ping_service(service)
            
            # Render Free se duerme después de 30 minutos de inactividad
            # Hacemos ping cada 25 minutos para mantener activo
            logger.info(f"⏳ Esperando 25 minutos para próximo ping...")
            time.sleep(1500)  # 25 minutos
            
        except KeyboardInterrupt:
            logger.info("🛑 Servicio keep-alive detenido")
            break
        except Exception as e:
            logger.error(f"🔥 Error en keep-alive: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # También podemos iniciar un thread para esto si se ejecuta desde el worker
    keep_alive_loop()