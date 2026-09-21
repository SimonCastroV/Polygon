<script setup>
// Franja superior de una card de OP con el color de su hoja física (ver
// HOJA_OP). Va como primer hijo de una card con p-5 y overflow-hidden: los
// márgenes negativos la llevan de borde a borde.
import { computed } from 'vue'
import { HOJA_OP } from '../../utils/ordenes'

const props = defineProps({
  clasificacion: {
    type: String,
    default: '',
  },
})

const hoja = computed(() => HOJA_OP[props.clasificacion])
</script>

<template>
  <p
    v-if="hoja"
    class="-mx-5 -mt-5 px-5 py-2 text-xs font-bold uppercase tracking-wide"
    :class="hoja.franja"
  >
    {{ hoja.texto }}
  </p>
</template>
