<script setup>
import { ref, onMounted } from 'vue'
import api from './services/api'

const estado = ref('Probando conexión...')

onMounted(async () => {
  try {
    const { data } = await api.get('/health/')
    estado.value = `Conectado ✅ — respuesta del backend: ${JSON.stringify(data)}`
  } catch (e) {
    estado.value = `Error de conexión ❌ — ${e.message}`
  }
})
</script>

<template>
  <div style="padding: 2rem; font-family: sans-serif;">
    <h1>Polygon — Test de conexión</h1>
    <p>{{ estado }}</p>
  </div>
</template>