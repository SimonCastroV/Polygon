from django.urls import reverse
from rest_framework.test import APITestCase

from .models import CustomUser, RegistroAuditoriaUsuario


class EdicionUsuariosTests(APITestCase):
    """
    HU-05/HU-06: editar usuarios y asignar roles. La regla crítica es que un
    administrador no puede quitarse a sí mismo el acceso, porque dejaría el
    sistema sin quien administre usuarios.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(username='admin1', rol='admin')
        cls.otro_admin = CustomUser.objects.create_user(username='admin2', rol='admin')
        cls.operario = CustomUser.objects.create_user(username='pesaje1', rol='pesaje')

    def setUp(self):
        self.client.force_authenticate(self.admin)

    def editar(self, usuario, datos):
        return self.client.patch(
            reverse('usuarios-detail-update', kwargs={'pk': usuario.pk}), datos, format='json'
        )

    def test_admin_no_puede_cambiar_su_propio_rol(self):
        respuesta = self.editar(self.admin, {'rol': 'pesaje'})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('rol', respuesta.data)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.rol, 'admin')

    def test_admin_no_puede_desactivarse_a_si_mismo(self):
        respuesta = self.editar(self.admin, {'is_active': False})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('is_active', respuesta.data)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_puede_guardar_su_cuenta_sin_cambiar_rol_ni_estado(self):
        respuesta = self.editar(self.admin, {'rol': 'admin', 'is_active': True})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)

    def test_admin_sigue_editando_a_los_demas(self):
        respuesta = self.editar(self.otro_admin, {'rol': 'supervisor', 'is_active': False})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.otro_admin.refresh_from_db()
        self.assertEqual(self.otro_admin.rol, 'supervisor')
        self.assertFalse(self.otro_admin.is_active)
        campos = RegistroAuditoriaUsuario.objects.filter(usuario=self.otro_admin).values_list(
            'campo', flat=True
        )
        self.assertCountEqual(campos, ['rol', 'is_active'])

    def test_solo_el_administrador_edita_usuarios(self):
        for usuario in (self.operario, CustomUser.objects.create_user(username='sup', rol='supervisor')):
            self.client.force_authenticate(usuario)
            with self.subTest(rol=usuario.rol):
                self.assertEqual(self.editar(self.operario, {'rol': 'admin'}).status_code, 403)
        self.operario.refresh_from_db()
        self.assertEqual(self.operario.rol, 'pesaje')

    def test_usuario_inactivo_no_inicia_sesion(self):
        self.operario.is_active = False
        self.operario.set_password('Clave-Segura-123')
        self.operario.save()
        self.client.force_authenticate(None)
        respuesta = self.client.post(
            reverse('login'), {'username': 'pesaje1', 'password': 'Clave-Segura-123'}, format='json'
        )
        self.assertEqual(respuesta.status_code, 400)
