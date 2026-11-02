from django.contrib import admin
from .models import FichaClinica, Recordatorio

@admin.register(FichaClinica)
class FichaClinicaAdmin(admin.ModelAdmin):
    list_display = ('mascota', 'profesional', 'fecha_atencion', 'diagnostico')
    search_fields = ('mascota__nombre', 'profesional__nombre', 'profesional__apellidos', 'diagnostico')
    list_filter = ('fecha_atencion', 'profesional')

@admin.register(Recordatorio)
class RecordatorioAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'mascota', 'fecha_programada', 'estado')
    search_fields = ('mascota__nombre', 'mensaje')
    list_filter = ('tipo', 'estado', 'fecha_programada')