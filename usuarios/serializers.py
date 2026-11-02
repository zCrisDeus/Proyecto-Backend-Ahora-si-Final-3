from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from rest_framework import serializers
from pacientes.models import Tutor
import re

class RegistroSerializer(serializers.Serializer):
    username=serializers.CharField(max_length=150,validators=[UnicodeUsernameValidator()])
    password=serializers.CharField(write_only=True,trim_whitespace=False)
    password_confirm=serializers.CharField(write_only=True,trim_whitespace=False)
    nombre=serializers.CharField(max_length=100)
    apellidos=serializers.CharField(max_length=100)
    email=serializers.EmailField(max_length=254)
    rut=serializers.CharField(max_length=12)
    telefono=serializers.CharField(max_length=15)
    acepta_recordatorios=serializers.BooleanField(default=False)

    def validate_rut(self,value):
        value=value.replace('.','').replace('-','').upper().strip()
        if not re.fullmatch(r'\d{7,8}[0-9K]',value): raise serializers.ValidationError('Escribe un RUT válido.')
        digits,check=value[:-1],value[-1]
        n=11-sum(int(d)*(2+i%6) for i,d in enumerate(reversed(digits)))%11
        if check!={10:'K',11:'0'}.get(n,str(n)): raise serializers.ValidationError('El dígito verificador no es válido.')
        # Do not claim preexisting clinical records based only on a supplied RUT.
        existing=Tutor.objects.values_list('rut',flat=True)
        if any(re.sub(r'[.\-]','',r).upper()==value for r in existing):
            raise serializers.ValidationError('No se puede registrar ese RUT. Contacta a la clínica si ya tienes ficha.')
        return digits+'-'+check

    def validate(self,attrs):
        User=get_user_model()
        if attrs['password']!=attrs.pop('password_confirm'): raise serializers.ValidationError({'password_confirm':'Las contraseñas no coinciden.'})
        attrs['email']=attrs['email'].lower()
        if User.objects.filter(username__iexact=attrs['username']).exists(): raise serializers.ValidationError({'username':'No disponible.'})
        if Tutor.objects.filter(email__iexact=attrs['email']).exists() or User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({'email':'No se puede usar ese correo. Contacta a la clínica si ya tienes cuenta.'})
        user=User(username=attrs['username'],email=attrs['email'],first_name=attrs['nombre'],last_name=attrs['apellidos'])
        try: password_validation.validate_password(attrs['password'],user=user)
        except DjangoValidationError as exc: raise serializers.ValidationError({'password':exc.messages})
        return attrs

    def create(self,data):
        try:
            with transaction.atomic():
                user=get_user_model().objects.create_user(username=data.pop('username'),password=data.pop('password'),email=data['email'],first_name=data['nombre'],last_name=data['apellidos'])
                Tutor.objects.create(usuario=user,**data)
                return user
        except IntegrityError:
            raise serializers.ValidationError('No se pudo registrar la cuenta con esos datos.')
