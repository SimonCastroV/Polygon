<script setup>
import { onMounted, ref } from 'vue'
import api from '../../services/api'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseModal from '../../components/ui/BaseModal.vue'
import Badge from '../../components/ui/Badge.vue'

const ROL_BADGE = {
  admin: 'navy',
  supervisor: 'blue',
  supervisor_pesaje: 'blue',
  produccion: 'amber',
  picky: 'gray',
  pesaje: 'gray',
  mezcla: 'gray',
  extrusion: 'gray',
  calidad: 'gray',
  empaque: 'gray',
  planta: 'gray',
}

const usuarios = ref([])
const cargando = ref(true)

const modalCrearAbierto = ref(false)
const nuevoUsuario = ref({
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  rol: 'planta',
})
const erroresCrear = ref({})
const guardandoUsuario = ref(false)

const modalPasswordAbierto = ref(false)
const usuarioSeleccionado = ref(null)
const nuevaPassword = ref('')
const errorPassword = ref('')
const guardandoPassword = ref(false)

// --- Editar usuario: estado y rol (HU-05 / HU-06) ---
// En Polygon los usuarios son máquinas/estaciones, no personas: la edición
// solo permite cambiar el rol y activar/desactivar la cuenta (nombre y
// apellido no son editables aquí, ver UsuarioUpdateSerializer en backend).
const modalEditarAbierto = ref(false)
const usuarioEditando = ref(null)
const formEditar = ref({ rol: 'planta', is_active: true })
const erroresEditar = ref({})
const guardandoEdicion = ref(false)

async function cargarUsuarios() {
  cargando.value = true
  const { data } = await api.get('/usuarios/')
  usuarios.value = data
  cargando.value = false
}

function abrirModalCrear() {
  nuevoUsuario.value = { username: '', password: '', first_name: '', last_name: '', rol: 'planta' }
  erroresCrear.value = {}
  modalCrearAbierto.value = true
}

async function crearUsuario() {
  erroresCrear.value = {}
  guardandoUsuario.value = true
  try {
    await api.post('/usuarios/', nuevoUsuario.value)
    modalCrearAbierto.value = false
    await cargarUsuarios()
  } catch (e) {
    erroresCrear.value = mapearErroresCampo(e)
  } finally {
    guardandoUsuario.value = false
  }
}

function abrirModalPassword(usuario) {
  usuarioSeleccionado.value = usuario
  nuevaPassword.value = ''
  errorPassword.value = ''
  modalPasswordAbierto.value = true
}

