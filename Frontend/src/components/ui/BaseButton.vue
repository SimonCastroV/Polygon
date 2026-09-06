<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary', // primary | secondary | danger
  },
  type: {
    type: String,
    default: 'button',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const variantClasses = {
  primary: 'bg-navy-900 text-white hover:bg-navy-800 focus-visible:outline-navy-900',
  secondary:
    'bg-white text-ink-900 border border-slate-300 hover:bg-surface-alt focus-visible:outline-navy-900',
  danger: 'bg-danger text-white hover:bg-red-700 focus-visible:outline-danger',
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold shadow-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
    :class="variantClasses[variant]"
  >
    <svg v-if="loading" class="h-4 w-4 animate-spin text-current" viewBox="0 0 24 24" fill="none">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
    <slot />
  </button>
</template>
