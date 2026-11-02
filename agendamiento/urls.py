from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfesionalViewSet, CitaMedicaViewSet, HorarioViewSet

router = DefaultRouter()
router.register(r'horarios', HorarioViewSet)
router.register(r'profesionales', ProfesionalViewSet)
router.register(r'citas', CitaMedicaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
