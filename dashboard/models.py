from django.db import models

class RegistroFisiologico(models.Model):
    """
    Modelo que mapea la tabla existente 'usuarios' en Supabase.
    NOTA: no se hacen migraciones ya que solo serán para leer
    """
    id = models.AutoField(primary_key=True, db_column='id')
    creado_en = models.DateTimeField(db_column='creado_en')
    activation_level = models.FloatField(null=True, blank=True, db_column='activation_level')
    bpm = models.FloatField(null=True, blank=True, db_column='bpm')
    conductance_us = models.FloatField(null=True, blank=True, db_column='conductance_us')
    gsr_value = models.FloatField(null=True, blank=True, db_column='gsr_value')

    class Meta:
        db_table = 'usuarios'  # nombre EXACTO en Supabase
        managed = False
        ordering = ['-creado_en']
        verbose_name = "Registro Fisiológico"
        verbose_name_plural = "Registros Fisiológicos"

    def __str__(self):
        return f"Registro {self.id} - {self.creado_en} - BPM:{self.bpm}"


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
