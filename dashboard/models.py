from django.db import models

class RegistroFisiologico(models.Model):
    """
    Modelo que mapea la tabla existente 'usuarios' en Supabase.
    CRÍTICO: Usa db_column para conectar los nombres lógicos de Django 
    a los nombres de columna en PostgreSQL (activation_level, bpm, creado_en).
    """
    
    # ID
    id = models.AutoField(primary_key=True, db_column='id') 

    # Mapeo del Timestamp (Columna real: creado_en)
    creado_en = models.DateTimeField(db_column='creado_en')
    
    # Nivel de Estrés (Columna real: activation_level)
    activation_level = models.FloatField(
        null=True, blank=True, 
        db_column='activation_level'
    )
    
    # Pulso (Columna real: bpm)
    # Mapeo clave para la vista (usa 'ritmo_cardiaco_bpm' lógicamente, 'bpm' físicamente)
    ritmo_cardiaco_bpm = models.FloatField(
        null=True, blank=True, 
        db_column='bpm' 
    )
    
    # Conductancia (Columna real: conductance_us)
    conductance_us = models.FloatField(
        null=True, blank=True, 
        db_column='conductance_us'
    )
    
    # Valor GSR (Columna real: gsr_value)
    gsr_value = models.FloatField(
        null=True, blank=True, 
        db_column='gsr_value'
    )


    class Meta:
        db_table = 'usuarios' # Nombre EXACTO de tu tabla en Supabase
        managed = False        # ¡CRÍTICO! Le dice a Django que no modifique esta tabla
        ordering = ['-creado_en']
        verbose_name = "Registro Fisiológico"
        verbose_name_plural = "Registros Fisiológicos"

    def __str__(self):
        return f"Registro {self.id} - {self.creado_en} - BPM:{self.ritmo_cardiaco_bpm}"


class ActivacionSistema(models.Model):
    """
    Modelo que mapea la tabla existente 'activacion_sistema' en Supabase.
    """
    id = models.AutoField(primary_key=True, db_column='id')
    activation = models.BooleanField(default=False, db_column='activation')

    class Meta:
        db_table = 'activacion_sistema'
        managed = False
        verbose_name = "Activación del Sistema"
        verbose_name_plural = "Activaciónes del Sistema"

    def __str__(self):
        return f"Activación: {'Activo' if self.activation else 'Inactivo'}"