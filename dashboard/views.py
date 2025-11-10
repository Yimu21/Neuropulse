# dashboard/views.py

from django.shortcuts import render

# Vista de la página de inicio (ya implementada)
def home(request):
    return render(request, 'dashboard/home.html', {})

# Nuevas Vistas para el menú

def resultados_gsr(request):
    """Muestra el gráfico y datos de GSR (Estrés)."""
    return render(request, 'dashboard/resultados_gsr.html', {})

def resultados_pulso(request):
    """Muestra el gráfico y datos del Pulso (Frecuencia Cardíaca)."""
    return render(request, 'dashboard/resultados_pulso.html', {})

def ver_correlacion(request):
    """Muestra la correlación entre GSR y Pulso."""
    return render(request, 'dashboard/ver_correlacion.html', {})

def lista_usuarios(request):
    """Muestra la tabla con los últimos registros de usuarios."""
    return render(request, 'dashboard/lista_usuarios.html', {})

def descargar_app(request):
    """Página con el enlace o código QR para descargar la app Android."""
    return render(request, 'dashboard/descargar_app.html', {})