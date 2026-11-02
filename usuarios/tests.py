from datetime import timedelta, time
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.db import connection, IntegrityError, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient
from pacientes.models import Tutor, Mascota
from agendamiento.models import Profesional, HorarioProfesional, CitaMedica
from clinica.models import FichaClinica, Recordatorio

class WorkflowTests(TestCase):
    def setUp(self):
        self.u=get_user_model().objects.create_user('ana',password='Prueba-segura-2026')
        self.v=get_user_model().objects.create_user('otro',password='Prueba-segura-2026')
        self.t=Tutor.objects.create(usuario=self.u,rut='11111111-1',nombre='Ana',apellidos='Prueba',email='ana@example.invalid',telefono='111',email_verificado=True,acepta_recordatorios=True)
        self.other=Tutor.objects.create(usuario=self.v,rut='22222222-2',nombre='Otro',apellidos='Prueba',email='otro@example.invalid',telefono='222')
        self.pet=Mascota.objects.create(tutor=self.t,nombre='Luna',especie='GATO')
        self.other_pet=Mascota.objects.create(tutor=self.other,nombre='Rex',especie='PERRO')
        self.pro=Profesional.objects.create(nombre='Vet',apellidos='Prueba',especialidad='General')
        self.day=timezone.localdate()+timedelta(days=2)
        HorarioProfesional.objects.create(profesional=self.pro,dia_semana=self.day.weekday(),inicio=time(9),fin=time(17))
        self.client=APIClient();self.client.force_authenticate(self.u)
        self.payload={'mascota':self.pet.pk,'profesional':self.pro.pk,'fecha':str(self.day),'hora':'10:00','duracion_minutos':30,'motivo':'Control'}
    def staff(self,group):
        user=get_user_model().objects.create_user(group,is_staff=True)
        user.groups.add(Group.objects.get_or_create(name=group)[0]);self.client.force_authenticate(user);return user
    def appointment(self,**changes):
        data=dict(mascota=self.pet,profesional=self.pro,fecha=self.day,hora=time(10),duracion_minutos=30,motivo='Control');data.update(changes);return CitaMedica.objects.create(**data)
    def reminder(self,**changes):
        data=dict(mascota=self.pet,tipo='VACUNA',fecha_programada=timezone.localdate(),mensaje='Recordatorio');data.update(changes);return Recordatorio.objects.create(**data)

    def test_private_lists_and_details(self):
        self.assertEqual([r['id'] for r in self.client.get('/api/pacientes/tutores/').json()],[self.t.pk])
        self.assertEqual(self.client.get(f'/api/pacientes/tutores/{self.other.pk}/').status_code,404)
        self.assertEqual(self.client.patch(f'/api/pacientes/mascotas/{self.other_pet.pk}/',{'nombre':'Robo'}).status_code,404)
        self.assertEqual(self.client.delete(f'/api/pacientes/mascotas/{self.pet.pk}/').status_code,403)
    def test_foreign_relationship_cannot_be_supplied(self):
        self.assertEqual(self.client.post('/api/pacientes/mascotas/',{'nombre':'Intrusa','especie':'GATO','tutor':self.other.pk}).status_code,400)
        self.assertEqual(self.client.post('/api/agendamiento/citas/',dict(self.payload,mascota=self.other_pet.pk)).status_code,400)
    def test_pet_automatically_belongs_to_current_tutor(self):
        response=self.client.post('/api/pacientes/mascotas/',{'nombre':'Nueva','especie':'PERRO'})
        self.assertEqual(response.status_code,201,response.data);self.assertEqual(response.data['tutor'],self.t.pk)
    def test_profile_cannot_rebind_user_or_verify_email(self):
        self.client.patch(f'/api/pacientes/tutores/{self.t.pk}/',{'usuario':self.v.pk,'email_verificado':True,'email':'nueva@example.invalid'})
        self.t.refresh_from_db();self.assertEqual(self.t.usuario,self.u);self.assertFalse(self.t.email_verificado)
    def test_clinical_data_is_scoped_and_tutor_cannot_write(self):
        own=FichaClinica.objects.create(mascota=self.pet,profesional=self.pro,diagnostico='Dato propio',tratamiento='Control')
        other=FichaClinica.objects.create(mascota=self.other_pet,profesional=self.pro,diagnostico='Privado',tratamiento='Control')
        self.assertEqual([r['id'] for r in self.client.get('/api/clinica/fichas/').data],[own.pk])
        self.assertEqual(self.client.get(f'/api/clinica/fichas/{other.pk}/').status_code,404)
        self.assertEqual(self.client.post('/api/clinica/fichas/',{}).status_code,403)
    def test_reminders_are_scoped(self):
        own=self.reminder();self.reminder(mascota=self.other_pet)
        self.assertEqual([r['id'] for r in self.client.get('/api/clinica/recordatorios/').data],[own.pk])
    def test_reception_cannot_read_clinical_data(self):
        self.staff('Recepcion')
        self.assertEqual(self.client.get('/api/clinica/fichas/').status_code,403)
        self.assertEqual(self.client.get('/api/pacientes/tutores/').status_code,200)
        self.assertEqual(self.client.post('/api/agendamiento/profesionales/',{}).status_code,403)
    def test_vet_can_write_clinical_data(self):
        self.staff('Veterinarios')
        response=self.client.post('/api/clinica/fichas/',{'mascota':self.pet.pk,'profesional':self.pro.pk,'diagnostico':'Control','tratamiento':'Control'})
        self.assertEqual(response.status_code,201,response.data)
    def test_staff_without_group_has_no_implicit_access(self):
        user=get_user_model().objects.create_user('staff',is_staff=True);self.client.force_authenticate(user)
        self.assertEqual(self.client.get('/api/pacientes/tutores/').status_code,403)
    def test_public_registration_never_grants_privileges(self):
        self.client.force_authenticate(None)
        payload=dict(username='nuevo',password='Una-clave-larga-945!',password_confirm='Una-clave-larga-945!',nombre='Nueva',apellidos='Persona',email='nueva@example.invalid',rut='12345678-5',telefono='123',is_staff=True,is_superuser=True,rol='administrador')
        response=self.client.post('/api/usuarios/registro/',payload,format='json')
        self.assertEqual(response.status_code,201,response.data)
        u=get_user_model().objects.get(username='nuevo');self.assertFalse(u.is_staff);self.assertFalse(u.is_superuser);self.assertEqual(u.tutor.rut,'12345678-5');self.assertFalse(u.tutor.email_verificado)
    def test_registration_password_validation_and_existing_profile(self):
        self.client.force_authenticate(None)
        payload=dict(username='nuevo',password='12345678',password_confirm='12345678',nombre='Nueva',apellidos='Persona',email='nueva@example.invalid',rut='12345678-5',telefono='123')
        self.assertEqual(self.client.post('/api/usuarios/registro/',payload).status_code,400)
        payload.update(password='Una-clave-larga-945!',password_confirm='Una-clave-larga-945!',email=self.t.email)
        self.assertEqual(self.client.post('/api/usuarios/registro/',payload).status_code,400)
        self.assertFalse(get_user_model().objects.filter(username='nuevo').exists())
    def test_email_confirmation_signed_and_bound_to_current_address(self):
        self.t.email_verificado=False;self.t.save()
        token=signing.dumps({'id':self.t.pk,'email':self.t.email},salt='petcare-email')
        self.assertEqual(self.client.get('/verificar-correo/'+token+'/').status_code,200)
        self.t.refresh_from_db();self.assertFalse(self.t.email_verificado)
        self.assertEqual(self.client.post('/verificar-correo/'+token+'/').status_code,200)
        self.t.refresh_from_db();self.assertTrue(self.t.email_verificado)
        self.assertEqual(self.client.post('/verificar-correo/'+token+'x/').status_code,400)
    def test_slot_overlap_and_adjacency(self):
        self.appointment()
        response=self.client.post('/api/agendamiento/citas/',dict(self.payload,hora='10:15'))
        self.assertEqual(response.status_code,400,response.data)
        self.assertEqual(self.client.post('/api/agendamiento/citas/',dict(self.payload,hora='10:30')).status_code,201)
    def test_cancelled_slot_can_be_reused(self):
        old=self.appointment();self.client.patch(f'/api/agendamiento/citas/{old.pk}/',{'estado':'CANCELADA'})
        self.assertEqual(self.client.post('/api/agendamiento/citas/',self.payload).status_code,201)
    def test_outside_schedule_and_past_rejected(self):
        self.assertEqual(self.client.post('/api/agendamiento/citas/',dict(self.payload,hora='16:45')).status_code,400)
        self.assertEqual(self.client.post('/api/agendamiento/citas/',dict(self.payload,fecha='2000-01-01')).status_code,400)
    def test_tutor_cannot_complete_or_view_others_appointment(self):
        own=self.appointment();other=self.appointment(mascota=self.other_pet,hora=time(11))
        self.assertEqual(self.client.patch(f'/api/agendamiento/citas/{own.pk}/',{'estado':'COMPLETADA'}).status_code,400)
        self.assertEqual(self.client.get(f'/api/agendamiento/citas/{other.pk}/').status_code,404)
    def test_available_slots_do_not_disclose_patients(self):
        self.appointment(mascota=self.other_pet)
        response=self.client.get(f'/api/agendamiento/profesionales/{self.pro.pk}/disponibilidad/?fecha={self.day}&duracion=30')
        self.assertEqual(response.status_code,200);self.assertNotIn('10:00',response.data['horas']);self.assertIn('10:30',response.data['horas']);self.assertNotIn('Rex',str(response.data))
    def test_anonymous_cannot_access_data(self):
        self.client.force_authenticate(None)
        for endpoint in ['pacientes/tutores','pacientes/mascotas','agendamiento/citas','clinica/fichas','clinica/recordatorios']:
            self.assertEqual(self.client.get('/api/'+endpoint+'/').status_code,401)
    def test_jwt_login_and_all_html_routes(self):
        self.client.force_authenticate(None)
        response=self.client.post('/api/token/',{'username':'ana','password':'Prueba-segura-2026'})
        self.assertEqual(response.status_code,200)
        for path in ['','login/','registro/','mi-cuenta/','tutores/','mascotas/','citas/','profesionales/','fichas/','recordatorios/']:
            self.assertEqual(self.client.get('/'+path).status_code,200,path)
    def test_groups_admin_permissions_match_roles(self):
        call_command('configurar_roles',stdout=StringIO())
        group=Group.objects.get(name='Recepcion');self.assertFalse(group.permissions.filter(content_type__app_label='clinica').exists())
        self.assertFalse(group.permissions.filter(codename='change_user').exists())

    @override_settings(REMINDERS_ENABLED=True,MAILERS={'default':{'BACKEND':'django.core.mail.backends.smtp.EmailBackend','OPTIONS':{'host':'unused.invalid'}}})
    @patch('clinica.management.commands.enviar_recordatorios.send_mail',return_value=1)
    def test_reminder_is_sent_once_and_consent_respected(self,send):
        reminder=self.reminder();self.reminder(mascota=self.other_pet)
        call_command('enviar_recordatorios',stdout=StringIO());call_command('enviar_recordatorios',stdout=StringIO())
        reminder.refresh_from_db();self.assertEqual(reminder.estado,'ENVIADO');self.assertEqual(send.call_count,1)
    @override_settings(REMINDERS_ENABLED=True,MAILERS={'default':{'BACKEND':'django.core.mail.backends.smtp.EmailBackend','OPTIONS':{'host':'unused.invalid'}}})
    @patch('clinica.management.commands.enviar_recordatorios.send_mail',side_effect=TimeoutError('private detail'))
    def test_failure_remains_pending_and_does_not_store_secret(self,send):
        reminder=self.reminder()
        with self.assertRaises(CommandError):call_command('enviar_recordatorios',stdout=StringIO())
        reminder.refresh_from_db();self.assertEqual(reminder.estado,'PENDIENTE');self.assertEqual(reminder.ultimo_error,'TimeoutError');self.assertEqual(reminder.intentos,1)
    def test_simulation_creates_file_but_never_marks_delivered(self):
        reminder=self.reminder()
        with TemporaryDirectory(dir=settings.BASE_DIR) as folder:
            with override_settings(MAILERS={'default':{'BACKEND':'django.core.mail.backends.filebased.EmailBackend','OPTIONS':{'file_path':folder}}}):
                call_command('enviar_recordatorios',simular=True,stdout=StringIO())
                call_command('enviar_recordatorios',simular=True,stdout=StringIO())
                from pathlib import Path
                self.assertEqual(len(list(Path(folder).glob('*'))),1)
        reminder.refresh_from_db();self.assertEqual(reminder.estado,'PENDIENTE');self.assertIsNotNone(reminder.simulado_en);self.assertIsNone(reminder.enviado_en)
    def test_dry_run_never_sends_or_changes(self):
        reminder=self.reminder()
        with patch('clinica.management.commands.enviar_recordatorios.send_mail') as send:
            call_command('enviar_recordatorios',dry_run=True,stdout=StringIO());send.assert_not_called()
        reminder.refresh_from_db();self.assertEqual(reminder.intentos,0)
    def test_database_exclusion_blocks_bypassed_model_validation(self):
        if connection.vendor!='postgresql':self.skipTest('Requiere PostgreSQL real')
        self.appointment()
        with self.assertRaises(IntegrityError),transaction.atomic():
            CitaMedica.objects.bulk_create([CitaMedica(mascota=self.other_pet,profesional=self.pro,fecha=self.day,hora=time(10,15),motivo='Conflicto')])

