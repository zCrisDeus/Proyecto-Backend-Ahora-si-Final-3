from datetime import datetime, timedelta
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from pacientes.models import Mascota

class Profesional(models.Model):
    nombre=models.CharField(max_length=100)
    apellidos=models.CharField(max_length=100)
    especialidad=models.CharField(max_length=100)
    activo=models.BooleanField(default=True)
    class Meta:
        verbose_name='Profesional'
        verbose_name_plural='Profesionales'
    def __str__(self): return f'Dr/a. {self.nombre} {self.apellidos} - {self.especialidad}'

class HorarioProfesional(models.Model):
    profesional=models.ForeignKey(Profesional,on_delete=models.CASCADE,related_name='horarios')
    dia_semana=models.PositiveSmallIntegerField(choices=list(enumerate(['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'])))
    inicio=models.TimeField()
    fin=models.TimeField()
    class Meta:
        ordering=['dia_semana','inicio']
        constraints=[models.CheckConstraint(condition=models.Q(fin__gt=models.F('inicio')),name='horario_fin_mayor_inicio')]
    def clean(self):
        if self.inicio and self.fin and self.fin<=self.inicio: raise ValidationError('La hora final debe ser posterior a la inicial.')
    def __str__(self):return f'{self.profesional} · {self.get_dia_semana_display()} {self.inicio}-{self.fin}'

class CitaMedica(models.Model):
    ESTADOS_CHOICES=[('PROGRAMADA','Programada'),('COMPLETADA','Completada'),('CANCELADA','Cancelada')]
    mascota=models.ForeignKey(Mascota,on_delete=models.CASCADE,related_name='citas')
    profesional=models.ForeignKey(Profesional,on_delete=models.CASCADE,related_name='citas')
    fecha=models.DateField()
    hora=models.TimeField()
    duracion_minutos=models.PositiveSmallIntegerField(default=30,validators=[MinValueValidator(15),MaxValueValidator(240)])
    motivo=models.TextField()
    estado=models.CharField(max_length=20,choices=ESTADOS_CHOICES,default='PROGRAMADA')
    class Meta:
        verbose_name='Cita Médica'
        verbose_name_plural='Citas Médicas'
        ordering=['fecha','hora']
        constraints=[models.CheckConstraint(condition=models.Q(duracion_minutos__gte=15,duracion_minutos__lte=240),name='cita_duracion_valida')]
    @property
    def inicio(self):return datetime.combine(self.fecha,self.hora)
    @property
    def fin(self):return self.inicio+timedelta(minutes=self.duracion_minutos)
    def clean(self):
        if not all([self.fecha,self.hora,self.profesional_id,self.mascota_id,self.duracion_minutos]):return
        if self.estado=='CANCELADA':return
        if self.fin.date()!=self.fecha:raise ValidationError('La cita debe terminar el mismo día.')
        old=type(self).objects.filter(pk=self.pk).first() if self.pk else None
        changed=not old or any(getattr(old,k)!=getattr(self,k) for k in ['fecha','hora','duracion_minutos','profesional_id','mascota_id']) or old.estado=='CANCELADA'
        if changed:
            if timezone.make_aware(self.inicio)<timezone.now():raise ValidationError('No se puede reservar una cita en el pasado.')
            if not self.profesional.activo:raise ValidationError('El profesional no está activo.')
            if not self.profesional.horarios.filter(dia_semana=self.fecha.weekday(),inicio__lte=self.hora,fin__gte=self.fin.time()).exists():raise ValidationError('La cita está fuera de la disponibilidad del profesional.')
        conflicts=type(self).objects.filter(fecha=self.fecha).exclude(estado='CANCELADA').exclude(pk=self.pk).filter(models.Q(profesional_id=self.profesional_id)|models.Q(mascota_id=self.mascota_id))
        if any(self.inicio<c.fin and self.fin>c.inicio for c in conflicts):raise ValidationError('La cita se superpone con otra del profesional o de la mascota.')
    def save(self,*args,**kwargs):
        with transaction.atomic():
            # Serialize normal application writes; PostgreSQL also enforces exclusions.
            list(Profesional.objects.select_for_update().filter(pk=self.profesional_id))
            self.full_clean()
            return super().save(*args,**kwargs)
    def __str__(self):return f'{self.fecha} {self.hora} | {self.mascota.nombre} con {self.profesional.nombre}'
