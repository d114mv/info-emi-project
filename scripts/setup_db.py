#!/usr/bin/env python3
"""
Script para configurar la base de datos PostgreSQL local
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from pathlib import Path
import getpass
import hashlib

def read_sql_file(filepath):
    """Leer archivo SQL"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error leyendo archivo SQL: {e}")
        sys.exit(1)

def get_db_connection(dbname=None):
    """Establecer conexión a PostgreSQL"""
    # Parámetros de conexión por defecto
    params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': None,
        'dbname': dbname
    }
    
    # Intentar obtener de variables de entorno
    if not params['password']:
        params['password'] = os.getenv('PGPASSWORD')
    
    if not params['user']:
        params['user'] = os.getenv('PGUSER', 'postgres')
    
    if not params['host']:
        params['host'] = os.getenv('PGHOST', 'localhost')
    
    if not params['port']:
        params['port'] = os.getenv('PGPORT', 5432)
    
    # Solicitar contraseña si no está configurada
    if not params['password']:
        params['password'] = getpass.getpass(f"Contraseña para PostgreSQL ({params['user']}): ")
    
    try:
        conn = psycopg2.connect(**{k: v for k, v in params.items() if v is not None})
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        print("\nSolución de problemas:")
        print("1. Verifica que PostgreSQL esté instalado y ejecutándose")
        print("2. Verifica usuario y contraseña")
        print("3. Verifica que el puerto 5432 esté disponible")
        sys.exit(1)

def create_database():
    """Crear base de datos si no existe"""
    print("🔧 Creando base de datos 'info_emi'...")
    
    # Conectar a postgres database
    conn = get_db_connection('postgres')
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        # Verificar si la base de datos existe
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'info_emi'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(sql.SQL("CREATE DATABASE info_emi"))
            print("✅ Base de datos creada exitosamente")
        else:
            print("ℹ️ La base de datos ya existe")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creando base de datos: {e}")
        sys.exit(1)

