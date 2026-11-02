from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TutorViewSet, MascotaViewSet

router = DefaultRouter()
router.register(r'tutores', TutorViewSet)
router.register(r'mascotas', MascotaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]