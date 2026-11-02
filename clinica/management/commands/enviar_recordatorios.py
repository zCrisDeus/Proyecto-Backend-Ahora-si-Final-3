from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from clinica.models import Recordatorio

class Command(BaseCommand):
    help='Envía recordatorios pendientes vencidos o próximos; --dry-run no envía ni modifica.'
    def add_arguments(self,parser):
        parser.add_argument('--dry-run',action='store_true')
        parser.add_argument('--simular',action='store_true',help='Guarda un correo en archivo privado, sin enviarlo ni marcar ENVIADO.')
    def handle(self,*args,**options):
        dry=options['dry_run']
        simulate=options['simular']
        if simulate and settings.MAILERS['default']['BACKEND']!='django.core.mail.backends.filebased.EmailBackend':
            raise CommandError('--simular requiere el backend de archivos privados.')
        if not dry and not simulate:
            if not settings.REMINDERS_ENABLED:raise CommandError('Activa REMINDERS_ENABLED después de configurar y probar el correo.')
            backend=settings.MAILERS['default']['BACKEND']
            if backend!='django.core.mail.backends.smtp.EmailBackend':raise CommandError('El envío real requiere el backend SMTP; la consola no cuenta como entrega.')
        limit=timezone.localdate()+timedelta(days=settings.REMINDER_ADVANCE_DAYS)
        ids=Recordatorio.objects.filter(estado='PENDIENTE',fecha_programada__lte=limit,enviado_en__isnull=True,mascota__tutor__email_verificado=True,mascota__tutor__acepta_recordatorios=True).values_list('pk',flat=True)
        if simulate: ids=ids.filter(simulado_en__isnull=True)
        sent=failed=0
        for pk in list(ids):
            if dry:
                self.stdout.write(f'Elegible: recordatorio {pk}')
                continue
            with transaction.atomic():
                reminder=Recordatorio.objects.select_for_update().filter(pk=pk,estado='PENDIENTE',enviado_en__isnull=True).first()
                if not reminder:continue
                if simulate and reminder.simulado_en:continue
                tutor=reminder.mascota.tutor
                if not tutor.email_verificado or not tutor.acepta_recordatorios:continue
                reminder.intentos+=1
                try:
                    # No diagnoses or prescriptions in emails; details stay behind login.
                    text=f'Hola {tutor.nombre}. Tienes un recordatorio de {reminder.get_tipo_display().lower()} para {reminder.mascota.nombre}, con fecha {reminder.fecha_programada:%d/%m/%Y}. Consulta los detalles en {settings.PUBLIC_BASE_URL}/recordatorios/. Puedes desactivar estos correos en tu perfil.'
                    result=send_mail('PetCare · Próximo cuidado',text,settings.DEFAULT_FROM_EMAIL,[tutor.email],using='default')
                    if result!=1:raise RuntimeError('SMTP no confirmó el envío')
                except Exception as exc:
                    reminder.ultimo_error=type(exc).__name__[:100]
                    failed+=1
                else:
                    if simulate:reminder.simulado_en=timezone.now()
                    else:reminder.estado='ENVIADO';reminder.enviado_en=timezone.now()
                    reminder.ultimo_error='';sent+=1
                reminder.save(update_fields=['intentos','ultimo_error','estado','enviado_en','simulado_en'])
        self.stdout.write(f'Procesados: {sent}; fallidos: {failed}; simulación de archivo: {simulate}; solo consulta: {dry}')
        if failed:raise CommandError('Hubo fallos de envío; los pendientes se reintentarán en la próxima ejecución.')