def execute_sql_script():
    """Ejecutar script SQL de inicialización"""
    print("📄 Ejecutando script de inicialización...")
    
    # Leer archivo SQL
    script_path = Path(__file__).parent / 'init.sql'
    sql_script = read_sql_file(script_path)
    
    # Conectar a la base de datos creada
    conn = get_db_connection('info_emi')
    conn.autocommit = False
    cur = conn.cursor()
    
    try:
        # Ejecutar script completo
        cur.execute(sql_script)
        conn.commit()
        
        print("✅ Script SQL ejecutado exitosamente")
        
        # Mostrar resumen
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM careers) as careers_count,
                (SELECT COUNT(*) FROM pre_university) as preuniversity_count,
                (SELECT COUNT(*) FROM events) as events_count,
                (SELECT COUNT(*) FROM faqs) as faqs_count,
                (SELECT COUNT(*) FROM admins) as admins_count
        """)
        
        stats = cur.fetchone()
        
        print("\n📊 RESUMEN DE DATOS CARGADOS:")
        print(f"   • Carreras: {stats[0]}")
        print(f"   • Programas preuniversitarios: {stats[1]}")
        print(f"   • Eventos: {stats[2]}")
        print(f"   • FAQs: {stats[3]}")
        print(f"   • Administradores: {stats[4]}")
        
        # Mostrar credenciales de administrador
        cur.execute("SELECT username FROM admins LIMIT 1")
        admin_user = cur.fetchone()
        
        print("\n🔐 CREDENCIALES POR DEFECTO:")
        print(f"   • Usuario: {admin_user[0]}")
        print(f"   • Contraseña: admin123")
        print("\n⚠️  IMPORTANTE: Cambia la contraseña después del primer login!")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Error ejecutando script SQL: {e}")
        sys.exit(1)

def create_user():
    """Crear usuario específico para la aplicación"""
    print("\n👤 Creando usuario de aplicación...")
    
    conn = get_db_connection('info_emi')
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        # Crear usuario si no existe
        app_user = 'info_emi_user'
        app_password = 'SecurePass123!'  # Cambiar en producción
        
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (app_user,))
        user_exists = cur.fetchone()
        
        if not user_exists:
            # Crear usuario con contraseña
            cur.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                sql.Identifier(app_user)
            ), (app_password,))
            
            # Otorgar privilegios
            cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier('info_emi'),
                sql.Identifier(app_user)
            ))
            
            # Otorgar permisos en esquema público
            cur.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO %s", (app_user,))
            cur.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO %s", (app_user,))
            
            print(f"✅ Usuario '{app_user}' creado exitosamente")
            print(f"   • Contraseña: {app_password}")
        else:
            print(f"ℹ️ El usuario '{app_user}' ya existe")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creando usuario: {e}")

def update_env_file():
    """Actualizar archivo .env con la configuración de la BD"""
    print("\n⚙️ Actualizando archivo .env...")
    
    env_path = Path(__file__).parent.parent / 'backend' / '.env'
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Actualizar DATABASE_URL
        new_db_url = "DATABASE_URL=postgresql://info_emi_user:SecurePass123!@localhost:5432/info_emi"
        
        if 'DATABASE_URL=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('DATABASE_URL='):
                    lines[i] = new_db_url
                    break
            content = '\n'.join(lines)
        else:
            content += f"\n{new_db_url}\n"
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Archivo .env actualizado exitosamente")
        print(f"   • Ruta: {env_path}")
        
    except Exception as e:
        print(f"⚠️ No se pudo actualizar .env: {e}")
        print("   Puedes configurar manualmente:")
        print("   DATABASE_URL=postgresql://info_emi_user:SecurePass123!@localhost:5432/info_emi")

def generate_password_hash(password):
    """Generar hash SHA256 para contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def change_admin_password():
    """Cambiar contraseña del administrador"""
    print("\n🔐 ¿Deseas cambiar la contraseña del administrador? (s/n): ", end='')
    response = input().lower()
    
    if response == 's':
        new_password = getpass.getpass("Nueva contraseña para admin: ")
        confirm_password = getpass.getpass("Confirmar contraseña: ")
        
        if new_password != confirm_password:
            print("❌ Las contraseñas no coinciden")
            return
        
        if len(new_password) < 6:
            print("⚠️  La contraseña debe tener al menos 6 caracteres")
        
        password_hash = generate_password_hash(new_password)
        
        conn = get_db_connection('info_emi')
        cur = conn.cursor()
        
        try:
            cur.execute("UPDATE admins SET password_hash = %s WHERE username = 'admin'", (password_hash,))
            conn.commit()
            print("✅ Contraseña del administrador actualizada exitosamente")
            
            # Mostrar nuevo hash para archivo .env
            print(f"\n🔧 Si usas Render, actualiza esta variable de entorno:")
            print(f"   ADMIN_PASSWORD_HASH={password_hash}")
            
        except Exception as e:
            print(f"❌ Error actualizando contraseña: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()

def main():
    """Función principal"""
    print("=" * 50)
    print("CONFIGURADOR DE BASE DE DATOS - INFO EMI")
    print("=" * 50)
    
    # Verificar que PostgreSQL esté instalado
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 no está instalado")
        print("   Ejecuta: pip install psycopg2-binary")
        sys.exit(1)
    
    # Verificar archivo init.sql
    init_file = Path(__file__).parent / 'init.sql'
    if not init_file.exists():
        print(f"❌ Archivo init.sql no encontrado en: {init_file}")
        sys.exit(1)
    
    print(f"\n📁 Script SQL encontrado: {init_file}")
    
    # Ejecutar pasos
    try:
        create_database()
        execute_sql_script()
        create_user()
        update_env_file()
        change_admin_password()
        
        print("\n" + "=" * 50)
        print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 50)
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Verifica que el backend pueda conectarse a la BD")
        print("2. Ejecuta el backend: python backend/app.py")
        print("3. Ejecuta el bot: python backend/bot_worker.py")
        print("4. Accede al panel en: http://localhost:8000/panel")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Proceso cancelado por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()