from django.shortcuts import render
# Importaciones de Django y utilidades
from dashboard.models import RegistroFisiologico 
from datetime import datetime
from django.http import JsonResponse
import random
# Importaciones para el Cálculo y Gráficas
from scipy.stats import pearsonr # Necesario para la correlación
import numpy as np               # Necesario para el manejo de arrays en el cálculo
import plotly.express as px
import pandas as pd

# 🌟🌟🌟 CORRECCIÓN: DEFINICIÓN DE VARIABLE GLOBAL 🌟🌟🌟
NUM_REGISTROS = 50 
def home(request):
    """Vista de inicio"""
    return render (request, "dashboard/home.html")
# Definimos el intervalo de refresco para las peticiones AJAX
REFRESH_INTERVAL_MS = 10000 # 10 segundos
def resultados_pulso (request):
    # Petición AJAX devolver JSON
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        ultimo = RegistroFisiologico.objects.order_by("-creado_en").first()
        bpm = ultimo.ritmo_cardiaco_bpm if ultimo else 70
        return JsonResponse({
            "bpm": bpm,
            "timestamp": datetime.now().isoformat()
        })
    # Página completa
    return render(request, "dashboard/resultados_pulso.html", {
        "refresh_interval": REFRESH_INTERVAL_MS
    })
def resultados_gsr(request):
    # Lógica de GSR existente
    registros = RegistroFisiologico.objects.order_by('-creado_en')[:30]
    if not registros:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "activation": 0,
                "conductance": 0,
                "estado": "Sin datos",
                "gif": "dashboard/relajado.gif"
            })
        return render(request, 'dashboard/resultados_gsr.html', {
            "gsr_graph": None,
            "activation_level_actual": "--",
            "conductance_actual": "--",
            "estado": "sin datos",
            "gif": "dashboard/relajado.gif",
            "refresh_interval": REFRESH_INTERVAL_MS,
        })
    ultimo = registros[0]
    activation = ultimo.activation_level or 0
    conductance = ultimo.conductance_us or 0
    # Estado emocional
    if activation > 100:
        estado = "Estresado"
        gif = "dashboard/estresado.gif"
    elif activation >= 80:
        estado = "Normal"
        gif = "dashboard/normal.gif"
    else:
        estado = "Relajado"
        gif = "dashboard/relajado.gif"
    # Si es AJAX devolver solo datos
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "activation": activation,
            "conductance": conductance,
            "estado": estado,
            "gif": gif,
        })
    # Datos iniciales de la gráfica (solo para cargar página) - Lógica de Plotly
    valores = []
    tiempos = []
    base = activation
    for i in range(20):
        val = random.uniform(base - 5, base + 5)
        val = max(50, min (120, val))
        valores.append(val)
        tiempos.append(i)
    df = pd.DataFrame({"t": tiempos, "activation": valores})
    fig = px.line(
        df,
        x="t",
        y="activation",
        title="<b>Nivel de Estrés – Activation Level</b>",
        markers=True,
        range_y=[50, 120]
    )
    fig.update_layout(template="simple_white", title_x=0.5)
    gsr_graph_html = fig.to_html(full_html=False)
    return render (request, 'dashboard/resultados_gsr.html', {
        "gsr_graph": gsr_graph_html,
        "activation_level_actual": activation,
        "conductance_actual": conductance,
        "estado": estado,
        "gif": gif,
        "refresh_interval": REFRESH_INTERVAL_MS,
    })
def calcular_interpretacion_correlacion(r):
    """
    Determina la clase CSS y el texto de interpretación basado en el valor de r.
    El texto incluye la fórmula de Correlación de Pearson en formato LaTeX.
    """
    r_abs = abs(r)
    
    # Texto de la fórmula de Correlación de Pearson (para MathJax)
    formula_latex = r"$$\rho_{X,Y} = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2 \sum_{i=1}^{n}(y_i - \bar{y})^2}}$$"
    
    if r_abs >= 0.7:
        clase = "fuerte"
        texto = f"El coeficiente $\\mathbf{{r = {r:.4f}}}$ indica una **correlación fuerte** entre el Nivel de Estrés (GSR) y el Ritmo Cardíaco (Pulso). \\({formula_latex}\\)"
    elif r_abs >= 0.3:
        clase = "moderada"
        texto = f"El coeficiente $\\mathbf{{r = {r:.4f}}}$ indica una **correlación moderada**. Existe una tendencia a que las variables se muevan juntas. \\({formula_latex}\\)"
    else: # r_abs < 0.3
        clase = "debil"
        texto = f"El coeficiente $\\mathbf{{r = {r:.4f}}}$ indica una **correlación débil o nula**. No hay relación lineal significativa. \\({formula_latex}\\)"
    # Ajuste de clase según el signo
    if r >= 0.3:
        clase += "-pos"
    elif r <= -0.3:
        clase += "-neg"
    else:
        clase = "debil"
    return clase, texto