async function cambiarPassword() {
  errorPassword.value = ''
  guardandoPassword.value = true
  try {
    await api.post(`/usuarios/${usuarioSeleccionado.value.id}/cambiar-password/`, {
      new_password: nuevaPassword.value,
    })
    modalPasswordAbierto.value = false
  } catch (e) {
    const detalle = e.response?.data?.new_password
    errorPassword.value = Array.isArray(detalle) ? detalle[0] : 'No se pudo cambiar la contraseña.'
  } finally {
    guardandoPassword.value = false
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

function abrirModalEditar(usuario) {
  usuarioEditando.value = usuario
  formEditar.value = {
    rol: usuario.rol,
    is_active: usuario.is_active,
  }
  erroresEditar.value = {}
  modalEditarAbierto.value = true
}

async function guardarEdicion() {
  erroresEditar.value = {}
  guardandoEdicion.value = true
  try {
    await api.patch(`/usuarios/${usuarioEditando.value.id}/`, formEditar.value)
    modalEditarAbierto.value = false
    await cargarUsuarios()
  } catch (e) {
    erroresEditar.value = mapearErroresCampo(e)
  } finally {
    guardandoEdicion.value = false
  }
}

function formatearFecha(fechaIso) {
  return new Date(fechaIso).toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

onMounted(cargarUsuarios)
</script>

<template>
  <main class="px-4 py-6 sm:px-6 sm:py-8">
    <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 class="text-xl font-bold text-ink-900 sm:text-2xl">Gestión de Usuarios</h1>
      </div>
      <BaseButton variant="primary" class="w-full sm:w-auto" @click="abrirModalCrear">
        + Nuevo usuario
      </BaseButton>
    </div>

    <div class="overflow-x-auto rounded-xl bg-white shadow-sm">
      <table class="w-full min-w-[640px] text-left text-sm">
        <thead class="bg-surface-alt text-xs font-semibold uppercase text-ink-500">
          <tr>
            <th class="px-6 py-3">Usuario</th>
            <th class="px-6 py-3">Nombre</th>
            <th class="px-6 py-3">Rol</th>
            <th class="px-6 py-3">Estado</th>
            <th class="px-6 py-3">Creado</th>
            <th class="px-6 py-3">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="cargando">
            <td colspan="6" class="px-6 py-8 text-center text-ink-500">Cargando usuarios…</td>
          </tr>
          <tr v-else-if="usuarios.length === 0">
            <td colspan="6" class="px-6 py-8 text-center text-ink-500">
              Aún no hay usuarios creados.
            </td>
          </tr>
          <tr v-for="usuario in usuarios" :key="usuario.id" class="hover:bg-surface-alt/60">
            <td class="px-6 py-3 font-semibold text-ink-900">{{ usuario.username }}</td>
            <td class="px-6 py-3 text-ink-500">
              {{ [usuario.first_name, usuario.last_name].filter(Boolean).join(' ') || '—' }}
            </td>
            <td class="px-6 py-3">
              <Badge :color="ROL_BADGE[usuario.rol]">{{ usuario.rol_display }}</Badge>
            </td>
            <td class="px-6 py-3">
              <Badge :color="usuario.is_active ? 'blue' : 'gray'">
                {{ usuario.is_active ? 'Activo' : 'Inactivo' }}
              </Badge>
            </td>
            <td class="px-6 py-3 text-ink-500">{{ formatearFecha(usuario.date_joined) }}</td>
            <td class="px-6 py-3">
              <div class="flex flex-wrap gap-x-3 gap-y-1">
                <button
                  type="button"
                  class="font-semibold text-accent-blue hover:underline"
                  @click="abrirModalEditar(usuario)"
                >
                  Editar
                </button>
                <button
                  type="button"
                  class="font-semibold text-accent-blue hover:underline"
                  @click="abrirModalPassword(usuario)"
                >
                  Cambiar contraseña
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal :open="modalCrearAbierto" title="Nuevo usuario" @close="modalCrearAbierto = false">
      <form class="space-y-4" @submit.prevent="crearUsuario">
        <BaseInput
          v-model="nuevoUsuario.username"
          label="Usuario"
          placeholder="ej. pesaje1"
          :error="erroresCrear.username"
          required
        />
        <BaseInput
          v-model="nuevoUsuario.password"
          label="Contraseña"
          type="password"
          :error="erroresCrear.password"
          required
        />
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <BaseInput v-model="nuevoUsuario.first_name" label="Nombre (opcional)" />
          <BaseInput v-model="nuevoUsuario.last_name" label="Apellido (opcional)" />
        </div>
        <label class="block">
          <span class="mb-1.5 block text-sm font-medium text-ink-900">Rol</span>
          <select
            v-model="nuevoUsuario.rol"
            class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
          >
            <option value="admin">Administrador</option>
            <option value="supervisor">Supervisor</option>
            <option value="supervisor_pesaje">Supervisor de Pesaje</option>
            <option value="produccion">Producción</option>
            <option value="picky">Picky</option>
            <option value="pesaje">Pesaje</option>
            <option value="mezcla">Mezcla</option>
            <option value="extrusion">Extrusión</option>
            <option value="calidad">Calidad</option>
            <option value="empaque">Empaque</option>
            <option value="planta">Personal de Planta</option>
          </select>
        </label>

        <div class="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
          <BaseButton
            type="button"
            variant="secondary"
            class="w-full sm:w-auto"
            @click="modalCrearAbierto = false"
          >
            Cancelar
          </BaseButton>
          <BaseButton
            type="submit"
            variant="primary"
            class="w-full sm:w-auto"
            :loading="guardandoUsuario"
          >
            Crear usuario
          </BaseButton>
        </div>
      </form>
    </BaseModal>

    <BaseModal
      :open="modalPasswordAbierto"
      :title="`Cambiar contraseña · ${usuarioSeleccionado?.username ?? ''}`"
      @close="modalPasswordAbierto = false"
    >
      <form class="space-y-4" @submit.prevent="cambiarPassword">
        <BaseInput
          v-model="nuevaPassword"
          label="Nueva contraseña"
          type="password"
          :error="errorPassword"
          required
        />
        <div class="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
          <BaseButton
            type="button"
            variant="secondary"
            class="w-full sm:w-auto"
            @click="modalPasswordAbierto = false"
          >
            Cancelar
          </BaseButton>
          <BaseButton
            type="submit"
            variant="primary"
            class="w-full sm:w-auto"
            :loading="guardandoPassword"
          >
            Guardar
          </BaseButton>
        </div>
      </form>
    </BaseModal>

    <!-- HU-05 Editar usuario / HU-06 Asignar roles y permisos -->
    <BaseModal
      :open="modalEditarAbierto"
      :title="`Editar usuario · ${usuarioEditando?.username ?? ''}`"
      @close="modalEditarAbierto = false"
    >
      <form class="space-y-4" @submit.prevent="guardarEdicion">
        <p class="text-sm text-ink-500">
          Usuario: <span class="font-semibold text-ink-900">{{ usuarioEditando?.username }}</span>
        </p>
        <label class="block">
          <span class="mb-1.5 block text-sm font-medium text-ink-900">Rol</span>
          <select
            v-model="formEditar.rol"
            class="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-ink-900 outline-none focus:border-navy-900 focus:ring-2 focus:ring-navy-900/20"
          >
            <option value="admin">Administrador</option>
            <option value="supervisor">Supervisor</option>
            <option value="supervisor_pesaje">Supervisor de Pesaje</option>
            <option value="produccion">Producción</option>
            <option value="picky">Picky</option>
            <option value="pesaje">Pesaje</option>
            <option value="mezcla">Mezcla</option>
            <option value="extrusion">Extrusión</option>
            <option value="calidad">Calidad</option>
            <option value="empaque">Empaque</option>
            <option value="planta">Personal de Planta</option>
          </select>
          <span v-if="erroresEditar.rol" class="mt-1 block text-sm text-danger">{{
            erroresEditar.rol
          }}</span>
        </label>
        <label class="flex items-center gap-2">
          <input
            v-model="formEditar.is_active"
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300"
          />
          <span class="text-sm font-medium text-ink-900">Usuario activo</span>
        </label>

        <div class="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
          <BaseButton
            type="button"
            variant="secondary"
            class="w-full sm:w-auto"
            @click="modalEditarAbierto = false"
          >
            Cancelar
          </BaseButton>
          <BaseButton
            type="submit"
            variant="primary"
            class="w-full sm:w-auto"
            :loading="guardandoEdicion"
          >
            Guardar cambios
          </BaseButton>
        </div>
      </form>
    </BaseModal>
  </main>
</template>
