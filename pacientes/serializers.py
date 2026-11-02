from rest_framework import serializers
from .models import Tutor, Mascota
from usuarios.permissions import team

class MascotaSerializer(serializers.ModelSerializer):
    tutor_nombre = serializers.CharField(source='tutor.__str__', read_only=True)
    class Meta:
        model = Mascota
        fields = '__all__'
        extra_kwargs = {'tutor': {'required': False}}

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        request=self.context.get('request')
        if request and not team(request.user):
            self.fields['tutor'].queryset=Tutor.objects.filter(usuario=request.user)

    def validate(self,attrs):
        request=self.context.get('request')
        if request and not team(request.user):
            tutor=Tutor.objects.filter(usuario=request.user).first()
            if not tutor: raise serializers.ValidationError('Tu cuenta no tiene un perfil de tutor.')
            attrs['tutor']=tutor
        elif not self.instance and not attrs.get('tutor'):
            raise serializers.ValidationError({'tutor':'Selecciona un tutor.'})
        return attrs

class TutorSerializer(serializers.ModelSerializer):
    mascotas = MascotaSerializer(many=True, read_only=True)
    class Meta:
        model = Tutor
        fields = '__all__'
        read_only_fields = ('usuario','email_verificado','fecha_registro')

    def validate_email(self,value):
        value=value.lower()
        qs=Tutor.objects.filter(email__iexact=value)
        if self.instance:qs=qs.exclude(pk=self.instance.pk)
        if qs.exists():raise serializers.ValidationError('Ese correo ya está en uso.')
        return value

    def update(self,instance,validated_data):
        if 'email' in validated_data and validated_data['email'].lower()!=instance.email.lower():
            instance.email_verificado=False
        return super().update(instance,validated_data)
