from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class RegistroFisiologico(models.Model):
    """
    Modelo para simular la estructura de los registros de datos fisiológicos
    (GSR y Pulso) de NeuroPulse.
    """
    # En un entorno real, usarías la clave foránea del usuario autenticado
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros')
    
    # Campo para registrar la fecha y hora de la medición
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")
    
    # Respuesta Galvánica de la Piel (GSR) - Medida de estrés
    # El valor GSR suele ser un valor de conductancia o una señal cruda (aquí simulado)
    valor_gsr = models.IntegerField(verbose_name="Valor GSR (Estrés)")
    
    # Frecuencia Cardíaca (BPM) - Pulso
    valor_bpm = models.IntegerField(verbose_name="Valor BPM (Pulso)")

    class Meta:
        verbose_name = "Registro Fisiológico"
        verbose_name_plural = "Registros Fisiológicos"
        # Ordenamos los registros por fecha y hora descendente por defecto
        ordering = ['-timestamp']

    def __str__(self):
        return f"Registro de {self.usuario.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

# NOTA: Después de crear o modificar modelos, debes ejecutar:
# python manage.py makemigrations dashboard
# python manage.py migrate
