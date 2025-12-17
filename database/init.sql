-- 1. Tabla de administradores
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'admin',
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE admins IS 'Administradores del sistema';
COMMENT ON COLUMN admins.password_hash IS 'Hash SHA256 de la contraseña';

-- 2. Tabla de carreras
CREATE TABLE IF NOT EXISTS careers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    campus VARCHAR(100),
    duration VARCHAR(50),
    modality VARCHAR(50),
    description TEXT,
    requirements TEXT,
    cost DECIMAL(10,2),
    curriculum_link VARCHAR(500),
    career_coordinator VARCHAR(100),
    coordinator_email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE careers IS 'Carreras universitarias ofertadas';
COMMENT ON COLUMN careers.modality IS 'Presencial, Virtual, Semipresencial, Híbrida';

-- 3. Tabla de programas preuniversitarios
CREATE TABLE IF NOT EXISTS pre_university (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    duration VARCHAR(50),
    schedule TEXT,
    start_date DATE,
    end_date DATE,
    cost DECIMAL(10,2),
    requirements TEXT,
    registration_link VARCHAR(500),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pre_university IS 'Programas preuniversitarios y cursos de nivelación';

-- 4. Tabla de eventos
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    event_type VARCHAR(50),
    description TEXT,
    date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(200),
    organizer VARCHAR(100),
    registration_link VARCHAR(500),
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE events IS 'Eventos y actividades universitarias';
COMMENT ON COLUMN events.event_type IS 'academico, cultural, deportivo, conferencia, taller, otros';

-- 5. Tabla de preguntas frecuentes
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50),
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE faqs IS 'Preguntas frecuentes';
COMMENT ON COLUMN faqs.category IS 'academico, administrativo, becas, inscripciones, otros';

-- 6. Tabla de contactos
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    department VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(100),
    office VARCHAR(100),
    schedule TEXT,
    responsible VARCHAR(100),
    extension VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE contacts IS 'Contactos y departamentos de la universidad';

