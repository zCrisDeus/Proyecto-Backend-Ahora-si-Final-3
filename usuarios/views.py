from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import render
from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from pacientes.models import Tutor
from .serializers import RegistroSerializer
from .permissions import role
import logging

def send_verification(tutor):
    token=signing.dumps({'id':tutor.pk,'email':tutor.email},salt='petcare-email')
    url=settings.PUBLIC_BASE_URL+'/verificar-correo/'+token+'/'
    send_mail('Confirma tu correo en PetCare', 'Para habilitar los recordatorios, confirma tu correo en este enlace (válido por 24 horas):\n'+url, settings.DEFAULT_FROM_EMAIL,[tutor.email],using='default')

class RegistroView(generics.CreateAPIView):
    serializer_class=RegistroSerializer
    permission_classes=[permissions.AllowAny]
    authentication_classes=[]
    throttle_classes=[ScopedRateThrottle]
    throttle_scope='registro'
    def create(self,request,*args,**kwargs):
        serializer=self.get_serializer(data=request.data);serializer.is_valid(raise_exception=True)
        user=serializer.save()
        sent=True
        try: send_verification(user.tutor)
        except Exception:
            sent=False
            logging.getLogger(__name__).warning('Verificación pendiente para tutor %s',user.tutor.pk)
        simulated=settings.MAILERS['default']['BACKEND']!='django.core.mail.backends.smtp.EmailBackend'
        return Response({'detail':'Cuenta creada. Ya puedes iniciar sesión.', 'verificacion_generada':sent,'correo_simulado':simulated},status=201)

class LoginView(TokenObtainPairView):
    throttle_classes=[ScopedRateThrottle]
    throttle_scope='login'

class MeView(APIView):
    def get(self,request):
        tutor=Tutor.objects.filter(usuario=request.user).first()
        return Response({'username':request.user.username,'rol':role(request.user),'tutor_id':tutor.pk if tutor else None,'email_verificado':tutor.email_verificado if tutor else None})

class ReenviarVerificacionView(APIView):
    throttle_classes=[ScopedRateThrottle]
    throttle_scope='verificar'
    def post(self,request):
        tutor=Tutor.objects.filter(usuario=request.user).first()
        if not tutor: return Response({'detail':'No hay perfil de tutor.'},status=403)
        if tutor.email_verificado: return Response({'detail':'Tu correo ya está confirmado.'})
        try: send_verification(tutor)
        except Exception: return Response({'detail':'El servicio de correo no está disponible. Intenta más tarde.'},status=503)
        return Response({'detail':'Revisa tu correo para confirmar la dirección.'})

def verificar_correo(request,token):
    ok=False
    try:
        data=signing.loads(token,salt='petcare-email',max_age=86400)
        tutor=Tutor.objects.get(pk=data['id'],email=data['email'])
        if request.method=='POST':
            Tutor.objects.filter(pk=tutor.pk,email=data['email']).update(email_verificado=True)
            ok=True
        return render(request,'auth/verificar.html',{'ok':ok,'valido':True})
    except (signing.BadSignature,Tutor.DoesNotExist,KeyError):
        return render(request,'auth/verificar.html',{'valido':False},status=400)
