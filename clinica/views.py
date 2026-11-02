from rest_framework import viewsets
from .models import FichaClinica, Recordatorio
from .serializers import FichaClinicaSerializer, RecordatorioSerializer
from usuarios.permissions import ClinicaPermission, role

class ClinicalScope:
    permission_classes=[ClinicaPermission]
    def get_queryset(self):
        qs=super().get_queryset().select_related('mascota','mascota__tutor')
        r=role(self.request.user)
        if r in ('administrador','veterinario'):return qs
        return qs.filter(mascota__tutor__usuario=self.request.user) if r=='tutor' else qs.none()

class FichaClinicaViewSet(ClinicalScope,viewsets.ModelViewSet):
    queryset=FichaClinica.objects.all()
    serializer_class=FichaClinicaSerializer

class RecordatorioViewSet(ClinicalScope,viewsets.ModelViewSet):
    queryset=Recordatorio.objects.all()
    serializer_class=RecordatorioSerializer
