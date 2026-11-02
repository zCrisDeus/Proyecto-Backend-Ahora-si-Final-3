from rest_framework import serializers
from .models import FichaClinica, Recordatorio

class FichaClinicaSerializer(serializers.ModelSerializer):
    mascota_nombre=serializers.CharField(source='mascota.nombre',read_only=True)
    profesional_nombre=serializers.CharField(source='profesional.__str__',read_only=True)
    class Meta:
        model = FichaClinica
        fields = '__all__'

class RecordatorioSerializer(serializers.ModelSerializer):
    mascota_nombre=serializers.CharField(source='mascota.nombre',read_only=True)
    class Meta:
        model = Recordatorio
        fields = '__all__'
        read_only_fields = ('enviado_en','simulado_en','intentos','ultimo_error')
