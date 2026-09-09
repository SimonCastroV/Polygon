from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.produccion.models import HistorialOrdenProduccion, MaterialOrden, OrdenProduccion
from apps.usuarios.models import CustomUser

from .models import VERIFICACIONES, VERIFICACIONES_CRITICAS, PesoMaterial, RegistroPesaje


class FlujoPesajeTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {
            rol: CustomUser.objects.create_user(username=rol, rol=rol)
            for rol in ('produccion', 'picky', 'pesaje', 'supervisor', 'admin')
        }
        cls.orden = OrdenProduccion.objects.create(
            grupo_critico_pesaje='no_critico',
            codigo_producto='P01',
            referencia='Producto actual',
            cantidad=10,
            codigo_cliente='C01',
            pedido='001',
            vencimiento_pedido=date(2027, 1, 1),
            creado_por=cls.usuarios['produccion'],
            estado='pesaje',
        )
        cls.material = MaterialOrden.objects.create(
            orden=cls.orden, codigo='M01', descripcion='Pigmento', porcentaje=100, cantidad=10
        )

    def setUp(self):
        self.client.force_authenticate(self.usuarios['pesaje'])

    def datos_base(self):
        """Campos comunes a los dos formularios (crítico y estándar)."""
        return {
            'lote_anterior': 'L001',
            'referencia_anterior': 'Referencia anterior',
            'lote_actual': 'L002',
            'nombre_operario': 'Ana Pérez',
            'pesos': [{'material': self.material.pk, 'peso_real': '10.1250'}],
        }

    def datos(self):
        """Formulario estándar: solo lo responde una OP no crítica."""
        return {
            **self.datos_base(),
            'observaciones': 'Registro de prueba',
            **dict.fromkeys([campo for campo, _ in VERIFICACIONES], True),
        }

    def accion(self, nombre, datos=None):
        return self.client.patch(
            reverse(f'pesaje-{nombre}', kwargs={'pk': self.orden.pk}),
            datos if datos is not None else {},
            format='json',
        )

    def enviar(self):
        respuesta = self.accion('enviar', self.datos())
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        return respuesta

    def test_no_envia_incompleto_ni_crea_borrador_en_error(self):
        respuesta = self.accion('enviar')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('lote_actual', respuesta.data)
        self.assertIn('pesos', respuesta.data)
        self.assertFalse(RegistroPesaje.objects.exists())
        self.assertFalse(HistorialOrdenProduccion.objects.exists())
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, 'pesaje')

    def test_todas_las_verificaciones_y_campos_son_obligatorios(self):
        for campo in [
            'lote_anterior',
            'referencia_anterior',
            'lote_actual',
            'nombre_operario',
            *[campo for campo, _ in VERIFICACIONES],
        ]:
            with self.subTest(campo=campo):
                datos = self.datos()
                datos.pop(campo)
                respuesta = self.accion('enviar', datos)
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.data)

    def test_guarda_borrador_y_peso_sin_alterar_formula(self):
        datos = {'lote_actual': 'L002', 'pesos': self.datos()['pesos']}
        respuesta = self.accion('guardar', datos)
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.material.refresh_from_db()
        self.assertEqual(self.material.cantidad, 10)
        self.assertEqual(PesoMaterial.objects.get().peso_real, Decimal('10.1250'))
        registro = RegistroPesaje.objects.get()
        self.assertIsNone(registro.productos_retirados)
        self.assertEqual(registro.registrado_por, self.usuarios['pesaje'])
        self.assertIsNotNone(registro.fecha_recepcion)
        self.assertEqual(registro.referencia_actual, self.orden.referencia)
        self.assertIsNotNone(respuesta.data['pesaje'])

    def test_envia_datos_guardados_y_no_cumple_es_respuesta_explicita(self):
        datos = self.datos()
        datos['piso_limpio'] = False
        self.assertEqual(self.accion('guardar', datos).status_code, 200)
        respuesta = self.accion('enviar')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertIs(respuesta.data['pesaje']['piso_limpio'], False)
        self.assertEqual(respuesta.data['estado'], 'supervision_pesaje')
        self.assertIsNotNone(respuesta.data['pesaje']['fecha_envio_supervision'])

    def test_pesos_invalidos_y_precision(self):
        for peso in ['0', '-1', 'NaN', 'Infinity', '1.12345', '10000000000', '']:
            with self.subTest(peso=peso):
                datos = self.datos()
                datos['pesos'][0]['peso_real'] = peso
                self.assertEqual(self.accion('enviar', datos).status_code, 400)
        self.assertFalse(PesoMaterial.objects.exists())

    def test_rechaza_material_ajeno_duplicado_y_pendiente(self):
        otra = OrdenProduccion.objects.create(
            codigo_producto='P02',
            referencia='Otra',
            cantidad=1,
            codigo_cliente='C',
            pedido='2',
            vencimiento_pedido=date(2027, 1, 1),
            creado_por=self.usuarios['produccion'],
        )
        ajeno = MaterialOrden.objects.create(
            orden=otra, codigo='AJENO', descripcion='Otro', porcentaje=100, cantidad=1
        )
        for pesos in [[], [{'material': ajeno.pk, 'peso_real': '1'}], self.datos()['pesos'] * 2]:
            with self.subTest(pesos=pesos):
                datos = self.datos()
                datos['pesos'] = pesos
                self.assertEqual(self.accion('enviar', datos).status_code, 400)

    def test_orden_sin_materiales_no_se_envia(self):
        self.material.delete()
        datos = self.datos()
        datos['pesos'] = []
        self.assertEqual(self.accion('enviar', datos).status_code, 400)

    def test_peso_parcial_no_produce_error_interno(self):
        for peso in [{}, {'material': self.material.pk}, {'peso_real': '1'}]:
            with self.subTest(peso=peso):
                self.assertEqual(self.accion('guardar', {'pesos': [peso]}).status_code, 400)
        self.assertFalse(RegistroPesaje.objects.exists())

    def test_no_edita_en_supervision_ni_repite_envio(self):
        self.enviar()
        self.assertEqual(self.accion('guardar', self.datos()).status_code, 400)
        self.assertEqual(self.accion('enviar', self.datos()).status_code, 400)
        self.assertEqual(HistorialOrdenProduccion.objects.filter(campo='estado').count(), 1)

    def test_solo_supervisor_aprueba_o_devuelve(self):
        self.enviar()
        for rol in ['pesaje', 'picky', 'produccion', 'admin']:
            self.client.force_authenticate(self.usuarios[rol])
            for accion in ['aprobar', 'devolver']:
                with self.subTest(rol=rol, accion=accion):
                    self.assertEqual(self.accion(accion, {'motivo': 'Corregir'}).status_code, 403)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, 'supervision_pesaje')

    def test_pesaje_no_puede_enviar_directamente_a_mezcla(self):
        respuesta = self.accion('guardar', {'estado': 'mezcla', 'revision': 'aprobada'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['estado'], 'pesaje')
        self.assertEqual(respuesta.data['pesaje']['revision'], '')
        self.assertEqual(self.accion('aprobar').status_code, 403)
        self.assertEqual(self.accion('devolver', {'motivo': 'x'}).status_code, 403)

    def test_supervisor_no_edita_el_formulario(self):
        self.client.force_authenticate(self.usuarios['supervisor'])
        self.assertEqual(self.accion('guardar', self.datos()).status_code, 403)
        self.assertEqual(self.accion('enviar', self.datos()).status_code, 403)

    def test_devolucion_exige_motivo(self):
        self.enviar()
        self.client.force_authenticate(self.usuarios['supervisor'])
        for datos in [{}, {'motivo': ''}, {'motivo': '   '}]:
            self.assertEqual(self.accion('devolver', datos).status_code, 400)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, 'supervision_pesaje')

    def test_ciclo_devolucion_correccion_reenvio_aprobacion_con_historial(self):
        self.enviar()
        self.client.force_authenticate(self.usuarios['supervisor'])
        motivo = 'Corregir identificación. ' * 30
        respuesta = self.accion('devolver', {'motivo': motivo})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'pesaje')
        self.assertEqual(respuesta.data['pesaje']['revision'], 'devuelta')
        self.assertEqual(respuesta.data['pesaje']['motivo_devolucion'], motivo.strip())
        self.client.force_authenticate(self.usuarios['pesaje'])
        self.assertEqual(self.accion('guardar', {'lote_actual': 'L003'}).status_code, 200)
        respuesta = self.accion('enviar')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertIsNone(respuesta.data['pesaje']['supervisor_username'])
        self.client.force_authenticate(self.usuarios['supervisor'])
        respuesta = self.accion('aprobar')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'mezcla')
        self.assertEqual(respuesta.data['pesaje']['revision'], 'aprobada')
        self.assertEqual(respuesta.data['pesaje']['supervisor_username'], 'supervisor')
        self.assertIsNotNone(respuesta.data['pesaje']['fecha_revision'])
        eventos = HistorialOrdenProduccion.objects.filter(campo='estado').order_by('id')
        self.assertEqual(
            list(eventos.values_list('valor_nuevo', flat=True)),
            ['supervision_pesaje', 'pesaje', 'supervision_pesaje', 'mezcla'],
        )
        self.assertTrue(all(e.modificado_por_id and e.fecha for e in eventos))
        self.assertEqual(eventos[1].detalle, motivo.strip())
        self.assertEqual(self.accion('aprobar').status_code, 400)
        self.assertEqual(self.accion('devolver', {'motivo': 'x'}).status_code, 400)

    def test_aprobar_revalida_materiales_actuales(self):
        self.enviar()
        MaterialOrden.objects.create(
            orden=self.orden, codigo='M02', descripcion='Nuevo', porcentaje=0, cantidad=1
        )
        self.client.force_authenticate(self.usuarios['supervisor'])
        self.assertEqual(self.accion('aprobar').status_code, 400)

    def test_bandeja_de_pesaje_filtrada_y_supervisor_consulta_todo(self):
        listado = reverse('ordenes-list')
        detalle = reverse('ordenes-detail', kwargs={'pk': self.orden.pk})
        # Pesaje solo alcanza su propia cola: la OP mientras está En Pesaje.
        self.assertEqual(len(self.client.get(listado).data), 1)
        self.enviar()
        self.assertEqual(self.client.get(listado).data, [])
        self.assertEqual(self.client.get(detalle).status_code, 404)
        # El Supervisor consulta todas las OP en cualquier estado (también las
        # necesita en su pantalla principal); su bandeja de supervisión filtra
        # por estado en el frontend.
        self.client.force_authenticate(self.usuarios['supervisor'])
        self.assertEqual(len(self.client.get(listado).data), 1)
        self.assertEqual(self.client.get(detalle).status_code, 200)
        self.accion('aprobar')
        self.assertEqual(len(self.client.get(listado).data), 1)
        self.assertEqual(self.client.get(detalle).status_code, 200)
        # Ya aprobada (En Mezcla), Pesaje deja de verla.
        self.client.force_authenticate(self.usuarios['pesaje'])
        self.assertEqual(self.client.get(listado).data, [])

    def test_rollback_si_falla_trazabilidad(self):
        with (
            patch('apps.pesaje.views.registrar_historial', side_effect=RuntimeError('fallo')),
            self.assertRaises(RuntimeError),
        ):
            self.accion('enviar', self.datos())
        self.assertFalse(RegistroPesaje.objects.exists())
        self.assertFalse(PesoMaterial.objects.exists())
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, 'pesaje')

    def test_transicion_desde_picky_conserva_compatibilidad(self):
        self.orden.estado = 'picky'
        self.orden.save()
        self.client.force_authenticate(self.usuarios['picky'])
        url = reverse('ordenes-enviar-pesaje', kwargs={'pk': self.orden.pk})
        self.assertEqual(self.client.patch(url).status_code, 400)
        recepcion = reverse('ordenes-recepcion-picky', kwargs={'pk': self.orden.pk})
        self.assertEqual(
            self.client.patch(recepcion, {'nombre_operario_picky': 'Luis'}).status_code, 200
        )
        respuesta = self.client.patch(url)
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'pesaje')
        self.assertIsNone(respuesta.data['pesaje'])

    def test_acciones_requieren_autenticacion(self):
        self.client.force_authenticate(None)
        for accion in ['guardar', 'enviar', 'aprobar', 'devolver']:
            self.assertEqual(self.accion(accion).status_code, 401)

    def marcar_critico(self, grupo='blancos'):
        self.orden.grupo_critico_pesaje = grupo
        self.orden.save()

    def datos_criticos(self):
        """Formulario de condiciones críticas: sustituye al estándar, no lo suma."""
        return {
            **self.datos_base(),
            **dict.fromkeys([campo for campo, _ in VERIFICACIONES_CRITICAS], True),
            'critico_observaciones': 'Se verificó limpieza adicional y segregación.',
        }

    def test_no_critico_no_requiere_seccion_aunque_texto_mencione_grupos(self):
        self.orden.referencia = 'Blancos Aditivos Retardantes a la Llama Hojas azules'
        self.orden.clasificacion = 'peligroso'
        self.orden.save()
        respuesta = self.enviar()
        self.assertFalse(respuesta.data['es_critico_pesaje'])
        self.assertEqual(respuesta.data['grupo_critico_pesaje'], 'no_critico')
        for campo, _ in VERIFICACIONES_CRITICAS:
            self.assertIsNone(respuesta.data['pesaje'][campo])

    def test_inicio_de_pesaje_se_sella_una_sola_vez(self):
        self.assertEqual(self.accion('guardar', {'nombre_operario': 'Ana'}).status_code, 200)
        respuesta = self.accion('iniciar')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        inicio = respuesta.data['pesaje']['fecha_inicio_pesaje']
        self.assertIsNotNone(inicio)
        # Volver a entrar a la vista no mueve la hora de inicio real.
        self.assertEqual(self.accion('iniciar').data['pesaje']['fecha_inicio_pesaje'], inicio)
        self.assertEqual(
            HistorialOrdenProduccion.objects.filter(
                valor_nuevo='Inicio del pesaje de materias primas'
            ).count(),
            1,
        )

    def test_iniciar_pesaje_solo_lo_hace_el_operario_de_pesaje(self):
        self.accion('guardar', {'nombre_operario': 'Ana'})
        for rol in ['supervisor', 'picky', 'produccion', 'admin']:
            self.client.force_authenticate(self.usuarios[rol])
            with self.subTest(rol=rol):
                self.assertEqual(self.accion('iniciar').status_code, 403)
        RegistroPesaje.objects.get().refresh_from_db()
        self.assertIsNone(RegistroPesaje.objects.get().fecha_inicio_pesaje)

    def test_critico_no_exige_las_verificaciones_del_formulario_normal(self):
        self.marcar_critico()
        respuesta = self.accion('enviar', self.datos_criticos())
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'supervision_pesaje')
        for campo, _ in VERIFICACIONES:
            self.assertIsNone(respuesta.data['pesaje'][campo])

    def test_critico_no_acepta_respuestas_del_formulario_normal(self):
        self.marcar_critico()
        self.assertEqual(self.accion('guardar', {'piso_limpio': True}).status_code, 400)
        self.assertEqual(self.accion('guardar', {'observaciones': 'Nota'}).status_code, 400)
        self.assertFalse(RegistroPesaje.objects.exists())

    def test_no_cumple_exige_observacion_pero_no_impide_avanzar(self):
        datos = self.datos()
        datos['piso_limpio'] = False
        datos['observaciones'] = ''
        respuesta = self.accion('enviar', datos)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('observaciones', respuesta.data)
        self.assertFalse(RegistroPesaje.objects.exists())
        datos['observaciones'] = 'El piso tenía derrame; se limpió antes de pesar.'
        respuesta = self.accion('enviar', datos)
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'supervision_pesaje')

    def test_no_cumple_critico_exige_acciones_correctivas(self):
        self.marcar_critico()
        datos = self.datos_criticos()
        datos['critico_cero_pellets'] = False
        datos['critico_observaciones'] = ''
        respuesta = self.accion('enviar', datos)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('critico_observaciones', respuesta.data)

    def test_recepcion_critica_no_vuelca_checklist_pendiente_en_historial(self):
        self.marcar_critico()
        respuesta = self.accion('guardar', {'nombre_operario': 'Ana'})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        evento = HistorialOrdenProduccion.objects.get(campo='pesaje_registro')
        self.assertEqual(evento.detalle, 'Operario: Ana')
        respuesta = self.accion('guardar', {'critico_cero_pellets': True})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        evento_actualizado = HistorialOrdenProduccion.objects.filter(
            campo='pesaje_registro'
        ).latest('id')
        self.assertIn('Cero Pellets en el Piso”. Cumple', evento_actualizado.detalle)

    def test_cada_grupo_critico_requiere_todas_las_respuestas(self):
        for grupo in ['blancos', 'aditivos_retardantes', 'hojas_azules']:
            self.marcar_critico(grupo)
            respuesta = self.accion('enviar', self.datos_base())
            self.assertEqual(respuesta.status_code, 400)
            for campo, _ in VERIFICACIONES_CRITICAS:
                self.assertIn(campo, respuesta.data)
        self.assertFalse(RegistroPesaje.objects.exists())

    def test_critico_incompleto_guarda_borrador_pero_no_envia(self):
        self.marcar_critico()
        for campo, _ in VERIFICACIONES_CRITICAS:
            datos = self.datos_criticos()
            datos[campo] = None
            with self.subTest(campo=campo):
                respuesta = self.accion('enviar', datos)
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.data)
        self.assertEqual(self.accion('guardar', self.datos_base()).status_code, 200)
        self.assertEqual(self.accion('enviar').status_code, 400)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, 'pesaje')

    def test_critico_completo_envia_y_supervisor_ve_no_cumple(self):
        self.marcar_critico('hojas_azules')
        datos = self.datos_criticos()
        datos['critico_cero_pellets'] = False
        respuesta = self.accion('enviar', datos)
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['estado'], 'supervision_pesaje')
        self.client.force_authenticate(self.usuarios['supervisor'])
        respuesta = self.client.get(reverse('ordenes-detail', kwargs={'pk': self.orden.pk}))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.data['es_critico_pesaje'])
        self.assertEqual(respuesta.data['grupo_critico_pesaje_display'], 'Hojas azules')
        for campo, _ in VERIFICACIONES_CRITICAS:
            self.assertEqual(respuesta.data['pesaje'][campo], datos[campo])
        self.assertEqual(
            respuesta.data['pesaje']['critico_observaciones'], datos['critico_observaciones']
        )
        self.assertEqual(self.accion('guardar', datos).status_code, 403)

    def test_devolucion_reenvio_conservan_condiciones_y_trazabilidad(self):
        self.marcar_critico('aditivos_retardantes')
        datos = self.datos_criticos()
        datos['critico_cero_pellets'] = False
        self.assertEqual(self.accion('enviar', datos).status_code, 200)
        self.client.force_authenticate(self.usuarios['supervisor'])
        respuesta = self.accion('devolver', {'motivo': 'Revisar pellets'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIs(respuesta.data['pesaje']['critico_cero_pellets'], False)
        self.client.force_authenticate(self.usuarios['pesaje'])
        self.assertEqual(self.accion('guardar', {'lote_actual': 'L003'}).status_code, 200)
        respuesta = self.accion('enviar')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        for campo, _ in VERIFICACIONES_CRITICAS:
            self.assertEqual(respuesta.data['pesaje'][campo], datos[campo])
        self.assertEqual(
            respuesta.data['pesaje']['critico_observaciones'], datos['critico_observaciones']
        )
        eventos = self.orden.historial.filter(campo='estado').order_by('id')
        self.assertEqual(
            list(eventos.values_list('valor_nuevo', flat=True)),
            ['supervision_pesaje', 'pesaje', 'supervision_pesaje'],
        )
        self.assertEqual(eventos[1].detalle, 'Revisar pellets')
        self.assertTrue(
            self.orden.historial.filter(
                campo='pesaje_registro', detalle__contains='Cero Pellets en el Piso”. No cumple'
            ).exists()
        )
        self.client.force_authenticate(self.usuarios['supervisor'])
        self.assertEqual(self.accion('devolver', {'motivo': 'Corregir'}).status_code, 200)
        self.client.force_authenticate(self.usuarios['pesaje'])
        self.assertEqual(self.accion('enviar', {'critico_cero_pellets': True}).status_code, 200)
        # La respuesta anterior sigue en el historial incluso al corregir el formulario.
        self.assertTrue(
            self.orden.historial.filter(
                detalle__contains='Cero Pellets en el Piso”. No cumple'
            ).exists()
        )
        self.assertTrue(
            self.orden.historial.filter(
                detalle__contains='Cero Pellets en el Piso”. Cumple'
            ).exists()
        )

    def test_sin_clasificar_no_asume_no_critico_ni_acepta_grupo_del_operario(self):
        self.marcar_critico('')
        datos = {**self.datos(), 'grupo_critico_pesaje': 'no_critico', 'es_critico_pesaje': False}
        respuesta = self.accion('enviar', datos)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('grupo_critico_pesaje', respuesta.data)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.grupo_critico_pesaje, '')

    def test_no_critico_no_acepta_respuestas_ocultas(self):
        self.assertEqual(self.accion('guardar', {'critico_cero_pellets': False}).status_code, 400)
        self.assertFalse(RegistroPesaje.objects.exists())

    def test_aprobacion_revalida_condiciones_criticas(self):
        self.marcar_critico()
        self.assertEqual(self.accion('enviar', self.datos_criticos()).status_code, 200)
        RegistroPesaje.objects.filter(orden=self.orden).update(critico_cero_pellets=None)
        self.client.force_authenticate(self.usuarios['supervisor'])
        self.assertEqual(self.accion('aprobar').status_code, 400)

    def ingresar(self, datos):
        return self.client.patch(
            reverse('ordenes-ingresar', kwargs={'pk': self.orden.pk}), datos, format='json'
        )

    def test_produccion_clasifica_el_producto_y_queda_en_el_historial(self):
        self.marcar_critico('')
        self.client.force_authenticate(self.usuarios['produccion'])
        respuesta = self.ingresar({'grupo_critico_pesaje': 'blancos'})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['grupo_critico_pesaje'], 'blancos')
        self.assertTrue(respuesta.data['es_critico_pesaje'])
        evento = HistorialOrdenProduccion.objects.get(campo='grupo_critico_pesaje')
        self.assertEqual(evento.valor_nuevo, 'blancos')
        self.assertEqual(evento.modificado_por, self.usuarios['produccion'])
        self.assertIn('Blancos', evento.detalle)

    def test_solo_produccion_clasifica_el_producto(self):
        for rol in ['pesaje', 'picky', 'supervisor', 'admin']:
            self.client.force_authenticate(self.usuarios[rol])
            with self.subTest(rol=rol):
                self.assertEqual(self.ingresar({'grupo_critico_pesaje': 'blancos'}).status_code, 403)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.grupo_critico_pesaje, 'no_critico')

    def test_no_se_reclasifica_despues_de_enviar_a_supervision(self):
        self.enviar()
        self.client.force_authenticate(self.usuarios['produccion'])
        respuesta = self.ingresar({'grupo_critico_pesaje': 'blancos'})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('grupo_critico_pesaje', respuesta.data)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.grupo_critico_pesaje, 'no_critico')
        # Las observaciones sí se pueden seguir editando.
        self.assertEqual(self.ingresar({'observaciones': 'Nota posterior'}).status_code, 200)

    def test_admin_congela_grupo_enviado_pero_permite_clasificar_legadas(self):
        from django.contrib.admin.sites import AdminSite

        from apps.produccion.admin import OrdenProduccionAdmin

        self.enviar()
        self.orden.refresh_from_db()
        admin = OrdenProduccionAdmin(OrdenProduccion, AdminSite())
        self.assertIn('grupo_critico_pesaje', admin.get_readonly_fields(None, self.orden))
        self.orden.grupo_critico_pesaje = ''
        self.assertNotIn('grupo_critico_pesaje', admin.get_readonly_fields(None, self.orden))
