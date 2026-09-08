<script setup>
import Badge from '../ui/Badge.vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
  campos: { type: Array, required: true },
  errores: { type: Object, default: () => ({}) },
  editable: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
function actualizar(campo, valor) {
  emit('update:modelValue', { ...props.modelValue, [campo]: valor })
}
</script>

<template>
  <div class="grid grid-cols-1 gap-x-6 gap-y-4 lg:grid-cols-2">
    <fieldset v-for="[campo, label] in campos" :key="campo" class="min-w-0">
      <legend class="mb-1.5 text-sm font-medium text-ink-900">{{ label }}</legend>
      <div v-if="editable" class="grid grid-cols-2 gap-2 sm:max-w-md">
        <label
          v-for="opcion in [true, false]"
          :key="String(opcion)"
          class="flex items-center gap-2 rounded-lg border px-3.5 py-2.5 text-sm"
          :class="
            modelValue[campo] === opcion ? 'border-navy-900 bg-navy-900/5' : 'border-slate-300'
          "
        >
          <input
            :checked="modelValue[campo] === opcion"
            type="radio"
            :name="campo"
            :value="opcion"
            required
            class="h-4 w-4 border-slate-300"
            @change="actualizar(campo, opcion)"
          />
          <span class="text-ink-900">{{ opcion ? 'Cumple' : 'No cumple' }}</span>
        </label>
      </div>
      <Badge
        v-else
        :color="modelValue[campo] === false ? 'red' : modelValue[campo] === true ? 'blue' : 'gray'"
        >{{
          modelValue[campo] === null ? 'Pendiente' : modelValue[campo] ? 'Cumple' : 'No cumple'
        }}</Badge
      >
      <p v-if="errores[campo]" class="mt-1 text-sm text-danger">{{ errores[campo] }}</p>
    </fieldset>
  </div>
</template>
