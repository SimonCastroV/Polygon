from rest_framework.permissions import BasePermission


class PuedeGestionarOP(BasePermission):
    """
    HU-10 / HU-11: "Como personal de Planeación...".

    Supuesto: el sistema (apps.usuarios.CustomUser.Rol) solo define los
    roles admin / supervisor / planta; no existe un rol "planeacion". Se
    asume que el personal de Planeación (p. ej. Adriana) opera con el rol
    'supervisor'. Si Sumicolor requiere un rol propio de Planeación, hay
    que agregarlo a CustomUser.Rol y ajustar este permiso.
    """

    message = 'No tiene permisos para gestionar Órdenes de Producción.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.rol in ('admin', 'supervisor')
        )
