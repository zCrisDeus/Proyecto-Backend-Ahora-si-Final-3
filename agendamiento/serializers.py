from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from pacientes.models import Mascota
from usuarios.permissions import role, team
from .models import Profesional, CitaMedica, HorarioProfesional

class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model=HorarioProfesional
        fields='__all__'
    def validate(self,attrs):
        inicio=attrs.get('inicio',getattr(self.instance,'inicio',None))
        fin=attrs.get('fin',getattr(self.instance,'fin',None))
        if inicio and fin and fin<=inicio:raise serializers.ValidationError('La hora final debe ser posterior a la inicial.')
        return attrs

class ProfesionalSerializer(serializers.ModelSerializer):
    horarios=HorarioSerializer(many=True,read_only=True)
    class Meta:
        model=Profesional
        fields='__all__'

class CitaMedicaSerializer(serializers.ModelSerializer):
    mascota_nombre=serializers.CharField(source='mascota.nombre',read_only=True)
    profesional_nombre=serializers.CharField(source='profesional.__str__',read_only=True)
    class Meta:
        model=CitaMedica
        fields='__all__'
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        request=self.context.get('request')
        if request and not team(request.user):
            self.fields['mascota'].queryset=Mascota.objects.filter(tutor__usuario=request.user)
            self.fields['profesional'].queryset=Profesional.objects.filter(activo=True)
    def validate(self,attrs):
        request=self.context.get('request')
        if request and role(request.user)=='tutor':
            if self.instance:
                if self.instance.estado!='PROGRAMADA':raise serializers.ValidationError('Solo puedes modificar citas programadas.')
                if attrs.get('estado','PROGRAMADA') not in ('PROGRAMADA','CANCELADA'):raise serializers.ValidationError('No puedes completar una atención médica.')
            elif attrs.get('estado','PROGRAMADA')!='PROGRAMADA':raise serializers.ValidationError('Las nuevas citas deben estar programadas.')
        candidate=CitaMedica()
        if self.instance:
            for field in CitaMedica._meta.concrete_fields:setattr(candidate,field.attname,getattr(self.instance,field.attname))
        for key,value in attrs.items():setattr(candidate,key,value)
        try:candidate.clean()
        except DjangoValidationError as exc:raise serializers.ValidationError(exc.messages)
        return attrs
    def create(self,data):
        try:
            with transaction.atomic():return super().create(data)
        except (IntegrityError,DjangoValidationError):raise serializers.ValidationError('La hora dejó de estar disponible o no es válida. Consulta la agenda nuevamente.')
    def update(self,instance,data):
        try:
            with transaction.atomic():return super().update(instance,data)
        except (IntegrityError,DjangoValidationError):raise serializers.ValidationError('La hora dejó de estar disponible o no es válida. Consulta la agenda nuevamente.')
