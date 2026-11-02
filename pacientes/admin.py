from django.contrib import admin
from .models import Tutor, Mascota

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    def get_readonly_fields(self,request,obj=None):
        return ('email_verificado',) if request.user.is_superuser else ('usuario','email_verificado')
    def save_model(self,request,obj,form,change):
        if change and 'email' in form.changed_data: obj.email_verificado=False
        super().save_model(request,obj,form,change)
    list_display = ('rut', 'nombre', 'apellidos', 'telefono', 'email')
    search_fields = ('rut', 'nombre', 'apellidos', 'email')
    list_filter = ('fecha_registro',)

@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especie', 'raza', 'tutor')
    search_fields = ('nombre', 'tutor__nombre', 'tutor__apellidos')
    list_filter = ('especie',)
