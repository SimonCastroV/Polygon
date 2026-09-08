from rest_framework.permissions import BasePermission


class EsPesaje(BasePermission):
    message = 'Solo Pesaje puede registrar y enviar el pesaje a supervisión.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'pesaje'


class EsSupervisorPesaje(BasePermission):
    message = 'Solo el Supervisor de Pesaje puede revisar el pesaje.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'supervisor_pesaje'
