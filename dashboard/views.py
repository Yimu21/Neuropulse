from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings # Para acceder a las variables de entorno
import plotly.express as px
import pandas as pd
import numpy as np
import datetime
import random 

# --- Nuevas Importaciones para PostgreSQL (psycopg2) ---
import psycopg2
from urllib.parse import quote_plus
import os
# Asegúrate de tener 'python-dotenv' y 'psycopg2-binary' instalados.

# 1. Configuración de la conexión (Obteniendo variables de .env)
HOST = os.environ.get("SUPABASE_HOST")
DBNAME = os.environ.get("SUPABASE_DBNAME")
USER = os.environ.get("SUPABASE_USER")
PASSWORD = os.environ.get("SUPABASE_PASSWORD")
PORT = os.environ.get("SUPABASE_PORT", "5432")

# Verificar si las credenciales básicas están presentes
DB_CREDENTIALS_OK = all([HOST, DBNAME, USER, PASSWORD])

# --- Función para crear y obtener la conexión a PostgreSQL ---
def obtener_conexion():
    """Crea una conexión a la base de datos PostgreSQL de Supabase."""
    if not DB_CREDENTIALS_OK:
        print("ADVERTENCIA: Las variables de entorno de PostgreSQL no están configuradas correctamente.")
        return None

    try:
        conn = psycopg2.connect(
            host=HOST,
            database=DBNAME,
            user=USER,
            password=PASSWORD,
            port=PORT,
            connect_timeout=5 # Tiempo de espera para la conexión
        )
        return conn
    except Exception as e:
        print(f"Error al conectar con PostgreSQL (Supabase): {e}")
        return None

# Definimos el intervalo de actualización en milisegundos (20 segundos)
REFRESH_INTERVAL_MS = 20000 

# --- Función Auxiliar para Generar Gráficos Plotly (Sin cambios) ---
def crear_grafico_lineas_tiempo(df, y_columna, titulo, y_titulo, color_linea):
    """
    Crea un gráfico interactivo de líneas de Plotly para visualizar datos 
    fisiológicos a lo largo del tiempo.
    """
    fig = px.line(
        df, 
        x='timestamp', 
        y=y_columna, 
        title=f'<b>{titulo}</b>',
        markers=True, 
        height=550
    )
    
    # Personalización estética
    fig.update_layout(
        xaxis_title="Fecha y Hora",
        yaxis_title=y_titulo,
        font=dict(family="Segoe UI, Tahoma, Geneva, Verdana", size=12, color="#010101"),
        plot_bgcolor='#F8F9FA', 
        paper_bgcolor='#FFFFFF', 
        margin=dict(l=40, r=40, t=80, b=40),
        hovermode="x unified",
        title_x=0.5
    )
    
    fig.update_traces(line=dict(color=color_linea, width=2.5), mode='lines+markers')
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0', tickformat="%H:%M\n%Y-%m-%d")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
    
    graph_html = fig.to_html(full_html=False, default_height=550)
    return graph_html

# --- Función Auxiliar para OBTENER DATOS REALES/SIMULADOS ---
def obtener_datos_de_supabase(user_id=1): # user_id debería ser dinámico basado en la sesión
    """
    Intenta obtener los datos fisiológicos de la tabla 'registros' en Supabase usando psycopg2.
    Si falla la conexión o la consulta, retorna datos simulados (fallback).
    """
    conn = obtener_conexion()
    
    if conn:
        try:
            # Consulta SQL para obtener los últimos 50 registros del usuario
            # **ADVERTENCIA**: Asegúrate de que el nombre de la tabla ('registros_fisiologicos') 
            # y la columna ('usuario_id') coincidan con tu esquema de Supabase.
            sql_query = """
                SELECT timestamp, valor_gsr, valor_bpm
                FROM registros_fisiologicos
                WHERE usuario_id = %s
                ORDER BY timestamp DESC
                LIMIT 50;
            """
            
            df = pd.read_sql(sql_query, conn, params=[user_id])
            
            if not df.empty:
                # Asegurar que la columna 'timestamp' sea de tipo datetime y ordenar ascendente
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values(by='timestamp', ascending=True)
                return df
            
        except Exception as e:
            print(f"Error al ejecutar la consulta SQL: {e}")
        finally:
            if conn:
                conn.close()
    
    # --- FALLBACK: Generación de datos simulados si la conexión falla o no hay datos ---
    N = 50
    base_time = datetime.datetime.now()
    timestamps = [base_time - datetime.timedelta(seconds=20 * i) for i in range(N)] # Ajustado a 20s
    gsr_base = np.linspace(30, 70, N)
    gsr_data = (gsr_base + np.random.normal(0, 5, N)).astype(int).tolist()
    bpm_base = np.linspace(75, 85, N)
    bpm_data = (bpm_base + np.random.normal(0, 5, N)).astype(int).tolist()
    
    data = {
        'timestamp': timestamps,
        'valor_gsr': gsr_data,
        'valor_bpm': bpm_data
    }
    df = pd.DataFrame(data).sort_values(by='timestamp', ascending=True)
    return df

