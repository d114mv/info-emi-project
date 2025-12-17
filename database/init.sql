--
-- PostgreSQL database dump
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO info_emi_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: academic_calendar; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.academic_calendar (
    id integer NOT NULL,
    event_name character varying(200) NOT NULL,
    event_type character varying(50),
    start_date date NOT NULL,
    end_date date,
    description text,
    academic_period character varying(50),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.academic_calendar OWNER TO info_emi_user;

--
-- Name: TABLE academic_calendar; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.academic_calendar IS 'Fechas importantes del calendario académico';


--
-- Name: COLUMN academic_calendar.event_type; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON COLUMN public.academic_calendar.event_type IS 'inscripcion, clases, examen, vacaciones, feriado, otros';


--
-- Name: academic_calendar_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.academic_calendar_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.academic_calendar_id_seq OWNER TO info_emi_user;

--
-- Name: academic_calendar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.academic_calendar_id_seq OWNED BY public.academic_calendar.id;


--
-- Name: pre_university; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.pre_university (
    id integer NOT NULL,
    program_name character varying(200) NOT NULL,
    description text NOT NULL,
    duration character varying(50),
    schedule text,
    start_date date,
    end_date date,
    cost numeric(10,2),
    requirements text,
    registration_link character varying(500),
    contact_email character varying(100),
    contact_phone character varying(50),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.pre_university OWNER TO info_emi_user;

--
-- Name: TABLE pre_university; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.pre_university IS 'Programas preuniversitarios y cursos de nivelación';


--
-- Name: active_preuniversity; Type: VIEW; Schema: public; Owner: info_emi_user
--

CREATE VIEW public.active_preuniversity AS
 SELECT id,
    program_name,
    duration,
    start_date,
    end_date,
    cost,
    contact_phone,
    contact_email
   FROM public.pre_university
  WHERE ((is_active = true) AND ((end_date IS NULL) OR (end_date >= CURRENT_DATE)))
  ORDER BY start_date NULLS FIRST;


ALTER VIEW public.active_preuniversity OWNER TO info_emi_user;

--
-- Name: admins; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.admins (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(100),
    email character varying(100),
    role character varying(20) DEFAULT 'admin'::character varying,
    last_login timestamp without time zone,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.admins OWNER TO info_emi_user;

--
-- Name: TABLE admins; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.admins IS 'Administradores del sistema';


--
-- Name: COLUMN admins.password_hash; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON COLUMN public.admins.password_hash IS 'Hash SHA256 de la contraseña';


--
-- Name: admins_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.admins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admins_id_seq OWNER TO info_emi_user;

--
-- Name: admins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.admins_id_seq OWNED BY public.admins.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    admin_id integer,
    action character varying(50) NOT NULL,
    table_name character varying(50),
    record_id integer,
    changes jsonb,
    ip_address character varying(50),
    user_agent text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.audit_logs OWNER TO info_emi_user;

--
-- Name: TABLE audit_logs; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.audit_logs IS 'Registro de auditoría de todas las acciones en el sistema';


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO info_emi_user;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: careers; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.careers (
    id integer NOT NULL,
    code character varying(20) NOT NULL,
    name character varying(200) NOT NULL,
    campus character varying(100),
    duration character varying(50),
    modality character varying(50),
    description text,
    requirements text,
    curriculum_link character varying(500),
    career_coordinator character varying(100),
    coordinator_email character varying(100),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.careers OWNER TO info_emi_user;

--
-- Name: TABLE careers; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.careers IS 'Carreras universitarias ofertadas';


--
-- Name: COLUMN careers.modality; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON COLUMN public.careers.modality IS 'Presencial, Virtual, Semipresencial, Híbrida';


--
-- Name: careers_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.careers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.careers_id_seq OWNER TO info_emi_user;

--
-- Name: careers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.careers_id_seq OWNED BY public.careers.id;


--
-- Name: contacts; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.contacts (
    id integer NOT NULL,
    department character varying(100) NOT NULL,
    phone character varying(50),
    email character varying(100),
    office character varying(100),
    schedule text,
    responsible character varying(100),
    extension character varying(20),
    is_active boolean DEFAULT true,
    priority integer DEFAULT 1,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.contacts OWNER TO info_emi_user;

--
-- Name: TABLE contacts; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.contacts IS 'Contactos y departamentos de la universidad';


--
-- Name: contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contacts_id_seq OWNER TO info_emi_user;

--
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- Name: events; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.events (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    event_type character varying(50),
    description text,
    date date NOT NULL,
    start_time time without time zone,
    end_time time without time zone,
    location character varying(200),
    organizer character varying(100),
    registration_link character varying(500),
    max_participants integer,
    current_participants integer DEFAULT 0,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.events OWNER TO info_emi_user;

--
-- Name: TABLE events; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.events IS 'Eventos y actividades universitarias';


--
-- Name: COLUMN events.event_type; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON COLUMN public.events.event_type IS 'academico, cultural, deportivo, conferencia, taller, otros';


--
-- Name: events_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.events_id_seq OWNER TO info_emi_user;

--
-- Name: events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.events_id_seq OWNED BY public.events.id;


--
-- Name: faqs; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.faqs (
    id integer NOT NULL,
    question text NOT NULL,
    answer text NOT NULL,
    category character varying(50),
    priority integer DEFAULT 1,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.faqs OWNER TO info_emi_user;

--
-- Name: TABLE faqs; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.faqs IS 'Preguntas frecuentes';


--
-- Name: COLUMN faqs.category; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON COLUMN public.faqs.category IS 'academico, administrativo, becas, inscripciones, otros';


--
-- Name: faqs_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.faqs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.faqs_id_seq OWNER TO info_emi_user;

--
-- Name: faqs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.faqs_id_seq OWNED BY public.faqs.id;


--
-- Name: inscriptions; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.inscriptions (
    id integer NOT NULL,
    period character varying(50) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    requirements text NOT NULL,
    process_steps text,
    costs text,
    documents_required text,
    contact_info text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.inscriptions OWNER TO info_emi_user;

--
-- Name: TABLE inscriptions; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.inscriptions IS 'Información general sobre inscripciones';


--
-- Name: inscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.inscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inscriptions_id_seq OWNER TO info_emi_user;

--
-- Name: inscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.inscriptions_id_seq OWNED BY public.inscriptions.id;


--
-- Name: pre_university_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.pre_university_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pre_university_id_seq OWNER TO info_emi_user;

--
-- Name: pre_university_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.pre_university_id_seq OWNED BY public.pre_university.id;


--
-- Name: scholarships; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.scholarships (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    requirements text,
    coverage character varying(100),
    amount numeric(10,2),
    deadline date,
    application_link character varying(500),
    contact_info text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.scholarships OWNER TO info_emi_user;

--
-- Name: TABLE scholarships; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.scholarships IS 'Becas y descuentos disponibles';


--
-- Name: COLUMN scholarships.coverage; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON COLUMN public.scholarships.coverage IS 'parcial, total, porcentaje';


--
-- Name: scholarships_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.scholarships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scholarships_id_seq OWNER TO info_emi_user;

--
-- Name: scholarships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.scholarships_id_seq OWNED BY public.scholarships.id;


--
-- Name: system_config; Type: TABLE; Schema: public; Owner: info_emi_user
--

CREATE TABLE public.system_config (
    id integer NOT NULL,
    config_key character varying(100) NOT NULL,
    config_value text,
    description text,
    is_public boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.system_config OWNER TO info_emi_user;

--
-- Name: TABLE system_config; Type: COMMENT; Schema: public; Owner: info_emi_user
--

COMMENT ON TABLE public.system_config IS 'Configuraciones del sistema';


--
-- Name: system_config_id_seq; Type: SEQUENCE; Schema: public; Owner: info_emi_user
--

CREATE SEQUENCE public.system_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_config_id_seq OWNER TO info_emi_user;

--
-- Name: system_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: info_emi_user
--

ALTER SEQUENCE public.system_config_id_seq OWNED BY public.system_config.id;


--
-- Name: system_stats; Type: VIEW; Schema: public; Owner: info_emi_user
--

CREATE VIEW public.system_stats AS
 SELECT ( SELECT count(*) AS count
           FROM public.careers
          WHERE (careers.is_active = true)) AS active_careers,
    ( SELECT count(*) AS count
           FROM public.pre_university
          WHERE (pre_university.is_active = true)) AS active_preuniversity,
    ( SELECT count(*) AS count
           FROM public.events
          WHERE ((events.is_active = true) AND (events.date >= CURRENT_DATE))) AS upcoming_events,
    ( SELECT count(*) AS count
           FROM public.faqs
          WHERE (faqs.is_active = true)) AS active_faqs,
    ( SELECT count(*) AS count
           FROM public.contacts
          WHERE (contacts.is_active = true)) AS active_contacts,
    ( SELECT count(*) AS count
           FROM public.scholarships
          WHERE (scholarships.is_active = true)) AS active_scholarships;


ALTER VIEW public.system_stats OWNER TO info_emi_user;

--
-- Name: upcoming_events; Type: VIEW; Schema: public; Owner: info_emi_user
--

CREATE VIEW public.upcoming_events AS
 SELECT id,
    title,
    event_type,
    date,
    start_time,
    end_time,
    location,
    organizer
   FROM public.events
  WHERE (((date >= CURRENT_DATE) AND (date <= (CURRENT_DATE + '30 days'::interval))) AND (is_active = true))
  ORDER BY date, start_time;


ALTER VIEW public.upcoming_events OWNER TO info_emi_user;

--
-- Name: academic_calendar id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.academic_calendar ALTER COLUMN id SET DEFAULT nextval('public.academic_calendar_id_seq'::regclass);


--
-- Name: admins id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.admins ALTER COLUMN id SET DEFAULT nextval('public.admins_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: careers id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.careers ALTER COLUMN id SET DEFAULT nextval('public.careers_id_seq'::regclass);


--
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- Name: events id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.events ALTER COLUMN id SET DEFAULT nextval('public.events_id_seq'::regclass);


--
-- Name: faqs id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.faqs ALTER COLUMN id SET DEFAULT nextval('public.faqs_id_seq'::regclass);


--
-- Name: inscriptions id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.inscriptions ALTER COLUMN id SET DEFAULT nextval('public.inscriptions_id_seq'::regclass);


--
-- Name: pre_university id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.pre_university ALTER COLUMN id SET DEFAULT nextval('public.pre_university_id_seq'::regclass);


--
-- Name: scholarships id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.scholarships ALTER COLUMN id SET DEFAULT nextval('public.scholarships_id_seq'::regclass);


--
-- Name: system_config id; Type: DEFAULT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.system_config ALTER COLUMN id SET DEFAULT nextval('public.system_config_id_seq'::regclass);


--
-- Name: academic_calendar academic_calendar_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.academic_calendar
    ADD CONSTRAINT academic_calendar_pkey PRIMARY KEY (id);


--
-- Name: admins admins_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_pkey PRIMARY KEY (id);


--
-- Name: admins admins_username_key; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.admins
    ADD CONSTRAINT admins_username_key UNIQUE (username);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: careers careers_code_key; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.careers
    ADD CONSTRAINT careers_code_key UNIQUE (code);


--
-- Name: careers careers_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.careers
    ADD CONSTRAINT careers_pkey PRIMARY KEY (id);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: faqs faqs_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.faqs
    ADD CONSTRAINT faqs_pkey PRIMARY KEY (id);


--
-- Name: inscriptions inscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.inscriptions
    ADD CONSTRAINT inscriptions_pkey PRIMARY KEY (id);


--
-- Name: pre_university pre_university_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.pre_university
    ADD CONSTRAINT pre_university_pkey PRIMARY KEY (id);


--
-- Name: scholarships scholarships_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.scholarships
    ADD CONSTRAINT scholarships_pkey PRIMARY KEY (id);


--
-- Name: system_config system_config_config_key_key; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_config_key_key UNIQUE (config_key);


--
-- Name: system_config system_config_pkey; Type: CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_pkey PRIMARY KEY (id);


--
-- Name: idx_academic_calendar_dates; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_academic_calendar_dates ON public.academic_calendar USING btree (start_date, end_date);


--
-- Name: idx_academic_calendar_period; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_academic_calendar_period ON public.academic_calendar USING btree (academic_period);


--
-- Name: idx_audit_logs_action; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: idx_audit_logs_admin; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_audit_logs_admin ON public.audit_logs USING btree (admin_id);


--
-- Name: idx_audit_logs_created; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_audit_logs_created ON public.audit_logs USING btree (created_at);


--
-- Name: idx_careers_active; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_careers_active ON public.careers USING btree (is_active);


--
-- Name: idx_careers_faculty; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_careers_faculty ON public.careers USING btree (campus);


--
-- Name: idx_careers_modality; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_careers_modality ON public.careers USING btree (modality);


--
-- Name: idx_contacts_active; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_contacts_active ON public.contacts USING btree (is_active);


--
-- Name: idx_contacts_department; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_contacts_department ON public.contacts USING btree (department);


--
-- Name: idx_contacts_priority; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_contacts_priority ON public.contacts USING btree (priority);


--
-- Name: idx_events_active; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_events_active ON public.events USING btree (is_active);


--
-- Name: idx_events_date; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_events_date ON public.events USING btree (date);


--
-- Name: idx_events_type; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_events_type ON public.events USING btree (event_type);


--
-- Name: idx_faqs_active; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_faqs_active ON public.faqs USING btree (is_active);


--
-- Name: idx_faqs_category; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_faqs_category ON public.faqs USING btree (category);


--
-- Name: idx_faqs_priority; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_faqs_priority ON public.faqs USING btree (priority);


--
-- Name: idx_inscriptions_dates; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_inscriptions_dates ON public.inscriptions USING btree (start_date, end_date);


--
-- Name: idx_inscriptions_period; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_inscriptions_period ON public.inscriptions USING btree (period);


--
-- Name: idx_pre_university_active; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_pre_university_active ON public.pre_university USING btree (is_active);


--
-- Name: idx_pre_university_dates; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_pre_university_dates ON public.pre_university USING btree (start_date, end_date);


--
-- Name: idx_scholarships_active; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_scholarships_active ON public.scholarships USING btree (is_active);


--
-- Name: idx_scholarships_deadline; Type: INDEX; Schema: public; Owner: info_emi_user
--

CREATE INDEX idx_scholarships_deadline ON public.scholarships USING btree (deadline);


--
-- Name: academic_calendar update_academic_calendar_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_academic_calendar_updated_at BEFORE UPDATE ON public.academic_calendar FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: admins update_admins_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_admins_updated_at BEFORE UPDATE ON public.admins FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: careers update_careers_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_careers_updated_at BEFORE UPDATE ON public.careers FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: contacts update_contacts_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON public.contacts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: inscriptions update_inscriptions_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_inscriptions_updated_at BEFORE UPDATE ON public.inscriptions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: pre_university update_pre_university_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_pre_university_updated_at BEFORE UPDATE ON public.pre_university FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: scholarships update_scholarships_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_scholarships_updated_at BEFORE UPDATE ON public.scholarships FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: system_config update_system_config_updated_at; Type: TRIGGER; Schema: public; Owner: info_emi_user
--

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON public.system_config FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: audit_logs audit_logs_admin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: info_emi_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.admins(id) ON DELETE SET NULL;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO info_emi_user;


--
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO info_emi_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO info_emi_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO info_emi_user;


--
-- PostgreSQL database dump complete
--

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