from rest_framework.permissions import BasePermission, SAFE_METHODS

def role(user):
    if not user or not user.is_authenticated or not user.is_active:
        return 'anonimo'
    if user.is_superuser:
        return 'administrador'
    if user.is_staff:
        if user.groups.filter(name='Veterinarios').exists(): return 'veterinario'
        if user.groups.filter(name='Recepcion').exists(): return 'recepcion'
    if hasattr(user, 'tutor'): return 'tutor'
    return 'sin_asignar'

def team(user):
    return role(user) in ('administrador', 'veterinario', 'recepcion')

class PacientesPermission(BasePermission):
    def has_permission(self, request, view):
        r=role(request.user)
        if r=='administrador': return True
        if r in ('veterinario','recepcion'): return request.method != 'DELETE'
        if r!='tutor': return False
        if request.method in SAFE_METHODS: return True
        return request.method in ('POST','PUT','PATCH') and (view.basename=='mascota' or view.action in ('update','partial_update'))

class AgendaPermission(BasePermission):
    def has_permission(self, request, view):
        r=role(request.user)
        if r=='administrador': return True
        if r in ('veterinario','recepcion'): return request.method!='DELETE'
        return r=='tutor' and request.method!='DELETE'

class ProfesionalPermission(BasePermission):
    def has_permission(self, request, view):
        return role(request.user)=='administrador' or (role(request.user) in ('tutor','veterinario','recepcion') and request.method in SAFE_METHODS)

class ClinicaPermission(BasePermission):
    def has_permission(self, request, view):
        r=role(request.user)
        return r=='administrador' or (r=='veterinario' and request.method!='DELETE') or (r=='tutor' and request.method in SAFE_METHODS)
