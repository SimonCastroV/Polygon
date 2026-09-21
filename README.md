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



## 5. Roles y permisos

| Rol | Qué puede hacer |
|---|---|
| **Administrador** | Gestionar usuarios y roles; cargar OP por el admin de Django |
| **Producción** | Clasificar la OP (tipo y grupo para Pesaje), observaciones, liberar a Picking |
| **Ing. Producción** | Consultar, sin editar, las OP con acompañamiento de IP (hoja azul) en todo su proceso |
| **Picking** | Confirmar recepción, consultar materiales, enviar a Pesaje |
| **Pesaje** | Confirmar recibido, verificación de limpieza, ver cantidades a pesar, enviar a supervisor |
| **Supervisor** | Consultar todas las OP; revisar el pesaje: enviar a Mezcla o devolver |
| Mezcla, Extrusión, Calidad, Empaque, Planta | Roles creados; sus módulos están pendientes |

Los permisos se aplican **en el servidor** (`EsProduccion`, `EsPicking`, `EsPesaje`,
`EsSupervisorPesaje`, `PuedeVerOP`), no solo escondiendo botones. Cada estación además solo ve las
OP de su cola: Pesaje ve únicamente las que están En Pesaje, Picking las que Producción ya liberó,
e Ing. Producción solo las de acompañamiento de IP, en cualquier etapa.

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
- En el detalle de la OP: elegir el tipo de orden, escribir observaciones y **clasificar el producto
  para Pesaje**.
- **Mandar orden a Picking** guarda esa hoja y libera la OP en una sola acción (no hay botón
  Guardar aparte, para que no se pierda lo diligenciado). Solo desde el detalle, para obligar a
  revisar la orden antes de enviarla. Todo queda auditado; después la hoja es de solo lectura.

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
producto—. Son críticos: **Blancos**, **Aditivos / Retardantes a la Llama** y **Producto peligroso**.
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
