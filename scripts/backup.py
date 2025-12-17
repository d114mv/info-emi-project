#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import zipfile
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseBackup:
    """Clase para manejar backups de base de datos"""
    
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL no configurada")
        
        self.parse_db_url()
        
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))
        
        self.email_enabled = os.getenv('EMAIL_NOTIFICATIONS', 'False').lower() == 'true'
        if self.email_enabled:
            self.setup_email_config()
    
    def parse_db_url(self):
        import re
        
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, self.db_url)
        
        if not match:
            raise ValueError(f"URL de base de datos inválida: {self.db_url}")
        
        self.db_user = match.group(1)
        self.db_password = match.group(2)
        self.db_host = match.group(3)
        self.db_port = match.group(4)
        self.db_name = match.group(5)
        
        logger.info(f"Configurada conexión a: {self.db_host}:{self.db_port}/{self.db_name}")
    
    def setup_email_config(self):
        """Configurar parámetros de email"""
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.email_from = os.getenv('EMAIL_FROM')
        self.email_to = os.getenv('EMAIL_TO', '').split(',')
        
        missing = []
        for var in ['SMTP_SERVER', 'SMTP_USER', 'SMTP_PASSWORD', 'EMAIL_FROM', 'EMAIL_TO']:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            logger.warning(f"Configuración de email incompleta, faltan: {missing}")
            self.email_enabled = False
    
    def create_backup(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"info_emi_backup_{timestamp}.sql"
        backup_zip = self.backup_dir / f"info_emi_backup_{timestamp}.zip"
        
        logger.info(f"Creando backup: {backup_file}")
        
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            cmd = [
                'pg_dump',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-F', 'c',
                '-f', str(backup_file)
            ]
            
            logger.debug(f"Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error en pg_dump: {result.stderr}")
                return None
            
            logger.info(f"Backup creado exitosamente: {backup_file.stat().st_size / 1024:.1f} KB")
            
            self.compress_backup(backup_file, backup_zip)
            
            backup_file.unlink()
            
            return backup_zip
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return None
    
    def compress_backup(self, source_file, dest_zip):
        try:
            with zipfile.ZipFile(dest_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(source_file, source_file.name)
            
            logger.info(f"Backup comprimido: {dest_zip.stat().st_size / 1024:.1f} KB")
            
        except Exception as e:
            logger.error(f"Error comprimiendo backup: {e}")
            raise
    
    def cleanup_old_backups(self):
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted = 0
        
        logger.info(f"Limpiando backups más antiguos de {self.retention_days} días")
        
        for backup_file in self.backup_dir.glob('info_emi_backup_*.zip'):
            try:
                date_str = backup_file.stem.replace('info_emi_backup_', '')
                file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Eliminado backup antiguo: {backup_file.name}")
                    deleted += 1
                    
            except ValueError:
                continue
        
        logger.info(f"Eliminados {deleted} backups antiguos")
    
    def send_email_notification(self, backup_file, success=True):
        if not self.email_enabled:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            
            if success:
                msg['Subject'] = f'✅ Backup exitoso - Info EMI - {datetime.now().strftime("%Y-%m-%d")}'
                body = f"""
                <html>
                <body>
                    <h2>Backup exitoso - Sistema Info EMI</h2>
                    <p>Se ha creado un nuevo backup de la base de datos.</p>
                    <ul>
                        <li><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li><strong>Archivo:</strong> {backup_file.name}</li>
                        <li><strong>Tamaño:</strong> {backup_file.stat().st_size / 1024:.1f} KB</li>
                        <li><strong>Base de datos:</strong> {self.db_name}</li>
                    </ul>
                    <p>Este es un mensaje automático del sistema de backup.</p>
                </body>
                </html>
                """
            else:
                msg['Subject'] = f'❌ Error en backup - Info EMI - {datetime.now().strftime("%Y-%m-%d")}'
                body = f"""
                <html>
                <body>
                    <h2>Error en backup - Sistema Info EMI</h2>
                    <p>Ha ocurrido un error al intentar crear el backup de la base de datos.</p>
                    <p>Por favor, revisa los logs del sistema.</p>
                    <p><strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Este es un mensaje automático del sistema de backup.</p>
                </body>
                </html>
                """
            
            msg.attach(MIMEText(body, 'html'))
            
            if success and backup_file:
                with open(backup_file, 'rb') as f:
                    part = MIMEBase('application', 'zip')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{backup_file.name}"'
                    )
                    msg.attach(part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Notificación enviada a {len(self.email_to)} destinatarios")
            
        except Exception as e:
            logger.error(f"Error enviando notificación por email: {e}")
    
    def verify_backup(self, backup_file):
        try:
            if not backup_file.exists():
                logger.error(f"Archivo de backup no encontrado: {backup_file}")
                return False
            
            if backup_file.stat().st_size == 0:
                logger.error(f"Archivo de backup vacío: {backup_file}")
                return False
            
            if zipfile.is_zipfile(backup_file):
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if zipf.testzip() is None:
                        logger.info("Backup verificado exitosamente")
                        return True
                    else:
                        logger.error("Backup corrupto")
                        return False
            else:
                logger.error("El archivo no es un ZIP válido")
                return False
                
        except Exception as e:
            logger.error(f"Error verificando backup: {e}")
            return False
    
    def run_full_backup(self):
        logger.info("=" * 50)
        logger.info("INICIANDO PROCESO DE BACKUP")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        
        try:
            backup_file = self.create_backup()
            
            if not backup_file:
                logger.error("Falló la creación del backup")
                if self.email_enabled:
                    self.send_email_notification(None, success=False)
                return False
            
            if not self.verify_backup(backup_file):
                logger.error("Backup no verificado")
                backup_file.unlink()
                if self.email_enabled:
                    self.send_email_notification(None, success=False)
                return False
            
            self.cleanup_old_backups()
            
            if self.email_enabled:
                self.send_email_notification(backup_file, success=True)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 50)
            logger.info("BACKUP COMPLETADO EXITOSAMENTE")
            logger.info("=" * 50)
            logger.info(f"Archivo: {backup_file.name}")
            logger.info(f"Tamaño: {backup_file.stat().st_size / 1024:.1f} KB")
            logger.info(f"Duración: {duration:.1f} segundos")
            logger.info(f"Ubicación: {backup_file.absolute()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en proceso de backup: {e}")
            if self.email_enabled:
                self.send_email_notification(None, success=False)
            return False
    
    def list_backups(self):
        backups = list(self.backup_dir.glob('info_emi_backup_*.zip'))
        
        if not backups:
            print("No hay backups disponibles")
            return
        
        print(f"\n📦 BACKUPS DISPONIBLES ({len(backups)}):")
        print("-" * 80)
        print(f"{'No.':<4} {'Fecha':<20} {'Tamaño':<12} {'Archivo'}")
        print("-" * 80)
        
        for i, backup in enumerate(sorted(backups, reverse=True), 1):
            try:
                date_str = backup.stem.replace('info_emi_backup_', '')
                file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                date_formatted = file_date.strftime('%Y-%m-%d %H:%M')
                size_kb = backup.stat().st_size / 1024
                
                print(f"{i:<4} {date_formatted:<20} {size_kb:>8.1f} KB  {backup.name}")
            except:
                print(f"{i:<4} {'Fecha desconocida':<20} {'?':>8} KB  {backup.name}")
        
        print("-" * 80)
    
    def restore_backup(self, backup_number=None, backup_file=None):
        if not backup_file:
            backups = list(self.backup_dir.glob('info_emi_backup_*.zip'))
            
            if not backups:
                logger.error("No hay backups disponibles para restaurar")
                return False
            
            if backup_number is None:
                self.list_backups()
                try:
                    backup_number = int(input("\nNúmero del backup a restaurar: "))
                except ValueError:
                    logger.error("Número inválido")
                    return False
            
            sorted_backups = sorted(backups, reverse=True)
            
            if backup_number < 1 or backup_number > len(sorted_backups):
                logger.error("Número de backup inválido")
                return False
            
            backup_file = sorted_backups[backup_number - 1]
        
        logger.warning(f"⚠️  ADVERTENCIA: Esto sobrescribirá la base de datos actual")
        logger.warning(f"Base de datos: {self.db_name}")
        logger.warning(f"Backup a restaurar: {backup_file.name}")
        
        confirm = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
        if confirm.upper() != 'SI':
            logger.info("Restauración cancelada")
            return False
        
        logger.info(f"Iniciando restauración desde: {backup_file.name}")
        
        try:
            temp_dir = Path('temp_restore')
            temp_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                sql_files = [f for f in zipf.namelist() if f.endswith('.sql')]
                if not sql_files:
                    logger.error("No se encontró archivo SQL en el backup")
                    return False
                
                sql_file = sql_files[0]
                zipf.extract(sql_file, temp_dir)
                extracted_file = temp_dir / sql_file
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            cmd = [
                'pg_restore',
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '--clean',
                '--if-exists',
                '--no-owner',
                '--no-privileges',
                str(extracted_file)
            ]
            
            logger.debug(f"Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            shutil.rmtree(temp_dir)
            
            if result.returncode != 0:
                logger.error(f"Error en pg_restore: {result.stderr}")
                return False
            
            logger.info("✅ Base de datos restaurada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de backup para Info EMI')
    parser.add_argument('action', choices=['backup', 'list', 'restore', 'cleanup'],
                       help='Acción a ejecutar')
    parser.add_argument('--number', type=int, 
                       help='Número de backup para restaurar (solo para restore)')
    parser.add_argument('--file', type=str,
                       help='Archivo de backup específico (solo para restore)')
    parser.add_argument('--retention', type=int, default=7,
                       help='Días de retención para backups (default: 7)')
    
    args = parser.parse_args()
    
    try:
        backup_system = DatabaseBackup()
        backup_system.retention_days = args.retention
        
        if args.action == 'backup':
            success = backup_system.run_full_backup()
            sys.exit(0 if success else 1)
            
        elif args.action == 'list':
            backup_system.list_backups()
            
        elif args.action == 'restore':
            backup_system.restore_backup(args.number, args.file)
            
        elif args.action == 'cleanup':
            backup_system.cleanup_old_backups()
            
    except Exception as e:
        logger.error(f"Error en sistema de backup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()