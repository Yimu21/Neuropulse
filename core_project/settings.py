from pathlib import Path
import os
import dj_database_url
from decouple import config
from dotenv import load_dotenv 

# CRÍTICO: Carga de variables de entorno al inicio.
load_dotenv() 

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# 1. SEGURIDAD Y HOSTS (CRÍTICO PARA ERROR 400 EN RENDER)
# -------------------------------------------------------------------

# Leer variables sensibles y DEBUG de forma segura
SECRET_KEY = config('SECRET_KEY', default='django-insecure-vr^jtl^umh3!=9b*rk)&1erydyyh#!ppu_hji#dcidf)=gfvkv')
# Usamos un valor por defecto seguro (True) en caso de fallo de lectura local
DEBUG = config('DEBUG', default='True', cast=bool) 

# CRÍTICO: Lista de hosts permitidos (Solo dominio, sin https://)
ALLOWED_HOSTS = [
    '127.0.0.1', 
    'localhost',
    'neuropulse-1.onrender.com', # Dominio específico de Render
    '.onrender.com'             # Comodín para aceptar peticiones de Render
]

# -------------------------------------------------------------------
# 2. APLICACIONES INSTALADAS (SOLO UNA LISTA)
# -------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tu app
    'dashboard', 
    
    # Librerías de terceros
    'crispy_forms', 
]

# -------------------------------------------------------------------
# 3. MIDDLEWARE (Con Whitenoise y seguridad)
# -------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # ⬅️ Necesario para estáticos en Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # ⬅️ Corregido error E408
    'django.contrib.messages.middleware.MessageMiddleware',   # ⬅️ Corregido error E409
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core_project.urls'

# -------------------------------------------------------------------
# 4. TEMPLATES (Corregido el error de admin.E403)
# -------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"], 
        'APP_DIRS': True, # CRÍTICO: Busca plantillas dentro de las carpetas de las apps (dashboard/templates)
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages', 
            ],
        },
    },
]

WSGI_APPLICATION = 'core_project.wsgi.application'


# -------------------------------------------------------------------
# 5. CONFIGURACIÓN DE BASE DE DATOS (POSTGRESQL / SUPABASE)
# -------------------------------------------------------------------

# 1. Configuración Base (Usando variables locales para desarrollo)
DATABASES = {
    'default': {
        # Usamos PostgreSQL local como default para desarrollo
        'ENGINE': 'django.db.backends.postgresql', 
        'NAME': config("SUPABASE_DBNAME"),
        'USER': config("SUPABASE_USER"),
        'PASSWORD': config("SUPABASE_PASSWORD"),
        'HOST': config("SUPABASE_HOST"),
        'PORT': config("SUPABASE_PORT", default='5432'),
        'OPTIONS': {
            'sslmode': 'require', # Es necesario para Supabase
        }
    }
}

# 2. LÓGICA DE PRODUCCIÓN: SOBRESESCRIBIR si Render establece DATABASE_URL
if os.environ.get('DATABASE_URL'):
    # 2a. Sobrescribir Base de Datos
    DATABASES['default'] = dj_database_url.parse(
        os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_check=True,
    )
    # CRÍTICO: Forzar SSL en producción
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }
    
    # 2b. Configurar Seguridad
    DEBUG = False
    # ✅ LÓGICA CORREGIDA: Reemplazar ALLOWED_HOSTS con el host de Render (solo si existe)
    # Render establece RENDER_EXTERNAL_HOSTNAME. Usamos ese valor para el host permitido.
    RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_HOST:
        ALLOWED_HOSTS.append(RENDER_HOST)
    
    # Agregar la línea de seguridad proxy SSL
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# -------------------------------------------------------------------
# 6. CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS PARA WHITENOISE
# -------------------------------------------------------------------

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'dashboard/static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 

# ... (El resto del archivo no necesita cambios)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'