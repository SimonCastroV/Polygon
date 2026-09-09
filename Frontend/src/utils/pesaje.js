import api from '../services/api'

// Los textos y campos de los dos formularios de verificación viven en el
// backend (apps/pesaje/models.py), que es donde están las columnas reales.
// Aquí solo se traen y se cachean para no repetir la petición en cada vista:
// mantener una copia local se desincronizaba en silencio al cambiar el modelo.
let cache = null

export async function cargarVerificaciones() {
  if (!cache) {
    const { data } = await api.get('/pesaje/verificaciones/')
    cache = { normales: data.normales, criticas: data.criticas }
  }
  return cache
}
