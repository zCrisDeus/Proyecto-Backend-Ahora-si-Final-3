from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FichaClinicaViewSet, RecordatorioViewSet

router = DefaultRouter()
router.register(r'fichas', FichaClinicaViewSet)
router.register(r'recordatorios', RecordatorioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]