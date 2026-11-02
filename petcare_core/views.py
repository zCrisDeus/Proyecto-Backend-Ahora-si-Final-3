from django.shortcuts import render

def home_view(request):
    return render(request, 'dashboard/index.html')

def login_view(request):
    return render(request, 'auth/login.html')

def registro_view(request):
    return render(request, 'auth/registro.html')

def tutores_view(request):
    return render(request, 'pacientes/tutores.html')

def mascotas_view(request):
    return render(request, 'pacientes/mascotas.html')

def citas_view(request):
    return render(request, 'agendamiento/citas.html')

def profesionales_view(request):
    return render(request, 'agendamiento/profesionales.html')

def fichas_view(request):
    return render(request, 'clinica/fichas.html')

def recordatorios_view(request):
    return render(request, 'clinica/recordatorios.html')