from rest_framework.permissions import BasePermission


class PuedeVerOP(BasePermission):
    """
    Consulta de Órdenes de Producción: Producción, Picky, Supervisor y
    Administrador. Picky solo alcanza las OP que Producción ya liberó: ese
    filtro se aplica en el queryset de las vistas (ver
    apps.produccion.views), no aquí. Los demás roles de estación (Pesaje,
    Mezcla, etc.) todavía no tienen acceso, se irán sumando cuando se
    construya cada base.
    """

    message = 'No tiene permisos para consultar Órdenes de Producción.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in ('admin', 'supervisor', 'produccion', 'picky')
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


class EsPicky(BasePermission):
    """
    Solo la estación de Picky (rol 'picky') registra la recepción de una
    OP liberada por Producción. Picky no puede modificar ningún otro dato
    de la orden (ver OrdenProduccionRecepcionPickySerializer).
    """

    message = 'Solo Picky puede registrar la recepción de la Orden de Producción.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.rol == 'picky'
        )
