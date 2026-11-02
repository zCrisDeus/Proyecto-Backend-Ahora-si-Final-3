from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from usuarios.views import LoginView, verificar_correo
from .views import home_view, login_view, registro_view, tutores_view, mascotas_view, citas_view, profesionales_view, fichas_view, recordatorios_view


schema_view = get_schema_view(
   openapi.Info(
      title="PetCare API",
      default_version='v1',
      description="Documentación interactiva de la API",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('mi-cuenta/', TemplateView.as_view(template_name='dashboard/cuenta.html'), name='cuenta'),
    path('api/usuarios/', include('usuarios.urls')),
    path('verificar-correo/<str:token>/', verificar_correo, name='verificar_correo'),
    path('admin/', admin.site.urls),
    path('api/pacientes/', include('pacientes.urls')),
    path('api/agendamiento/', include('agendamiento.urls')),
    path('api/clinica/', include('clinica.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('registro/', registro_view, name='registro'),
    path('tutores/', tutores_view, name='tutores'),
    path('mascotas/', mascotas_view, name='mascotas'),
    path('citas/', citas_view, name='citas'),
    path('profesionales/', profesionales_view, name='profesionales'),
    path('fichas/', fichas_view, name='fichas'),
    path('recordatorios/', recordatorios_view, name='recordatorios'),
]
