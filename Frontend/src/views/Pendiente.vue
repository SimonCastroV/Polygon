<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import BaseButton from '../components/ui/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()

async function cerrarSesion() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-navy-900">
    <header class="border-l-4 border-accent-blue bg-navy-900 px-6 py-4">
      <h1 class="text-lg font-bold text-white">Polygon</h1>
      <p class="text-sm text-slate-300">Sumicolor · Sistema de producción</p>
    </header>

    <main class="flex flex-1 items-center justify-center bg-surface px-4">
      <div class="max-w-md rounded-2xl bg-white p-8 text-center shadow-xl">
        <p class="text-sm font-semibold text-ink-500">Conectado como {{ auth.user?.username }}</p>
        <h2 class="mt-2 text-xl font-bold text-ink-900">Tu vista aún no está disponible</h2>
        <p class="mt-2 text-sm text-ink-500">
          Esta sección del sistema todavía está en construcción para tu rol.
        </p>
        <BaseButton variant="secondary" class="mt-6" @click="cerrarSesion">
          Cerrar sesión
        </BaseButton>
      </div>
    </main>
  </div>
</template>
