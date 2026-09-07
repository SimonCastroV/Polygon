<script setup>
import { onMounted, ref } from 'vue'
import api from '../../services/api'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseModal from '../../components/ui/BaseModal.vue'
import Badge from '../../components/ui/Badge.vue'

const ESTADO_BADGE = {
  planeacion: 'blue',
  picky: 'navy',
  pesaje: 'navy',
  mezcla: 'navy',
  extrusion: 'navy',
  calidad: 'navy',
  empaque: 'navy',
  finalizada: 'gray',
  cancelada: 'red',
}

const ordenes = ref([])
const cargando = ref(true)

// --- Crear OP (HU-10) ---
const modalCrearAbierto = ref(false)
const nuevaOrden = ref(ordenVacia())
const erroresCrear = ref({})
const guardandoOrden = ref(false)

// --- Editar OP (HU-11) ---
const modalEditarAbierto = ref(false)
const ordenSeleccionada = ref(null)
const ordenEditando = ref(ordenVacia())
const erroresEditar = ref({})
const guardandoEdicion = ref(false)

function ordenVacia() {
  return {
    producto: '',
    cantidad: '',
    materia_prima: '',
    urgente: false,
    observaciones: '',
  }
}

async function cargarOrdenes() {
  cargando.value = true
  const { data } = await api.get('/produccion/ordenes/')
  ordenes.value = data
  cargando.value = false
}

function abrirModalCrear() {
  nuevaOrden.value = ordenVacia()
  erroresCrear.value = {}
  modalCrearAbierto.value = true
}

async function crearOrden() {
  erroresCrear.value = {}
  guardandoOrden.value = true
  try {
    await api.post('/produccion/ordenes/', {
      ...nuevaOrden.value,
      cantidad: Number(nuevaOrden.value.cantidad),
    })
    modalCrearAbierto.value = false
    await cargarOrdenes()
  } catch (e) {
    erroresCrear.value = mapearErroresCampo(e)
  } finally {
    guardandoOrden.value = false
  }
}

function puedeEditar(orden) {
  return orden.estado === 'planeacion'
}

function abrirModalEditar(orden) {
  ordenSeleccionada.value = orden
  ordenEditando.value = {
    producto: orden.producto,
    cantidad: String(orden.cantidad),
    materia_prima: orden.materia_prima,
    urgente: orden.urgente,
    observaciones: orden.observaciones,
  }
  erroresEditar.value = {}
  modalEditarAbierto.value = true
}

async function guardarEdicion() {
  erroresEditar.value = {}
  guardandoEdicion.value = true
  try {
    await api.patch(`/produccion/ordenes/${ordenSeleccionada.value.id}/`, {
      ...ordenEditando.value,
      cantidad: Number(ordenEditando.value.cantidad),
    })
    modalEditarAbierto.value = false
    await cargarOrdenes()
  } catch (e) {
    erroresEditar.value = mapearErroresCampo(e)
  } finally {
    guardandoEdicion.value = false
  }
}

function mapearErroresCampo(e) {
  const data = e.response?.data
  if (!data || typeof data !== 'object') return {}
  const errores = {}
  for (const campo of Object.keys(data)) {
    errores[campo] = Array.isArray(data[campo]) ? data[campo][0] : String(data[campo])
  }
  return errores
}

