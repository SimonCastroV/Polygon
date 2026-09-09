// Constantes y formateo compartidos por las vistas de Órdenes de Producción
// (Producción, Supervisor y Picky), para no repetirlos en cada pantalla.

export const ESTADO_BADGE = {
  produccion: 'blue',
  picky: 'navy',
  pesaje: 'navy',
  supervision_pesaje: 'amber',
  mezcla: 'navy',
  extrusion: 'navy',
  calidad: 'navy',
  empaque: 'navy',
  finalizada: 'gray',
  cancelada: 'red',
}

export const CLASIFICACION_BADGE = {
  urgente: 'amber',
  peligroso: 'red',
  normal: 'gray',
}

export const CLASIFICACION_OPCIONES = [
  { value: 'normal', label: 'Proceso normal' },
  { value: 'urgente', label: 'Urgente' },
  { value: 'peligroso', label: 'Producto peligroso' },
]

// Clasificación del producto para Pesaje: los tres últimos son críticos y
// hacen que Pesaje responda el formulario de condiciones especiales
// (ver OrdenProduccion.GrupoCriticoPesaje en el backend).
export const GRUPO_CRITICO_OPCIONES = [
  { value: '', label: 'Sin clasificar' },
  { value: 'no_critico', label: 'No crítico' },
  { value: 'blancos', label: 'Blancos' },
  { value: 'aditivos_retardantes', label: 'Aditivos / Retardantes a la Llama' },
  { value: 'hojas_azules', label: 'Hojas azules' },
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
