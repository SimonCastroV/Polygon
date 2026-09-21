from rest_framework.permissions import BasePermission


class PuedeVerOP(BasePermission):
    """
    Consulta de Órdenes de Producción: Producción, Picking, Pesaje,
    Ing. Producción, Supervisor y Administrador. Picking solo alcanza las OP
    que Producción ya liberó: ese filtro se aplica en el queryset de las
    vistas (ver apps.produccion.views), no aquí. Pesaje solo alcanza su
    propia cola e Ing. Producción solo las OP con acompañamiento de IP. El
    Supervisor consulta todas y además revisa el pesaje. Los demás roles
    de estación se incorporarán cuando se construya cada base.
    """

    message = 'No tiene permisos para consultar Órdenes de Producción.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol
            in ('admin', 'supervisor', 'produccion', 'ing_produccion', 'picking', 'pesaje')
        )


class EsProduccion(BasePermission):
    """
    Solo Producción (rol 'produccion') diligencia la hoja de la OP (tipo de
    orden, grupo para Pesaje y observaciones) y la manda a Picking;
    Admin/Supervisor la pueden ver (vía PuedeVerOP) pero no la editan.
    """

    message = 'Solo Producción puede diligenciar la hoja de la OP y mandarla a Picking.'

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
        return bool(
            request.user and request.user.is_authenticated and request.user.rol == 'picking'
        )
