# Polygon — Sumicolor S.A.

Sistema que digitaliza el recorrido de una **Orden de Producción (OP)** por las estaciones de la
planta. Hoy la OP viaja en papel (la *Hoja de Procesos*) y se firma a mano; Polygon la convierte en
un registro digital con trazabilidad de quién hizo qué y cuándo.

**Flujo completo del proceso:**

```
Planeación → Picking → Pesaje → Mezcla → Extrusión → Calidad → Empaque → Espacio Cliente
```

**Implementado hasta hoy:** Producción → Picking → Pesaje → Supervisor → (entrega a Mezcla).

---

## 1. Stack

| Capa | Tecnología |
|---|---|
| Backend | Django 6.1 + Django REST Framework 3.18 |
| Base de datos | PostgreSQL (`psycopg2`) |
| Frontend | Vue 3 + Vite 8 + Vue Router + Pinia |
| Estilos | Tailwind CSS 4 |
| Autenticación | Token de DRF (`Authorization: Token <clave>`) |
| Calidad | Ruff (backend) · ESLint + Prettier (frontend) · 44 pruebas automatizadas |

## 2. Estructura del proyecto

```
Polygon/
├── Backend/
│   ├── config/            # settings, urls raíz
│   └── apps/
│       ├── usuarios/      # login, roles, auditoría de usuarios
│       ├── produccion/    # Orden de Producción, materiales, historial
│       ├── picking/         # (usa los endpoints de produccion)
│       ├── pesaje/        # formularios de verificación y hoja de pesaje
│       └── mezcla/ extrusion/ calidad/ empaque/ reportes/   ← pendientes
└── Frontend/src/
    ├── views/             # pantallas por módulo (usuarios, produccion, picking, pesaje)
    ├── components/        # OrdenResumen, OrdenTrazabilidad, VerificacionesPesaje, ui/
    ├── router/            # rutas protegidas por rol
    ├── store/             # sesión (Pinia)
    └── services/api.js    # cliente HTTP (axios)
```

---

## 3. Datos que vienen de Sumicolor

La OP **no se crea en Polygon**: llega hecha desde la base de datos de Sumicolor. Polygon solo la
lee y le añade lo que ocurre en planta.

> ⚠️ La integración automática todavía no existe. Mientras tanto, el encabezado y los materiales se
> cargan por el **panel de administración de Django**, y la API los expone **solo en lectura**.

### 3.1 Encabezado de la OP

Origen: vista `CantidadesLotes` y tablas `LotesProduccion`, `FrmProductos`, `Productos`.

| Campo en Polygon | Tipo | Equivalente en Sumicolor |
|---|---|---|
| `codigo_producto` | texto (20) | `CodigoProducto` |
| `referencia` | texto (120) | `Descripcion` |
| `cantidad` | float | `Cantidad` |
| `unidad` | texto (10) | — |
| `cliente` | texto (100) | `Cliente` |
| `codigo_cliente` | texto (15) | código de cliente |
| `pedido` | texto (9) | número de pedido |
| `fecha_pedido` / `hora_pedido` | fecha / hora | fecha y hora del pedido |
| `vencimiento_pedido` | fecha | vencimiento |
| `fecha_hora_lote` | fecha y hora | lote de producción (puede no existir aún) |

### 3.2 Materiales de la fórmula

Origen: `MateriasPrimas`, `FrmProductos`, `Productos`. Es la tabla de componentes de la Hoja de
Procesos (Resina / Aditivos / Componentes).

| Campo | Tipo | Significado |
|---|---|---|
| `codigo` | texto (20) | código de la materia prima |
| `descripcion` | texto (120) | nombre del componente |
| `porcentaje` | float | % en la fórmula |
| `cantidad` | float | kg teóricos según fórmula |
| `localizacion` | texto (120) | ubicación en bodega |

### 3.3 Diccionario de datos de la Hoja de Proceso de Pesaje

