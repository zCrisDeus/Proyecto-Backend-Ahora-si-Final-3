from django.db import models
from pacientes.models import Mascota
from agendamiento.models import Profesional

class FichaClinica(models.Model):
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='fichas')
    profesional = models.ForeignKey(Profesional, on_delete=models.SET_NULL, null=True)
    fecha_atencion = models.DateTimeField(auto_now_add=True)
    diagnostico = models.TextField()
    tratamiento = models.TextField()
    receta_medica = models.TextField(blank=True, null=True, help_text="Medicamentos recetados")
    examenes = models.TextField(blank=True, null=True, help_text="Exámenes solicitados o resultados")

    class Meta:
        verbose_name = "Ficha Clínica"
        verbose_name_plural = "Fichas Clínicas"

    def __str__(self):
        return f"Ficha de {self.mascota.nombre} - {self.fecha_atencion.strftime('%d/%m/%Y')}"

class Recordatorio(models.Model):
    simulado_en = models.DateTimeField(null=True, blank=True, editable=False)
    enviado_en = models.DateTimeField(null=True, blank=True, editable=False)
    intentos = models.PositiveIntegerField(default=0, editable=False)
    ultimo_error = models.CharField(max_length=100, blank=True, editable=False)
    TIPO_CHOICES = [
        ('VACUNA', 'Vacunación'),
        ('CONTROL', 'Control Periódico'),
    ]
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADO', 'Enviado'),
        ('COMPLETADO', 'Completado'),
    ]

    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='recordatorios')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha_programada = models.DateField()
    mensaje = models.TextField(help_text="Mensaje preventivo para el tutor")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    class Meta:
        verbose_name = "Recordatorio"
        verbose_name_plural = "Recordatorios"

    def __str__(self):
        return f"{self.tipo} para {self.mascota.nombre} - {self.fecha_programada}"
