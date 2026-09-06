from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser
from .permissions import EsAdministrador
from .serializers import (
    CambiarPasswordSerializer,
    LoginSerializer,
    UsuarioCreateSerializer,
    UsuarioSerializer,
)


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
