from rest_framework.permissions import BasePermission


class PuedeVerOP(BasePermission):
    """
    Consulta de Órdenes de Producción: Producción, Picking, Supervisor y
    Administrador. Picking solo alcanza las OP que Producción ya liberó: ese
    filtro se aplica en el queryset de las vistas (ver
    apps.produccion.views), no aquí. Pesaje solo alcanza su propia cola. El
    Supervisor consulta todas y además revisa el pesaje. Los demás roles
    de estación se incorporarán cuando se construya cada base.
    """

    message = 'No tiene permisos para consultar Órdenes de Producción.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol
            in ('admin', 'supervisor', 'produccion', 'picking', 'pesaje')
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


class EsPicking(BasePermission):
    """
    Solo la estación de Picking (rol 'picking') registra la recepción de una
    OP liberada por Producción. Picking no puede modificar ningún otro dato
    de la orden (ver OrdenProduccionRecepcionPickingSerializer).
    """

    message = 'Solo Picking puede registrar la recepción de la Orden de Producción.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'picking')
