from rest_framework.permissions import BasePermission


class EsPesaje(BasePermission):
    message = 'Solo Pesaje puede registrar y enviar el pesaje a supervisión.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'pesaje'


class EsSupervisorPesaje(BasePermission):
    """
    Revisa y libera el pesaje el rol 'supervisor' genérico: por ahora no se
    distingue un supervisor por área (Pesaje, Mezcla, etc.). Si más adelante
    el negocio necesita separarlos, se agrega el rol específico y se amplía
    esta comprobación.
    """

    message = 'Solo un Supervisor puede revisar el pesaje.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'supervisor'
