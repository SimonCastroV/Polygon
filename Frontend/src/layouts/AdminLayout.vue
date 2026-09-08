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
      class="flex flex-col gap-3 border-l-4 border-accent-blue bg-navy-900 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6"
    >
      <div>
        <h1 class="text-lg font-bold text-white">Polygon</h1>
        <p class="text-sm text-slate-300">Sumicolor · Sistema de producción</p>
      </div>

      <div class="flex items-center justify-between gap-4 sm:justify-end">
        <div class="text-right">
          <p class="text-sm font-semibold text-white">{{ auth.user?.username }}</p>
          <Badge color="blue">{{ auth.user?.rol_display }}</Badge>
        </div>
        <BaseButton variant="secondary" @click="cerrarSesion">Cerrar sesión</BaseButton>
      </div>
    </header>

    <nav class="flex gap-1 overflow-x-auto border-b border-slate-200 bg-white px-4 sm:px-6">
      <router-link
        v-if="auth.rol === 'admin'"
        :to="{ name: 'admin-usuarios' }"
        class="shrink-0 border-b-2 border-transparent px-3 py-3 text-sm font-semibold"
        active-class="border-navy-900 text-navy-900"
        exact-active-class="border-navy-900 text-navy-900"
      >
        Usuarios
      </router-link>
      <router-link
        v-if="['admin', 'supervisor', 'produccion'].includes(auth.rol)"
        :to="{ name: 'admin-ordenes-produccion' }"
        class="shrink-0 border-b-2 border-transparent px-3 py-3 text-sm font-semibold"
        active-class="border-navy-900 text-navy-900"
        exact-active-class="border-navy-900 text-navy-900"
      >
        Órdenes de Producción
      </router-link>
      <router-link
        v-if="auth.rol === 'picky'"
        :to="{ name: 'picky-ordenes' }"
        class="shrink-0 border-b-2 border-transparent px-3 py-3 text-sm font-semibold"
        active-class="border-navy-900 text-navy-900"
        exact-active-class="border-navy-900 text-navy-900"
      >
        Picky
      </router-link>
      <router-link
        v-if="auth.rol === 'pesaje'"
        :to="{ name: 'pesaje-ordenes' }"
        class="shrink-0 border-b-2 border-transparent px-3 py-3 text-sm font-semibold"
        active-class="border-navy-900 text-navy-900"
        exact-active-class="border-navy-900 text-navy-900"
      >
        Pesaje
      </router-link>
      <router-link
        v-if="auth.rol === 'supervisor_pesaje'"
        :to="{ name: 'supervision-pesaje-ordenes' }"
        class="shrink-0 border-b-2 border-transparent px-3 py-3 text-sm font-semibold"
        active-class="border-navy-900 text-navy-900"
        exact-active-class="border-navy-900 text-navy-900"
      >
        Supervisión de Pesaje
      </router-link>
    </nav>

    <router-view />
  </div>
</template>