def ver_correlacion(request):
    """
    Vista principal para el cálculo y visualización del coeficiente de correlación (r)
    entre el Nivel de Estrés (GSR) y el Ritmo Cardíaco (Pulso), usando datos de Supabase.
    """
    # Valor por defecto en caso de error o falta de datos
    contexto_default = {
        'coeficiente_r': 'N/A',
        'ultimo_gsr': 'N/A',
        'ultimo_pulso': 'N/A',
        'correlacion_clase': 'sin-datos',
        'interpretacion': 'No hay datos disponibles para el cálculo. Por favor, asegúrese de tener al menos 2 registros válidos.'
    }
    
    # Inicialización de contexto para evitar errores de referencia en el bloque 'except'
    contexto = contexto_default 
    
    try:
        # 1. Recuperar los últimos N registros (50) para el cálculo de CORRELACIÓN
        registros = RegistroFisiologico.objects.order_by('-creado_en')[:NUM_REGISTROS]
        
        if len(registros) < 2:
            return render(request, 'dashboard/ver_correlacion.html', contexto_default)
        # 2. Separar los datos en dos listas, filtrando valores nulos
        # CRÍTICO: Usa los nombres de campos del modelo (activation_level, ritmo_cardiaco_bpm)
        gsr_data = [r.activation_level for r in registros if r.activation_level is not None]
        bpm_data = [r.ritmo_cardiaco_bpm for r in registros if r.ritmo_cardiaco_bpm is not None]
        min_len = min(len(gsr_data), len(bpm_data))
        if min_len < 2:
            # No hay suficientes pares de datos válidos después de filtrar nulos
            return render(request, 'dashboard/ver_correlacion.html', contexto_default)
        gsr_array = np.array(gsr_data[:min_len])
        bpm_array = np.array(bpm_data[:min_len])
        
        # 3. Calcular el coeficiente de correlación de Pearson (r)
        coeficiente_r, p_value = pearsonr(gsr_array, bpm_array)
        
        # 4. Determinar la clase e interpretación
        correlacion_clase, interpretacion = calcular_interpretacion_correlacion(coeficiente_r)
        
        # 5. OBTENER SOLO EL ÚLTIMO REGISTRO VÁLIDO PARA CONTEXTO
        ultimo_registro_valido = RegistroFisiologico.objects.filter(
            activation_level__isnull=False, 
            ritmo_cardiaco_bpm__isnull=False
        ).order_by('-creado_en').first()
        
        # 🌟🌟🌟 CORRECCIÓN DE FLUJO: ASIGNAR LAS VARIABLES AQUÍ 🌟🌟🌟
        if ultimo_registro_valido:
            # Usar los nombres de campos del modelo
            ultimo_gsr = f"{ultimo_registro_valido.activation_level:.2f}"
            ultimo_pulso = f"{ultimo_registro_valido.ritmo_cardiaco_bpm}"
        else:
            ultimo_gsr = 'N/A'
            ultimo_pulso = 'N/A'
        
        # 6. Preparar el contexto si el cálculo fue exitoso (dentro del try)
        contexto = {
            'coeficiente_r': f"{coeficiente_r:.4f}", # Formateado a 4 decimales
            'ultimo_gsr': ultimo_gsr,
            'ultimo_pulso': ultimo_pulso,
            'num_registros': min_len if 'min_len' in locals() else NUM_REGISTROS,
            'correlacion_clase': correlacion_clase,
            'interpretacion': interpretacion, 
        }
        
    except Exception as e:
        # Manejo de errores de conexión o datos (muesta error en consola)
        print(f"Error al procesar datos de Supabase para correlación: {e}")
        # Si hay un error, se usa el contexto_default, que ya está cargado en 'contexto'
        contexto = contexto_default
    
    # Este es el ÚNICO return render que debe ocurrir. 
    return render(request, 'dashboard/ver_correlacion.html', contexto)

def descargar_app (request):
    """Vista de descarga de la aplicación"""
    return render (request, "dashboard/descargar_app.html")