-- 7. Tabla de becas
CREATE TABLE IF NOT EXISTS scholarships (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    requirements TEXT,
    coverage VARCHAR(100),
    amount DECIMAL(10,2),
    deadline DATE,
    application_link VARCHAR(500),
    contact_info TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE scholarships IS 'Becas y descuentos disponibles';
COMMENT ON COLUMN scholarships.coverage IS 'parcial, total, porcentaje';

-- 8. Tabla de calendario académico
CREATE TABLE IF NOT EXISTS academic_calendar (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR(200) NOT NULL,
    event_type VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    academic_period VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE academic_calendar IS 'Fechas importantes del calendario académico';
COMMENT ON COLUMN academic_calendar.event_type IS 'inscripcion, clases, examen, vacaciones, feriado, otros';

-- 9. Tabla de inscripciones (información general)
CREATE TABLE IF NOT EXISTS inscriptions (
    id SERIAL PRIMARY KEY,
    period VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    requirements TEXT NOT NULL,
    process_steps TEXT,
    costs TEXT,
    documents_required TEXT,
    contact_info TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE inscriptions IS 'Información general sobre inscripciones';

-- 10. Tabla de logs de auditoría
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    changes JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE audit_logs IS 'Registro de auditoría de todas las acciones en el sistema';

-- 11. Tabla de configuraciones del sistema
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE system_config IS 'Configuraciones del sistema';

-- ============================================
-- ÍNDICES PARA MEJOR RENDIMIENTO
-- ============================================

-- Índices para careers
CREATE INDEX idx_careers_active ON careers(is_active);
CREATE INDEX idx_careers_faculty ON careers(faculty);
CREATE INDEX idx_careers_modality ON careers(modality);

-- Índices para pre_university
CREATE INDEX idx_pre_university_active ON pre_university(is_active);
CREATE INDEX idx_pre_university_dates ON pre_university(start_date, end_date);

-- Índices para events
CREATE INDEX idx_events_date ON events(date);
CREATE INDEX idx_events_active ON events(is_active);
CREATE INDEX idx_events_type ON events(event_type);

-- Índices para faqs
CREATE INDEX idx_faqs_category ON faqs(category);
CREATE INDEX idx_faqs_active ON faqs(is_active);
CREATE INDEX idx_faqs_priority ON faqs(priority);

-- Índices para contacts
CREATE INDEX idx_contacts_department ON contacts(department);
CREATE INDEX idx_contacts_active ON contacts(is_active);
CREATE INDEX idx_contacts_priority ON contacts(priority);

-- Índices para scholarships
CREATE INDEX idx_scholarships_deadline ON scholarships(deadline);
CREATE INDEX idx_scholarships_active ON scholarships(is_active);

-- Índices para academic_calendar
CREATE INDEX idx_academic_calendar_period ON academic_calendar(academic_period);
CREATE INDEX idx_academic_calendar_dates ON academic_calendar(start_date, end_date);

-- Índices para inscriptions
CREATE INDEX idx_inscriptions_period ON inscriptions(period);
CREATE INDEX idx_inscriptions_dates ON inscriptions(start_date, end_date);

-- Índice para audit_logs
CREATE INDEX idx_audit_logs_admin ON audit_logs(admin_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Administrador por defecto (contraseña: admin123)
INSERT INTO admins (username, password_hash, full_name, email, role) 
VALUES (
    'admin', 
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', -- SHA256 de 'admin123'
    'Administrador Principal', 
    'admin@emi.edu', 
    'superadmin'
) ON CONFLICT (username) DO NOTHING;

-- Configuraciones del sistema
INSERT INTO system_config (config_key, config_value, description, is_public) VALUES
(
    'university_name',
    'Escuela Militar de Ingeniería - EMI',
    'Nombre oficial de la universidad',
    TRUE
),
(
    'university_address',
    'Calle Lanza entre Oruro y La Paz Cochabamba, Bolivia',
    'Dirección de la universidad',
    TRUE
),
(
    'university_phone',
    '(+591) 71420764',
    'Teléfono principal',
    TRUE
),
(
    'bot_welcome_message',
    '¡Hola! Soy Info_EMI, tu asistente virtual de la universidad. ¿En qué puedo ayudarte?',
    'Mensaje de bienvenida del bot',
    TRUE
),
(
    'maintenance_mode',
    'false',
    'Modo mantenimiento del sistema',
    FALSE
),
(
    'api_rate_limit',
    '100',
    'Límite de solicitudes por hora por IP',
    FALSE
)
ON CONFLICT (config_key) DO UPDATE 
SET config_value = EXCLUDED.config_value,
    description = EXCLUDED.description,
    is_public = EXCLUDED.is_public;

-- ============================================
-- FUNCIONES Y TRIGGERS
-- ============================================

-- Función para actualizar timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar updated_at automáticamente
CREATE TRIGGER update_admins_updated_at 
    BEFORE UPDATE ON admins 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_careers_updated_at 
    BEFORE UPDATE ON careers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pre_university_updated_at 
    BEFORE UPDATE ON pre_university 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at 
    BEFORE UPDATE ON contacts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scholarships_updated_at 
    BEFORE UPDATE ON scholarships 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_academic_calendar_updated_at 
    BEFORE UPDATE ON academic_calendar 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inscriptions_updated_at 
    BEFORE UPDATE ON inscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at 
    BEFORE UPDATE ON system_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista para eventos próximos (próximos 30 días)
CREATE OR REPLACE VIEW upcoming_events AS
SELECT 
    id,
    title,
    event_type,
    date,
    start_time,
    end_time,
    location,
    organizer
FROM events 
WHERE date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
AND is_active = TRUE
ORDER BY date, start_time;

-- Vista para programas preuniversitarios activos
CREATE OR REPLACE VIEW active_preuniversity AS
SELECT 
    id,
    program_name,
    duration,
    start_date,
    end_date,
    cost,
    contact_phone,
    contact_email
FROM pre_university 
WHERE is_active = TRUE 
AND (end_date IS NULL OR end_date >= CURRENT_DATE)
ORDER BY start_date NULLS FIRST;

-- Vista para estadísticas generales
CREATE OR REPLACE VIEW system_stats AS
SELECT 
    (SELECT COUNT(*) FROM careers WHERE is_active = TRUE) as active_careers,
    (SELECT COUNT(*) FROM pre_university WHERE is_active = TRUE) as active_preuniversity,
    (SELECT COUNT(*) FROM events WHERE is_active = TRUE AND date >= CURRENT_DATE) as upcoming_events,
    (SELECT COUNT(*) FROM faqs WHERE is_active = TRUE) as active_faqs,
    (SELECT COUNT(*) FROM contacts WHERE is_active = TRUE) as active_contacts,
    (SELECT COUNT(*) FROM scholarships WHERE is_active = TRUE) as active_scholarships;

-- ============================================
-- VERIFICACIÓN FINAL
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'BASE DE DATOS INICIALIZADA CORRECTAMENTE';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Tablas creadas: 11';
    RAISE NOTICE 'Administrador por defecto: admin / admin123';
    RAISE NOTICE '============================================';
END $$;