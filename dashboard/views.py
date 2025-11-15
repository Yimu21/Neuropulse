from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings # Para acceder a las variables de entorno
import plotly.express as px
import pandas as pd
import numpy as np
import datetime
import random 

# --- Importaciones de Supabase ---
from supabase import create_client, Client
import time
import os
# Asegúrate de tener 'python-dotenv' y 'supabase-py' instalados.

# 1. Configuración de la conexión a Supabase
# Se recomienda obtener la URL y KEY desde las variables de entorno de Django (settings.py)
# Estas variables se cargan gracias al "load_dotenv()" que pusiste en settings.py
SUPABASE_URL = os.environ.get("SUPABASE_URL", "URL_DE_FALLO")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "KEY_DE_FALLO")

# Inicializar cliente de Supabase (se puede hacer una sola vez en un módulo de servicio si el proyecto crece)
# Manejo de fallos en caso de que las variables no estén cargadas
supabase = None
if SUPABASE_URL != "URL_DE_FALLO" and SUPABASE_KEY != "KEY_DE_FALLO":
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        # En un entorno de producción, esto debería ser un logger, no un print.
        print(f"Error al inicializar Supabase: {e}")
else:
    print("ADVERTENCIA: Variables de entorno de Supabase no cargadas correctamente.")
# ------------------------------------

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
    Intenta obtener los datos fisiológicos de la tabla 'registros' en Supabase.
    Si falla la conexión, retorna datos simulados (fallback).
    """
    global supabase
    
    if supabase:
        try:
            # Reemplaza 'registros_fisiologicos' con el nombre de tu tabla en Supabase
            # Filtra por user_id (asumiendo que tienes una columna 'usuario_id' en Supabase)
            # Ordena por timestamp de forma descendente y limita a los últimos 50 registros.
            # NOTA: Supabase usa el nombre de tabla que creaste, por ejemplo: 'registro_fisiologico'
            # Aquí se usa un nombre genérico: 'registros_fisiologicos'
            response = supabase.table('registros_fisiologicos').select("timestamp, valor_gsr, valor_bpm").eq('usuario_id', user_id).order('timestamp', desc=True).limit(50).execute()
            
            data = response.data
            
            if data:
                # Convertir la lista de diccionarios de Supabase a DataFrame de Pandas
                df = pd.DataFrame(data)
                
                # Asegurar que la columna 'timestamp' sea de tipo datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Ordenar por timestamp de forma ascendente para la visualización del gráfico
                df = df.sort_values(by='timestamp', ascending=True)
                return df
            
        except Exception as e:
            print(f"Error al obtener datos de Supabase: {e}")
            print("Usando datos simulados como fallback.")
    
    # --- FALLBACK: Generación de datos simulados si la conexión falla o no hay datos ---
    N = 50
    base_time = datetime.datetime.now()
    timestamps = [base_time - datetime.timedelta(seconds=5 * i) for i in range(N)]
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
    
    # 1. Obtener datos (ahora con conexión a Supabase)
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
        'refresh_interval': REFRESH_INTERVAL_MS, # Nuevo: Intervalo de actualización
    }
    return render(request, 'dashboard/resultados_gsr.html', context)

def resultados_pulso(request):
    """Muestra el gráfico y datos del Pulso (Frecuencia Cardíaca), obtenidos de Supabase."""
    
    # 1. Obtener datos (ahora con conexión a Supabase)
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
        'refresh_interval': REFRESH_INTERVAL_MS, # Nuevo: Intervalo de actualización
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