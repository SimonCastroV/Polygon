<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { destinoSegunRol } from '../../router'
import { useAuthStore } from '../../store/auth'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseButton from '../../components/ui/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push(destinoSegunRol(auth.rol))
  } catch (e) {
    const detail = e.response?.data?.detail
    error.value = Array.isArray(detail) ? detail[0] : detail || 'No se pudo iniciar sesión.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-navy-900 px-4">
    <div class="w-full max-w-sm">
      <div class="mb-8 text-center">
        <div class="mx-auto mb-3 h-1 w-12 rounded-full bg-accent-blue" />
        <h1 class="text-2xl font-bold text-white">Polygon</h1>
        <p class="text-sm text-slate-300">Sumicolor · Sistema de producción</p>
      </div>

      <form class="rounded-2xl bg-white p-8 shadow-xl" @submit.prevent="onSubmit">
        <h2 class="mb-6 text-lg font-bold text-ink-900">Iniciar sesión</h2>

        <div class="space-y-4">
          <BaseInput
            v-model="username"
            label="Usuario"
            placeholder="ej. admin, pesaje1"
            required
            autofocus
          />
          <BaseInput
            v-model="password"
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            required
          />
        </div>

        <p v-if="error" class="mt-4 text-sm font-medium text-danger">{{ error }}</p>

        <BaseButton type="submit" variant="primary" :loading="loading" class="mt-6 w-full">
          Ingresar
        </BaseButton>
      </form>
    </div>
  </div>
</template>
