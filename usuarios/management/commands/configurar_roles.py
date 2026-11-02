from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help='Crea roles y sincroniza sus permisos; no asigna usuarios ni privilegios staff.'
    def handle(self,*args,**kwargs):
        for name,apps in [('Recepcion',['pacientes','agendamiento']),('Veterinarios',['pacientes','agendamiento','clinica'])]:
            group,_=Group.objects.get_or_create(name=name)
            permissions=Permission.objects.filter(content_type__app_label__in=apps).exclude(codename__startswith='delete_')
            regular=list(permissions.exclude(content_type__model__in=['profesional','horarioprofesional']))
            readonly=list(Permission.objects.filter(content_type__app_label='agendamiento',codename__in=['view_profesional','view_horarioprofesional']))
            group.permissions.set(regular+readonly)
        self.stdout.write('Roles configurados. Asigna is_staff y el grupo correspondiente solo desde una cuenta administradora.')
