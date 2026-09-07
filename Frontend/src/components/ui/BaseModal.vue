<script setup>
defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
})

defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      @click.self="$emit('close')"
    >
      <div class="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl bg-white p-4 shadow-xl sm:p-6">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-bold text-ink-900">{{ title }}</h2>
          <button
            type="button"
            class="rounded-lg p-1 text-ink-500 hover:bg-surface-alt hover:text-ink-900"
            @click="$emit('close')"
          >
            ✕
          </button>
        </div>

        <div class="overflow-y-auto">
          <slot />
        </div>

        <div v-if="$slots.footer" class="mt-6 flex justify-end gap-3">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
