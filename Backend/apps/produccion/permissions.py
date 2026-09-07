from rest_framework.permissions import BasePermission


class PuedeVerOP(BasePermission):
    """
    Consulta de Órdenes de Producción: solo Producción, Supervisor y
    Administrador. 'produccion' es el rol de la estación de Producción
    (primer eslabón del flujo, antes de Picky); no incluye 'planta'
    (Personal de Planta genérico, ej. Pesaje), que no debe ver esta
    pantalla.
    """

    message = 'No tiene permisos para consultar Órdenes de Producción.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in ('admin', 'supervisor', 'produccion')
        )


class EsProduccion(BasePermission):
    """
    Solo Producción (rol 'produccion') diligencia la clasificación y las
    observaciones de una OP al "ingresar" a ella; Admin/Supervisor las
    pueden ver (vía PuedeVerOP) pero no las editan.
    """

    message = 'Solo Producción puede diligenciar la clasificación y las observaciones de la OP.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.rol == 'produccion'
        )