class PostgreSQLConcurrencyTests(TransactionTestCase):
    def test_two_workers_cannot_reserve_same_interval(self):
        if connection.vendor!='postgresql':self.skipTest('Requiere PostgreSQL real')
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections, connections
        tutor=Tutor.objects.create(rut='33333333-3',nombre='Prueba',apellidos='Concurrente',email='test@example.invalid',telefono='1')
        pet=Mascota.objects.create(tutor=tutor,nombre='Prueba',especie='GATO')
        pro=Profesional.objects.create(nombre='Prueba',apellidos='Concurrente',especialidad='General')
        day=timezone.localdate()+timedelta(days=2)
        HorarioProfesional.objects.create(profesional=pro,dia_semana=day.weekday(),inicio=time(9),fin=time(17))
        barrier=Barrier(2)
        def reserve(_):
            close_old_connections();barrier.wait(timeout=10)
            try:
                CitaMedica.objects.create(mascota_id=pet.pk,profesional_id=pro.pk,fecha=day,hora=time(10),motivo='Prueba')
                return 'ok'
            except (IntegrityError,ValidationError):return 'conflicto'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(reserve,range(2)))
        self.assertCountEqual(results,['ok','conflicto'])

class MigrationPreservationTests(TransactionTestCase):
    def test_upgrade_preserves_existing_tutor_and_appointment(self):
        from django.db.migrations.executor import MigrationExecutor
        executor=MigrationExecutor(connection)
        old=[('pacientes','0001_initial'),('agendamiento','0001_initial'),('clinica','0001_initial')]
        executor.migrate(old)
        apps=executor.loader.project_state(old).apps
        T=apps.get_model('pacientes','Tutor');M=apps.get_model('pacientes','Mascota')
        P=apps.get_model('agendamiento','Profesional');C=apps.get_model('agendamiento','CitaMedica')
        t=T.objects.create(rut='44444444-4',nombre='Anterior',apellidos='Prueba',email='old@example.invalid',telefono='4')
        m=M.objects.create(tutor=t,nombre='Anterior',especie='GATO')
        p=P.objects.create(nombre='Anterior',apellidos='Prueba',especialidad='General')
        c=C.objects.create(mascota=m,profesional=p,fecha=timezone.localdate()+timedelta(days=2),hora=time(10),motivo='Existente')
        executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
        self.assertEqual(Tutor.objects.get(pk=t.pk).nombre,'Anterior')
        self.assertIsNone(Tutor.objects.get(pk=t.pk).usuario_id)
        self.assertEqual(CitaMedica.objects.get(pk=c.pk).duracion_minutos,30)
