# dashboard/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Ruta de Inicio
    path('', views.home, name='home'),
    
    # Rutas del Menú
    path('gsr/', views.resultados_gsr, name='resultados_gsr'),
    path('pulso/', views.resultados_pulso, name='resultados_pulso'),
    path('correlacion/', views.ver_correlacion, name='ver_correlacion'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('descargar/', views.descargar_app, name='descargar_app'),
]