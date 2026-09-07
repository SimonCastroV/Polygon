from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomUser, RegistroAuditoriaUsuario


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError({'detail': 'Usuario o contraseña incorrectos.'})
        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Usuario inactivo.'})
        attrs['user'] = user
        return attrs


class UsuarioSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'rol',
            'rol_display',
            'is_active',
            'date_joined',
        ]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'rol']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RegistroAuditoriaUsuarioSerializer(serializers.ModelSerializer):
    modificado_por_username = serializers.CharField(
        source='modificado_por.username', read_only=True, default=None
    )

    class Meta:
        model = RegistroAuditoriaUsuario
        fields = [
            'id',
            'campo',
            'valor_anterior',
            'valor_nuevo',
            'modificado_por_username',
            'fecha',
        ]


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    HU-05 (Editar usuario) y HU-06 (Asignar roles y permisos).

    En Polygon los usuarios representan principalmente máquinas/equipos o
    estaciones de trabajo, no personas con nombre propio, por lo que la
    edición de un usuario solo permite cambiar su rol (y activarlo o
    desactivarlo); nombre y apellido no son editables desde este endpoint
    (solo se definen, opcionalmente, al crear el usuario). El rol sigue
    siendo un único CharField, por lo que "cada usuario tiene un único rol
    principal" (regla de negocio de HU-06) se cumple de forma natural.
    """

    class Meta:
        model = CustomUser
        fields = ['rol', 'is_active']

    def validate_rol(self, value):
        if value not in CustomUser.Rol.values:
            raise serializers.ValidationError('Rol no válido.')
        return value


class CambiarPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value, user=self.context.get('usuario_objetivo'))
        return value
