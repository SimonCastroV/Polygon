# Pesaje operativo

El flujo implementado es `picky → pesaje → supervision_pesaje → mezcla`, con devolución `supervision_pesaje → pesaje`. Solo `supervisor_pesaje` puede aprobar o devolver; el supervisor genérico conserva sus permisos de consulta.

## Pantallas y componentes

- `/admin/pesaje/ordenes` y `/admin/pesaje/ordenes/:id`: bandeja y registro del operario.
- `/admin/supervision-pesaje/ordenes` y `/admin/supervision-pesaje/ordenes/:id`: bandeja y revisión del supervisor.
- Ambas estaciones reutilizan `OrdenesPesaje.vue` y `OrdenPesajeDetalle.vue`; el rol y el estado controlan edición y revisión.
- Se reutilizan `OrdenResumen`, `OrdenTrazabilidad`, `BaseInput`, `BaseButton` y `Badge`. La trazabilidad del detalle de Producción/Picky también muestra los eventos de Pesaje.
- El administrador puede asignar el nuevo rol desde Gestión de Usuarios. No se migran cuentas genéricas automáticamente.

## API

Los GET existentes de `/api/produccion/ordenes/` y `/api/produccion/ordenes/{id}/` incluyen `pesaje` (null si no existe) e `historial`. El backend filtra Pesaje por estado `pesaje` y Supervisor de Pesaje por `supervision_pesaje`.

Todas las acciones nuevas son PATCH bajo `/api/produccion/ordenes/{id}/pesaje/`:

| Sufijo | Acción | Rol |
| --- | --- | --- |
| vacío | Guardar borrador | pesaje |
| `enviar-supervisor/` | Guardar y enviar, validando integridad | pesaje |
| `aprobar/` | Aprobar y enviar a Mezcla | supervisor_pesaje |
| `devolver/` | Devolver con `{ "motivo": "..." }` obligatorio | supervisor_pesaje |

Guardar/enviar aceptan `lote_anterior`, `referencia_anterior`, `lote_actual`, `nombre_operario`, `observaciones`, los diez booleanos definidos en `apps/pesaje/models.py::VERIFICACIONES` y `pesos: [{ "material": 123, "peso_real": "10.1250" }]`.

PATCH puede omitir campos ya guardados. Si incluye `pesos`, la lista reemplaza los pesos del borrador. Cada elemento exige material y peso. La referencia actual, usuarios, fechas, revisión y cambios de estado los define el servidor. La respuesta es la OP completa actualizada.

## Persistencia y reglas

- `RegistroPesaje`: OneToOne con OP; formulario, cuenta del último registro, recepción/primer guardado, envío y última revisión.
- `PesoMaterial`: FK a registro y material; Decimal(14,4), positivo y único por registro/material. No modifica `MaterialOrden.cantidad` ni el porcentaje original.
- Se extiende `HistorialOrdenProduccion` con `detalle` de texto, para conservar motivos completos y los ciclos anteriores aunque el formulario vuelva a editarse.
- Cada operación de escritura bloquea la OP con `select_for_update` y guarda formulario, transición e historial en una sola transacción.
- Un borrador admite campos y respuestas pendientes (null). Para enviar se exigen lote/referencia anterior, lote actual, nombre del operario, diez respuestas y un peso positivo por cada material de la OP. No se permiten materiales ajenos, duplicados, pesos no finitos o más de cuatro decimales.
- Una OP sin materiales no puede enviarse. Aprobar vuelve a comprobar la integridad del registro.
- Después de enviar, Pesaje pierde edición y la OP sale de su bandeja; una devolución conserva los datos y habilita su corrección. Una OP aprobada sale de la bandeja del supervisor.
- La entrada a Pesaje se registra desde Picky; la recepción propia corresponde al primer guardado del formulario. Abrir una OP no genera una recepción.

## Decisiones funcionales explícitas

