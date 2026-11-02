from django.urls import path
from .views import RegistroView, MeView, ReenviarVerificacionView
urlpatterns=[path('registro/',RegistroView.as_view()),path('me/',MeView.as_view()),path('reenviar-verificacion/',ReenviarVerificacionView.as_view())]