Del archivo `HOJA DE PROCESO PESAJE Y MEZCLA.xlsx` entregado por Sumicolor:

| Campo de la hoja | Tabla/vista origen | Columna | Tipo |
|---|---|---|---|
| LOTE | `Lotes_de_Produccion` | `Lote` | int, not null |
| REFERENCIA | `Lotes_de_Produccion` | `CodigoProducto` | nvarchar(20), not null |
| FORMULA | `Lotes_de_Produccion` | `Descripcion` | nvarchar(80), not null |
| CANTIDAD | `Lotes_de_Produccion` | `Cantidad` | float, not null |
| CLIENTE | `Lotes_de_Produccion` | `Cliente` | nvarchar(100), not null |

**Todo lo demás de esa hoja lo aporta Polygon**: verificaciones de limpieza, condiciones críticas,
horas de inicio/fin, operario y firmas digitales. Las cantidades a pesar son las de la fórmula:
el operario las ve, no las digita.

---

## 4. Tablas que guarda Polygon

Siete tablas propias. Las cinco primeras son el núcleo del flujo.

### `produccion_ordenproduccion` — la OP

| Campo | Origen | Descripción |
|---|---|---|
| `numero_orden` | Polygon | consecutivo `OP-000001`, único |
| *(encabezado)* | Sumicolor | ver sección 3.1 |
| `clasificacion` | **Producción** | `urgente` · `peligroso` · `normal` |
| `observaciones` | **Producción** | indicaciones para las estaciones |
| `grupo_critico_pesaje` | **Producción** | clasificación del producto para Pesaje |
| `estado` | Polygon | etapa actual de la OP |
| `fecha_envio_picking` | servidor | cuándo Producción liberó la OP |
| `nombre_operario_picking` | Picking | quién recibe (dato escrito por el operario) |
| `recibida_por_picking` | servidor | cuenta que confirmó |
| `fecha_recepcion_picking` | servidor | cuándo se confirmó |
| `fecha_envio_pesaje` | servidor | fin en Picking = llegada a Pesaje |
| `creado_por`, `fecha_creacion`, `fecha_modificacion` | servidor | auditoría básica |

### `produccion_materialorden` — fórmula de la OP
Una fila por materia prima (ver 3.2). Solo lectura desde la API.

### `produccion_historialordenproduccion` — trazabilidad
El registro que permite reconstruir la vida completa de una OP.

| Campo | Descripción |
|---|---|
| `orden` | OP afectada |
| `modificado_por` | usuario que hizo el cambio |
| `campo` | qué cambió (`estado`, `grupo_critico_pesaje`, `pesaje_registro`…) |
| `valor_anterior` / `valor_nuevo` | antes y después |
| `detalle` | texto ampliado (respuestas del checklist, motivo de devolución…) |
| `fecha` | sello del servidor |

### `pesaje_registropesaje` — la hoja de Pesaje digitalizada
Un registro por OP (`OneToOne`). Contiene:

- **Identificación del lote:** `lote_anterior`, `referencia_anterior`, `lote_actual`,
  `referencia_actual`, `nombre_operario`
- **Verificación de limpieza + despeje de línea (10 campos):** `productos_retirados`,
  `sin_restos_lote_anterior`, `balanzas_limpias`, `superficies_limpias`, `utensilios_limpios`,
  `piso_limpio`, `area_ordenada`, `bolsa_identificada`, `epp_adecuado`, `residuos_dispuestos`
- **Liberación de condiciones para productos críticos (10 campos):**
  `critico_area_equipos_limpios`, `critico_limpieza_anterior_liberada`, `critico_uniforme_epp`,
  `critico_mp_identificadas`, `critico_equipos_aptos`, `critico_sin_actividades_simultaneas`,
  `critico_ambiente_adecuado`, `critico_cero_pellets`, `critico_sin_condiciones_inseguras`,
  `critico_liberacion_autorizada`
