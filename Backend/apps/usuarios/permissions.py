from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    message = 'Solo un Administrador puede realizar esta acción.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'admin')
