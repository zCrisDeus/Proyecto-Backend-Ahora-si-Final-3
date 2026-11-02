from django.contrib import admin
from .models import Profesional, CitaMedica, HorarioProfesional

@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellidos', 'especialidad', 'activo')
    search_fields = ('nombre', 'apellidos', 'especialidad')
    list_filter = ('especialidad', 'activo')

@admin.register(CitaMedica)
class CitaMedicaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'mascota', 'profesional', 'estado')
    search_fields = ('mascota__nombre', 'profesional__nombre', 'profesional__apellidos')
    list_filter = ('fecha', 'estado', 'profesional')
@admin.register(HorarioProfesional)
class HorarioAdmin(admin.ModelAdmin):
    list_display=('profesional','dia_semana','inicio','fin')
    list_filter=('profesional','dia_semana')
