from django.db import models
from django.conf import settings

class Tutor(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='tutor')
    email_verificado = models.BooleanField(default=False, editable=False)
    acepta_recordatorios = models.BooleanField(default=False)
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

class Mascota(models.Model):
    ESPECIES_CHOICES = [
        ('PERRO', 'Perro'),
        ('GATO', 'Gato'),
        ('EXOTICO', 'Exótico'),
        ('OTRO', 'Otro'),
    ]

    # Relación 1 a Muchos: Un tutor puede tener varias mascotas
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='mascotas')
    nombre = models.CharField(max_length=100)
    especie = models.CharField(max_length=20, choices=ESPECIES_CHOICES)
    raza = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = "Mascota"
        verbose_name_plural = "Mascotas"

    def __str__(self):
        return f"{self.nombre} - {self.tutor.nombre}"