# --- Vistas Actualizadas con Lógica Plotly ---

# Vista de la página de inicio (sin cambios)
def home(request):
    return render(request, 'dashboard/home.html', {})

def resultados_gsr(request):
    """Muestra el gráfico y datos de GSR (Estrés) en tiempo real, obtenidos de Supabase."""
    
    # 1. Obtener datos (ahora con conexión a Supabase/psycopg2)
    # En un proyecto real, obtendrías el ID del usuario actual: user_id = request.user.id
    df = obtener_datos_de_supabase(user_id=1) 
    
    # 2. Generar Gráfico Plotly para GSR
    gsr_graph_html = crear_grafico_lineas_tiempo(
        df, 
        y_columna='valor_gsr', 
        titulo='Nivel de Estrés (GSR) en Tiempo Real', 
        y_titulo='Conductancia de la Piel (Unidades Arbitrarias)',
        color_linea='#2C3E50' 
    )
    
    # 3. Preparar contexto y renderizar
    context = {
        'gsr_graph': gsr_graph_html,
        'gsr_promedio': df['valor_gsr'].mean().round(2),
        'gsr_maximo': df['valor_gsr'].max(),
        'refresh_interval': REFRESH_INTERVAL_MS, # Intervalo de actualización (20 segundos)
    }
    return render(request, 'dashboard/resultados_gsr.html', context)

def resultados_pulso(request):
    """Muestra el gráfico y datos del Pulso (Frecuencia Cardíaca), obtenidos de Supabase."""
    
    # 1. Obtener datos (ahora con conexión a Supabase/psycopg2)
    df = obtener_datos_de_supabase(user_id=1)
    
    # 2. Generar Gráfico Plotly para BPM
    bpm_graph_html = crear_grafico_lineas_tiempo(
        df, 
        y_columna='valor_bpm', 
        titulo='Ritmo Cardíaco (BPM) en Tiempo Real', 
        y_titulo='Frecuencia Cardíaca (Latidos por Minuto - BPM)',
        color_linea='#E74C3C' 
    )
    
    # 3. Preparar contexto y renderizar
    context = {
        'bpm_graph': bpm_graph_html,
        'bpm_promedio': df['valor_bpm'].mean().round(2),
        'bpm_maximo': df['valor_bpm'].max(),
        'refresh_interval': REFRESH_INTERVAL_MS, # Intervalo de actualización (20 segundos)
    }
    return render(request, 'dashboard/resultados_pulso.html', context)

def ver_correlacion(request):
    """Muestra la correlación entre GSR y Pulso (Gráfico Scatter Plot), obtenidos de Supabase."""
    
    df = obtener_datos_de_supabase(user_id=1)
    
    # 1. Calcular Correlación
    correlacion = df['valor_gsr'].corr(df['valor_bpm']).round(3)
    
    # 2. Generar Scatter Plot de Correlación
    fig = px.scatter(
        df, 
        x='valor_gsr', 
        y='valor_bpm', 
        title=f'<b>Correlación entre GSR y BPM (r = {correlacion})</b>',
        color='timestamp', 
        labels={
            'valor_gsr': 'Nivel de Estrés (GSR)',
            'valor_bpm': 'Ritmo Cardíaco (BPM)',
            'color': 'Momento'
        },
        height=550
    )
    
    fig.update_layout(
        font=dict(family="Segoe UI, Tahoma, Geneva, Verdana", size=12, color="#010101"),
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='#FFFFFF',
        title_x=0.5
    )
    
    correlation_graph_html = fig.to_html(full_html=False, default_height=550)
    
    context = {
        'correlation_graph': correlation_graph_html,
        'correlacion_valor': correlacion,
        # La correlación no suele ser en tiempo real, así que no se añade auto-refresh aquí.
    }
    return render(request, 'dashboard/ver_correlacion.html', context)

# Vistas existentes (sin cambios)
def lista_usuarios(request):
    """Muestra la tabla con los últimos registros de usuarios."""
    # Aquí iría la lógica para listar registros históricos (tal vez una tabla con Pandas/Bootstrap)
    return render(request, 'dashboard/lista_usuarios.html', {})

def descargar_app(request):
    """Página con el enlace o código QR para descargar la app Android."""
    return render(request, 'dashboard/descargar_app.html', {})