// Constantes y formateo compartidos por las vistas de Órdenes de Producción
// (Producción, Supervisor y Picking), para no repetirlos en cada pantalla.

// El azul y el amarillo quedan reservados para la hoja de la OP (ver HOJA_OP):
// los estados usan navy, y la revisión pendiente violeta para seguir resaltando.
export const ESTADO_BADGE = {
  produccion: 'navy',
  picking: 'navy',
  pesaje: 'navy',
  supervision_pesaje: 'violet',
  mezcla: 'navy',
  extrusion: 'navy',
  calidad: 'navy',
  empaque: 'navy',
  finalizada: 'gray',
  cancelada: 'red',
}

// Clase de OP según el color de la hoja física: blanca (normal), amarilla
// (urgente) y azul (requiere acompañamiento de IP).
export const CLASIFICACION_BADGE = {
  urgente: 'amber',
  acompanamiento_ip: 'blue',
  normal: 'gray',
}

export const CLASIFICACION_OPCIONES = [
  { value: 'normal', label: 'Proceso normal' },
  { value: 'urgente', label: 'Urgente' },
  { value: 'acompanamiento_ip', label: 'Acompañamiento de IP' },
]

// Card de la OP con el color de su hoja física: franja superior y contorno.
// La hoja blanca (proceso normal) no lleva marca, igual que el papel.
export const HOJA_OP = {
  urgente: {
    texto: 'Hoja amarilla · Urgente',
    franja: 'bg-yellow-300 text-yellow-950',
    contorno: 'ring-2 ring-yellow-400',
  },
  acompanamiento_ip: {
    texto: 'Hoja azul · Acompañamiento de IP',
    franja: 'bg-blue-600 text-white',
    contorno: 'ring-2 ring-blue-600',
  },
}

// Las urgentes (hoja amarilla) van primero; el resto conserva el orden en que
// llega del backend. Array.sort es estable, así que no se altera ese orden.
export function urgentesPrimero(ordenes) {
  return [...ordenes].sort(
    (a, b) => Number(b.clasificacion === 'urgente') - Number(a.clasificacion === 'urgente'),
  )
}

// Clasificación del producto para Pesaje: los tres últimos son críticos y
// hacen que Pesaje responda el formulario de condiciones especiales
// (ver OrdenProduccion.GrupoCriticoPesaje en el backend).
export const GRUPO_CRITICO_OPCIONES = [
  { value: '', label: 'Sin clasificar' },
  { value: 'no_critico', label: 'No crítico' },
  { value: 'blancos', label: 'Blancos' },
  { value: 'aditivos_retardantes', label: 'Aditivos / Retardantes a la Llama' },
  { value: 'producto_peligroso', label: 'Producto peligroso' },
]

// Una OP en estos estados ya no está en curso: no se lista como disponible.
export const ESTADOS_CERRADOS = ['finalizada', 'cancelada']

export function formatearFecha(fecha) {
  if (!fecha) return '—'
  return new Date(`${fecha}T00:00:00`).toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatearHora(hora) {
  if (!hora) return '—'
  return new Date(`1970-01-01T${hora}`).toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatearFechaHora(fechaIso) {
  if (!fechaIso) return '—'
  return new Date(fechaIso).toLocaleString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function mapearErroresCampo(e) {
  const data = e.response?.data
  if (!data || typeof data !== 'object') return {}
  const errores = {}
  for (const campo of Object.keys(data)) {
    errores[campo] = Array.isArray(data[campo]) ? data[campo][0] : String(data[campo])
  }
  return errores
}