- **Observaciones:** `observaciones` y `critico_observaciones`
- **Tiempos y firmas:** `registrado_por`, `fecha_recepcion`, `fecha_inicio_pesaje` (H.INC),
  `fecha_envio_supervision` (H.FIN), `fecha_modificacion`
- **Revisión del supervisor:** `supervisor`, `fecha_revision`, `revision`
  (`pendiente`/`aprobada`/`devuelta`), `motivo_devolucion`

Cada verificación admite tres valores: **Cumple**, **No cumple** y *sin responder* (`null`), para
no confundir "pendiente" con "incumple".

### `usuarios_customuser` y `usuarios_registroauditoriausuario`
Usuarios con **un rol único** por cuenta, y una fila de auditoría por cada cambio de `rol` o
`is_active` (quién lo cambió y cuándo).

---

## 5. Roles y permisos

| Rol | Qué puede hacer |
|---|---|
| **Administrador** | Gestionar usuarios y roles; cargar OP por el admin de Django |
| **Producción** | Clasificar la OP (tipo y grupo para Pesaje), observaciones, liberar a Picking |
| **Picking** | Confirmar recepción, consultar materiales, enviar a Pesaje |
| **Pesaje** | Confirmar recibido, verificación de limpieza, ver cantidades a pesar, enviar a supervisor |
| **Supervisor** | Consultar todas las OP; revisar el pesaje: enviar a Mezcla o devolver |
| Mezcla, Extrusión, Calidad, Empaque, Planta | Roles creados; sus módulos están pendientes |

Los permisos se aplican **en el servidor** (`EsProduccion`, `EsPicking`, `EsPesaje`,
`EsSupervisorPesaje`, `PuedeVerOP`), no solo escondiendo botones. Cada estación además solo ve las
OP de su cola: Pesaje ve únicamente las que están En Pesaje, Picking las que Producción ya liberó.

---

## 6. Estados de la OP

| Estado | Etiqueta | ¿Implementado? |
|---|---|---|
| `produccion` | En Producción | ✅ |
| `picking` | En Picking | ✅ |
| `pesaje` | En Pesaje | ✅ |
| `supervision_pesaje` | En supervisión de Pesaje | ✅ |
| `mezcla` | En Mezcla | ✅ (llega aquí) |
| `extrusion`, `calidad`, `empaque`, `finalizada`, `cancelada` | — | definidos, sin módulo |

---

## 7. Funcionalidades por módulo

### Producción
- Bandeja con filtros (Pendientes por enviar · En proceso · Todas) y contadores.
- "Ingresar a OP": clasificar el tipo de orden, escribir observaciones y **clasificar el producto
  para Pesaje**. Todo queda auditado.
- Liberar la OP a Picking (solo desde el detalle, para obligar a revisar la orden antes de enviarla).

### Picking
- Bandeja con filtros (Pendientes · En proceso · Ya liberado).
- Confirmar recepción registrando el nombre del operario; la fecha y hora las pone el servidor.
- Consulta de los materiales a preparar; el botón "Enviar a Pesaje" está al final de la pantalla,
  después de la lista, para que no se envíe sin revisarla.

### Pesaje
1. **Confirmar recibido** — registra operario, fecha y hora del servidor.
2. **Verificación de limpieza + despeje de línea**, o bien el **formulario de condiciones críticas**
   si el producto lo es. Nunca se muestran los dos: cada producto responde el suyo.
3. Un **"No cumple"** no bloquea el avance, pero obliga a explicarlo en observaciones.
4. **"Empezar pesaje"** abre la hoja de proceso: datos de la OP en solo lectura y, en grande, la
   cantidad a pesar de cada materia prima según la fórmula (el operario no digita pesos). El
   servidor sella la hora de inicio.
5. **"Enviar a supervisor"** — valida, guarda y pasa la OP a revisión. **No salta a Mezcla.**