- La OP no dispone de número de lote: lote actual y datos del lote anterior son manuales. La referencia actual es una copia de la OP al guardar. Si no hubo lote anterior se puede indicar “No aplica” en lote y referencia anterior.
- Las cuentas representan estaciones; se conserva la cuenta autenticada y se solicita el nombre del operario, siguiendo Picky.
- `No cumple` es una respuesta válida, distinta de pendiente. Se resalta al revisar; no se impone un bloqueo automático de aprobación no solicitado. La decisión corresponde al supervisor.
- Observaciones de Pesaje son opcionales; motivo de devolución es obligatorio.
- Peso real y cantidad esperada se comparan en la misma unidad de fórmula. No hay conversión ni tolerancia automática porque no están definidas en los requisitos ni existe unidad por material.
- Mezcla recibe el estado `mezcla`; no se implementa aquí su módulo operativo.

## Migraciones y verificación

Migraciones: `produccion.0006`, `pesaje.0001`, `usuarios.0005`.

Desde la raíz: `Backend/venv/bin/python Backend/manage.py migrate` y `Backend/venv/bin/python Backend/manage.py test apps.pesaje`.

Las pruebas cubren integridad, permisos, bandejas, fórmula preservada, revisión/devolución/reenvío, motivos, historial, rollback y compatibilidad con el envío desde Picky.

## Productos críticos: liberación de condiciones operacionales

La fuente disponible identifica el producto mediante `OrdenProduccion.codigo_producto`, pero no existe un catálogo local ni integración con la familia del producto en Sumicolor. `clasificacion` (normal/urgente/peligroso) tiene otro significado; referencia y descripción no son una clasificación fiable.

Se incorpora `OrdenProduccion.grupo_critico_pesaje`, dato estructurado cargado junto al encabezado en Django admin, usando el código y la ficha técnica como referencia humana:

- Vacío: Sin clasificar (valor inicial de las OP existentes, no equivale a no crítico).
- `no_critico`: No crítico.
- `blancos`: Blancos.
- `aditivos_retardantes`: Aditivos / Retardantes a la Llama.
- `hojas_azules`: Hojas azules.

No se asignan grupos por búsqueda de palabras ni se inventa un mapeo de códigos. La clasificación es por OP: un futuro importador debe rellenarla desde el catálogo estructurado por código. Hasta entonces, debe clasificarse explícitamente cada OP desde Django admin. La API de Pesaje no acepta modificar el grupo. Se registra el cambio de grupo en `HistorialOrdenProduccion`; una clasificación ya enviada queda de solo lectura en admin para no ocultar información revisada. Las OP legadas enviadas antes de esta migración y aún sin clasificar pueden recibir su clasificación inicial.

El serializer de la OP expone `grupo_critico_pesaje`, `grupo_critico_pesaje_display` y `es_critico_pesaje` calculado en backend. Las OP sin clasificar permiten borradores, pero no enviar ni aprobar hasta resolver la clasificación. Las no críticas no requieren la sección. Las tres categorías críticas muestran **LIBERACIÓN DE CONDICIONES OPERACIONALES PARA PRODUCTOS CRÍTICOS PESAJE**.

Las diez respuestas se guardan en los campos booleanos nullable `critico_*` de `RegistroPesaje`, definidos en `VERIFICACIONES_CRITICAS`. Null permite borrador y significa pendiente; tanto Cumple como No cumple son respuestas explícitas válidas. Todas son obligatorias para enviar/aprobar cuando aplica. `critico_observaciones` guarda Acciones correctivas / Observaciones y es opcional. No se aceptan respuestas críticas activas en una OP no crítica.

El formulario usa el mismo componente `VerificacionesPesaje` para ambas listas de verificación. El supervisor solo ve los resultados y los No cumple se resaltan en rojo. Devolver no elimina campos; PATCH y reenvíos preservan campos omitidos. Cada guardado crítico añade una instantánea legible de las respuestas y observaciones al detalle del historial existente, sin borrar revisiones previas.

**Evidencia/fotos:** no hay FileField, ImageField, configuración MEDIA ni API de adjuntos en el proyecto. No se implementa subida, enlaces ni almacenamiento alternativo. El punto de integración está señalado en el modelo y en la sección del formulario: cuando haya un servicio compartido de archivos, sus adjuntos deben relacionarse con el ID de `RegistroPesaje` y respetar los permisos de la OP. Hoy solo se admite evidencia textual mediante observaciones.

Migraciones adicionales: `produccion.0007` y `pesaje.0002`. No reclasifican automáticamente las órdenes existentes.
