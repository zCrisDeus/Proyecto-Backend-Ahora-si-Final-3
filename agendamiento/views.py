from datetime import date, datetime, timedelta
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from usuarios.permissions import AgendaPermission, ProfesionalPermission, team
from .models import Profesional, CitaMedica, HorarioProfesional
from .serializers import ProfesionalSerializer, CitaMedicaSerializer, HorarioSerializer

class ProfesionalViewSet(viewsets.ModelViewSet):
    queryset=Profesional.objects.all()
    serializer_class=ProfesionalSerializer
    permission_classes=[ProfesionalPermission]
    def get_queryset(self):
        qs=super().get_queryset().prefetch_related('horarios')
        return qs if team(self.request.user) else qs.filter(activo=True)
    @action(detail=True,methods=['get'])
    def disponibilidad(self,request,pk=None):
        professional=self.get_object()
        try:
            day=date.fromisoformat(request.query_params['fecha'])
            duration=int(request.query_params.get('duracion',30))
            if duration<15 or duration>240 or day<timezone.localdate():raise ValueError()
        except (KeyError,ValueError):return Response({'detail':'Indica fecha futura YYYY-MM-DD y duración entre 15 y 240 minutos.'},status=400)
        if not professional.activo:return Response({'horas':[]})
        busy=list(CitaMedica.objects.filter(profesional=professional,fecha=day).exclude(estado='CANCELADA'))
        slots=set()
        for schedule in professional.horarios.filter(dia_semana=day.weekday()):
            start=datetime.combine(day,schedule.inicio);end=datetime.combine(day,schedule.fin)
            while start+timedelta(minutes=duration)<=end:
                finish=start+timedelta(minutes=duration)
                if timezone.make_aware(start)>timezone.now() and not any(start<c.fin and finish>c.inicio for c in busy):slots.add(start.strftime('%H:%M'))
                start+=timedelta(minutes=15)
        return Response({'fecha':day,'duracion':duration,'horas':sorted(slots)})

class HorarioViewSet(viewsets.ModelViewSet):
    queryset=HorarioProfesional.objects.all()
    serializer_class=HorarioSerializer
    permission_classes=[ProfesionalPermission]

class CitaMedicaViewSet(viewsets.ModelViewSet):
    queryset=CitaMedica.objects.all()
    serializer_class=CitaMedicaSerializer
    permission_classes=[AgendaPermission]
    def get_queryset(self):
        qs=super().get_queryset().select_related('mascota','profesional')
        return qs if team(self.request.user) else qs.filter(mascota__tutor__usuario=self.request.user)