### Productos críticos
Se determinan por el campo `grupo_critico_pesaje` de la OP —**nunca** adivinando por el nombre del
producto—. Son críticos: **Blancos**, **Aditivos / Retardantes a la Llama** y **Hojas azules**.
Muestran una advertencia visible y su propio formulario de liberación de condiciones. Una vez el
formulario se envía a supervisión, la clasificación se congela.

### Supervisor
- Bandeja con filtros (Pendientes de revisión · En Pesaje · Ya liberadas).
- Revisa el pesaje registrado: verificaciones, observaciones, horas de inicio/fin y las
  cantidades de la fórmula.
- **Enviar a Mezcla** (libera la OP) o **Devolver a Pesaje** con motivo obligatorio. La OP vuelve a
  la bandeja del operario, que corrige y reenvía.

### Usuarios
Alta, edición de rol y estado, cambio de contraseña, y auditoría de cada cambio. Un administrador
**no puede cambiar su propio rol ni desactivarse**, para no dejar el sistema sin quien lo administre.

---

## 8. API

Base: `/api/`. Todo requiere token salvo el login.

| Método | Ruta | Quién |
|---|---|---|
| POST | `login/` · `logout/` | cualquiera |
| GET/POST | `usuarios/` | Administrador |
| GET/PATCH | `usuarios/<id>/` | Administrador |
| POST | `usuarios/<id>/cambiar-password/` | Administrador |
| GET | `produccion/ordenes/` · `produccion/ordenes/<id>/` | según rol y cola |
| PATCH | `produccion/ordenes/<id>/ingresar/` | Producción |
| PATCH | `produccion/ordenes/<id>/enviar-picking/` | Producción |
| PATCH | `produccion/ordenes/<id>/recepcion-picking/` | Picking |
| PATCH | `produccion/ordenes/<id>/enviar-pesaje/` | Picking |
| PATCH | `produccion/ordenes/<id>/pesaje/` | Pesaje |
| PATCH | `produccion/ordenes/<id>/pesaje/iniciar/` | Pesaje |
| PATCH | `produccion/ordenes/<id>/pesaje/enviar-supervisor/` | Pesaje |
| PATCH | `produccion/ordenes/<id>/pesaje/aprobar/` | Supervisor |
| PATCH | `produccion/ordenes/<id>/pesaje/devolver/` | Supervisor |
| GET | `pesaje/verificaciones/` | autenticado |
| GET | `health/` | cualquiera |

---

## 9. Trazabilidad

Toda acción relevante queda registrada en `produccion_historialordenproduccion` con **usuario,
fecha y hora del servidor** — el operario nunca escribe fechas a mano. Se registra:

- cada cambio de etapa (con el motivo, si fue una devolución);
- la clasificación del producto para Pesaje;
- la recepción en Pesaje y cada actualización del formulario, con las respuestas Cumple/No cumple;
- el inicio del pesaje de materias primas.

La información se muestra filtrada según quién mire: el operario ve el resumen de hitos, y el
detalle completo evento por evento queda para el Supervisor, que es quien revisa.

---

## 10. Cómo ejecutar el proyecto

```bash
# Backend
cd Backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# crear .env con: SECRET_KEY, DEBUG, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT,
#                 CORS_ALLOWED_ORIGINS, ALLOWED_HOSTS
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend
cd Frontend
npm install
npm run dev
```

**Pruebas:** `python manage.py test` — 44 pruebas que cubren el flujo completo de Pesaje,
los permisos por rol, las validaciones de los formularios y la gestión de usuarios.

---

## 11. Pendiente

- Integración automática con la base de datos de Sumicolor (hoy la OP se carga por el admin).
- Módulos de Mezcla, Extrusión, Calidad, Empaque y Espacio Cliente.
- Reportes e indicadores (los tiempos por etapa ya se están registrando).
- Adjuntar evidencias fotográficas al registro de Pesaje.
