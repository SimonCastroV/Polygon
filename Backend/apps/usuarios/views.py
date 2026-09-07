from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser, RegistroAuditoriaUsuario
from .permissions import EsAdministrador
from .serializers import (
    CambiarPasswordSerializer,
    LoginSerializer,
    UsuarioCreateSerializer,
    UsuarioSerializer,
    UsuarioUpdateSerializer,
)

# Campos que se rastrean en RegistroAuditoriaUsuario cuando cambian.
CAMPOS_AUDITADOS = ['first_name', 'last_name', 'rol', 'is_active']


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'token': token.key,
                'user': UsuarioSerializer(user).data,
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UsuarioListCreateView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all().order_by('username')
    permission_classes = [IsAuthenticated, EsAdministrador]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UsuarioCreateSerializer
        return UsuarioSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


class UsuarioDetailUpdateView(generics.RetrieveUpdateAPIView):
    """
    HU-05 Editar usuario / HU-06 Asignar roles y permisos.

    GET  /api/usuarios/<pk>/  -> detalle del usuario.
    PATCH/PUT /api/usuarios/<pk>/ -> edita nombre, apellido, rol y estado
    (is_active). Cada campo que cambie queda registrado en
    RegistroAuditoriaUsuario.
    """

    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated, EsAdministrador]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UsuarioSerializer
        return UsuarioUpdateSerializer

    def perform_update(self, serializer):
        usuario = self.get_object()
        valores_anteriores = {campo: getattr(usuario, campo) for campo in CAMPOS_AUDITADOS}
        usuario_actualizado = serializer.save()

        for campo in CAMPOS_AUDITADOS:
            valor_anterior = valores_anteriores[campo]
            valor_nuevo = getattr(usuario_actualizado, campo)
            if valor_anterior != valor_nuevo:
                RegistroAuditoriaUsuario.objects.create(
                    usuario=usuario_actualizado,
                    modificado_por=self.request.user,
                    campo=campo,
                    valor_anterior=str(valor_anterior),
                    valor_nuevo=str(valor_nuevo),
                )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = UsuarioSerializer(self.get_object()).data
        return response


class CambiarPasswordView(APIView):
    permission_classes = [IsAuthenticated, EsAdministrador]

    def post(self, request, pk):
        try:
            usuario_objetivo = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CambiarPasswordSerializer(
            data=request.data, context={'usuario_objetivo': usuario_objetivo}
        )
        serializer.is_valid(raise_exception=True)
        usuario_objetivo.set_password(serializer.validated_data['new_password'])
        usuario_objetivo.save()
        return Response({'detail': 'Contraseña actualizada correctamente.'})
