from rest_framework import viewsets
from .models import Tutor, Mascota
from .serializers import TutorSerializer, MascotaSerializer
from usuarios.permissions import PacientesPermission, team

class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer
    permission_classes = [PacientesPermission]
    def get_queryset(self):
        qs=super().get_queryset().prefetch_related('mascotas')
        return qs if team(self.request.user) else qs.filter(usuario=self.request.user)

class MascotaViewSet(viewsets.ModelViewSet):
    queryset = Mascota.objects.all()
    serializer_class = MascotaSerializer
    permission_classes = [PacientesPermission]
    def get_queryset(self):
        qs=super().get_queryset().select_related('tutor')
        return qs if team(self.request.user) else qs.filter(tutor__usuario=self.request.user)
