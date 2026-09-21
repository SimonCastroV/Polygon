from datetime import date
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.usuarios.models import CustomUser

from .models import HistorialOrdenProduccion, OrdenProduccion


class HojaProduccionTests(APITestCase):
    """La hoja de Producción se guarda al mandar la OP a Picking, sin un guardado aparte."""

    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {
            rol: CustomUser.objects.create_user(username=rol, rol=rol)
            for rol in ('produccion', 'ing_produccion', 'picking', 'pesaje', 'supervisor', 'admin')
        }

    def setUp(self):
        self.orden = OrdenProduccion.objects.create(
            codigo_producto='P01',
            referencia='Producto',
            cantidad=10,
            codigo_cliente='C01',
            pedido='001',
            vencimiento_pedido=date(2027, 1, 1),
            creado_por=self.usuarios['produccion'],
        )
        self.client.force_authenticate(self.usuarios['produccion'])

    def enviar(self, datos):
        return self.client.patch(
            reverse('ordenes-enviar-picking', kwargs={'pk': self.orden.pk}), datos, format='json'
        )

    def historial(self):
        return list(
            HistorialOrdenProduccion.objects.filter(orden=self.orden)
            .order_by('id')
            .values_list('campo', 'valor_anterior', 'valor_nuevo')
        )

    def test_enviar_guarda_lo_diligenciado_sin_boton_guardar(self):
        datos = {
            'clasificacion': 'urgente',
            'grupo_critico_pesaje': 'blancos',
            'observaciones': 'Priorizar despacho',
        }
        respuesta = self.enviar(datos)
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'picking')
        self.assertIsNotNone(respuesta.data['fecha_envio_picking'])
        self.orden.refresh_from_db()
        for campo, valor in datos.items():
            self.assertEqual(getattr(self.orden, campo), valor)
        self.assertEqual(
            self.historial(),
            [
                ('clasificacion', 'normal', 'urgente'),
                ('observaciones', '', 'Priorizar despacho'),
                ('grupo_critico_pesaje', '', 'blancos'),
                ('estado', 'produccion', 'picking'),
            ],
        )
        evento = HistorialOrdenProduccion.objects.get(campo='grupo_critico_pesaje')
        self.assertEqual(evento.modificado_por, self.usuarios['produccion'])
        self.assertIn('Blancos', evento.detalle)

    def test_enviar_sin_cambios_solo_registra_el_envio(self):
        self.assertEqual(self.enviar({}).status_code, 200)
        self.assertEqual(self.historial(), [('estado', 'produccion', 'picking')])

    def test_dato_invalido_no_guarda_ni_envia(self):
        respuesta = self.enviar({'clasificacion': 'peligroso', 'observaciones': 'Nota'})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('clasificacion', respuesta.data)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, 'produccion')
        self.assertEqual(self.orden.observaciones, '')
        self.assertEqual(self.historial(), [])

    def test_si_falla_la_trazabilidad_no_queda_nada_a_medias(self):
        with (
            patch('apps.produccion.views.registrar_historial', side_effect=RuntimeError('fallo')),
            self.assertRaises(RuntimeError),
        ):
            self.enviar({'clasificacion': 'urgente'})
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.clasificacion, 'normal')
        self.assertEqual(self.orden.estado, 'produccion')
        self.assertIsNone(self.orden.fecha_envio_picking)

    def test_no_se_reclasifica_ni_reenvia_despues_de_salir_de_produccion(self):
        self.assertEqual(self.enviar({'grupo_critico_pesaje': 'no_critico'}).status_code, 200)
        respuesta = self.enviar({'grupo_critico_pesaje': 'blancos', 'clasificacion': 'urgente'})
        self.assertEqual(respuesta.status_code, 400)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.grupo_critico_pesaje, 'no_critico')
        self.assertEqual(self.orden.clasificacion, 'normal')

    def test_solo_produccion_manda_la_hoja(self):
        for rol in ['ing_produccion', 'picking', 'pesaje', 'supervisor', 'admin']:
            self.client.force_authenticate(self.usuarios[rol])
            with self.subTest(rol=rol):
                self.assertEqual(self.enviar({'clasificacion': 'urgente'}).status_code, 403)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.clasificacion, 'normal')
        self.assertEqual(self.orden.estado, 'produccion')


class IngenieroProduccionTests(APITestCase):
    """Ing. Producción acompaña las OP de hoja azul: las consulta todas, sin editarlas."""

    @classmethod
    def setUpTestData(cls):
        cls.ing = CustomUser.objects.create_user(username='ip', rol='ing_produccion')
        produccion = CustomUser.objects.create_user(username='produccion', rol='produccion')

        def crear(clasificacion, estado='produccion'):
            return OrdenProduccion.objects.create(
                codigo_producto='P01',
                referencia='Producto',
                cantidad=10,
                codigo_cliente='C01',
                pedido='001',
                vencimiento_pedido=date(2027, 1, 1),
                creado_por=produccion,
                clasificacion=clasificacion,
                estado=estado,
            )

        cls.azul = crear('acompanamiento_ip')
        cls.azul_en_mezcla = crear('acompanamiento_ip', estado='mezcla')
        cls.blanca = crear('normal')
        cls.amarilla = crear('urgente', estado='pesaje')

    def setUp(self):
        self.client.force_authenticate(self.ing)

    def detalle(self, orden):
        return self.client.get(reverse('ordenes-detail', kwargs={'pk': orden.pk}))

    def test_solo_ve_las_op_con_acompanamiento_de_ip_en_cualquier_etapa(self):
        respuesta = self.client.get(reverse('ordenes-list'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            {orden['id'] for orden in respuesta.data}, {self.azul.pk, self.azul_en_mezcla.pk}
        )
        self.assertEqual(self.detalle(self.azul_en_mezcla).status_code, 200)
        self.assertIn('historial', self.detalle(self.azul).data)
        for orden in (self.blanca, self.amarilla):
            with self.subTest(clasificacion=orden.clasificacion):
                self.assertEqual(self.detalle(orden).status_code, 404)

    def test_no_edita_ni_mueve_la_op(self):
        acciones = [
            ('ordenes-enviar-picking', {}),
            ('ordenes-recepcion-picking', {'nombre_operario_picking': 'Luis'}),
            ('ordenes-enviar-pesaje', {}),
            ('pesaje-guardar', {'nombre_operario': 'Ana'}),
            ('pesaje-aprobar', {}),
        ]
        for nombre, datos in acciones:
            with self.subTest(accion=nombre):
                url = reverse(nombre, kwargs={'pk': self.azul.pk})
                self.assertEqual(self.client.patch(url, datos, format='json').status_code, 403)
        self.azul.refresh_from_db()
        self.assertEqual(self.azul.estado, 'produccion')
        self.assertEqual(self.azul.clasificacion, 'acompanamiento_ip')