function formatearFecha(fechaIso) {
  return new Date(fechaIso).toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

onMounted(cargarOrdenes)
</script>

<template>
  <main class="px-6 py-8">
    <div class="mb-6 flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-ink-900">Órdenes de Producción</h1>
      </div>
      <BaseButton variant="primary" @click="abrirModalCrear">+ Nueva Orden de Producción</BaseButton>
    </div>

    <div class="overflow-hidden rounded-xl bg-white shadow-sm">
      <table class="w-full text-left text-sm">
        <thead class="bg-surface-alt text-xs font-semibold uppercase text-ink-500">
          <tr>
            <th class="px-6 py-3">N° Orden</th>
            <th class="px-6 py-3">Producto</th>
            <th class="px-6 py-3">Cantidad</th>
            <th class="px-6 py-3">Materia prima</th>
            <th class="px-6 py-3">Urgente</th>
            <th class="px-6 py-3">Estado</th>
            <th class="px-6 py-3">Creada</th>
            <th class="px-6 py-3">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="cargando">
            <td colspan="8" class="px-6 py-8 text-center text-ink-500">Cargando órdenes…</td>
          </tr>
          <tr v-else-if="ordenes.length === 0">
            <td colspan="8" class="px-6 py-8 text-center text-ink-500">
              Aún no hay Órdenes de Producción registradas.
            </td>
          </tr>
          <tr v-for="orden in ordenes" :key="orden.id" class="hover:bg-surface-alt/60">
            <td class="px-6 py-3 font-semibold text-ink-900">{{ orden.numero_orden }}</td>
            <td class="px-6 py-3 text-ink-500">{{ orden.producto }}</td>
            <td class="px-6 py-3 text-ink-500">{{ orden.cantidad }}</td>
            <td class="px-6 py-3 text-ink-500">{{ orden.materia_prima }}</td>
            <td class="px-6 py-3">
              <Badge v-if="orden.urgente" color="amber">Urgente</Badge>
              <span v-else class="text-ink-500">—</span>
            </td>
            <td class="px-6 py-3">
              <Badge :color="ESTADO_BADGE[orden.estado]">{{ orden.estado_display }}</Badge>
            </td>
            <td class="px-6 py-3 text-ink-500">{{ formatearFecha(orden.fecha_creacion) }}</td>
            <td class="px-6 py-3">
              <button
                v-if="puedeEditar(orden)"
                type="button"
                class="font-semibold text-accent-blue hover:underline"
                @click="abrirModalEditar(orden)"
              >
                Editar
              </button>
              <span v-else class="text-ink-500">Sin cambios (fuera de Planeación)</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- HU-10: Crear OP -->
    <BaseModal
      :open="modalCrearAbierto"
      title="Nueva Orden de Producción"
      @close="modalCrearAbierto = false"
    >
      <form class="space-y-4" @submit.prevent="crearOrden">
        <BaseInput
          v-model="nuevaOrden.producto"
          label="Producto"
          placeholder="ej. Amarillo Sumifast 1040"
          :error="erroresCrear.producto"
          required
        />
        <BaseInput
          v-model="nuevaOrden.cantidad"
          label="Cantidad"
          type="number"
          :error="erroresCrear.cantidad"
          required
        />
        <BaseInput
          v-model="nuevaOrden.materia_prima"
          label="Materia prima"
          placeholder="ej. Pigmento amarillo + resina base"
          :error="erroresCrear.materia_prima"
          required
        />
        <label class="flex items-center gap-2">
          <input v-model="nuevaOrden.urgente" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
          <span class="text-sm font-medium text-ink-900">Marcar como urgente</span>
        </label>
        <label class="block">
          <span class="mb-1.5 block text-sm font-medium text-ink-900">Observaciones</span>
          <textarea
            v-model="nuevaOrden.observaciones"
            rows="3"
            class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
          />
        </label>

        <div class="flex justify-end gap-3 pt-2">
          <BaseButton type="button" variant="secondary" @click="modalCrearAbierto = false">
            Cancelar
          </BaseButton>
          <BaseButton type="submit" variant="primary" :loading="guardandoOrden">
            Crear Orden
          </BaseButton>
        </div>
      </form>
    </BaseModal>

    <!-- HU-11: Editar OP -->
    <BaseModal
      :open="modalEditarAbierto"
      :title="`Editar OP · ${ordenSeleccionada?.numero_orden ?? ''}`"
      @close="modalEditarAbierto = false"
    >
      <form class="space-y-4" @submit.prevent="guardarEdicion">
        <BaseInput
          v-model="ordenEditando.producto"
          label="Producto"
          :error="erroresEditar.producto"
          required
        />
        <BaseInput
          v-model="ordenEditando.cantidad"
          label="Cantidad"
          type="number"
          :error="erroresEditar.cantidad"
          required
        />
        <BaseInput
          v-model="ordenEditando.materia_prima"
          label="Materia prima"
          :error="erroresEditar.materia_prima"
          required
        />
        <label class="flex items-center gap-2">
          <input v-model="ordenEditando.urgente" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
          <span class="text-sm font-medium text-ink-900">Marcar como urgente</span>
        </label>
        <label class="block">
          <span class="mb-1.5 block text-sm font-medium text-ink-900">Observaciones</span>
          <textarea
            v-model="ordenEditando.observaciones"
            rows="3"
            class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
          />
        </label>
        <p v-if="erroresEditar.non_field_errors" class="text-sm text-danger">
          {{ erroresEditar.non_field_errors }}
        </p>

        <div class="flex justify-end gap-3 pt-2">
          <BaseButton type="button" variant="secondary" @click="modalEditarAbierto = false">
            Cancelar
          </BaseButton>
          <BaseButton type="submit" variant="primary" :loading="guardandoEdicion">
            Guardar cambios
          </BaseButton>
        </div>
      </form>
    </BaseModal>
  </main>
</template>
