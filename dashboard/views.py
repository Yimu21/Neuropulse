from django.shortcuts import render
from dashboard.models import RegistroFisiologico
import plotly.express as px
import pandas as pd
from django.http import JsonResponse
from dashboard.models import RegistroFisiologico
from datetime import datetime

REFRESH_INTERVAL_MS = 10000  # 10 segundos
def home(request):
    return render(request, "dashboard/home.html")

def resultados_pulso(request):
    # Petición AJAX → devolver JSON
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        ultimo = RegistroFisiologico.objects.order_by("-creado_en").first()
        bpm = ultimo.bpm if ultimo else 70
        return JsonResponse({
            "bpm": bpm,
            "timestamp": datetime.now().isoformat()
        })

    # Página completa
    return render(request, "dashboard/resultados_pulso.html", {
        "refresh_interval": REFRESH_INTERVAL_MS
    })



def resultados_gsr(request):

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

    # Si es AJAX → devolver solo datos
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "activation": activation,
            "conductance": conductance,
            "estado": estado,
            "gif": gif,
        })

    # Datos iniciales de la gráfica (solo para cargar página)
    import random
    valores = []
    tiempos = []
    base = activation
    for i in range(20):
        val = random.uniform(base - 5, base + 5)
        val = max(50, min(120, val))
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

    return render(request, 'dashboard/resultados_gsr.html', {
        "gsr_graph": gsr_graph_html,
        "activation_level_actual": activation,
        "conductance_actual": conductance,
        "estado": estado,
        "gif": gif,
        "refresh_interval": REFRESH_INTERVAL_MS,
    })





def ver_correlacion(request):
    return render(request, "dashboard/ver_correlacion.html") 


def descargar_app(request):
    return render(request, "dashboard/descargar_app.html")