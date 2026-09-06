<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import Badge from '../components/ui/Badge.vue'
import BaseButton from '../components/ui/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()

async function cerrarSesion() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen bg-surface">
    <header
      class="flex items-center justify-between border-l-4 border-accent-blue bg-navy-900 px-6 py-4"
    >
      <div>
        <h1 class="text-lg font-bold text-white">Panel de Administración</h1>
        <p class="text-sm text-slate-300">Polygon · Sumicolor</p>
      </div>

      <div class="flex items-center gap-4">
        <div class="text-right">
          <p class="text-sm font-semibold text-white">{{ auth.user?.username }}</p>
          <Badge color="blue">{{ auth.user?.rol_display }}</Badge>
        </div>
        <BaseButton variant="secondary" @click="cerrarSesion">Cerrar sesión</BaseButton>
      </div>
    </header>

    <router-view />
  </div>
</template>
