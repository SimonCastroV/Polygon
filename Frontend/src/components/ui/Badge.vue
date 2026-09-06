<script setup>
defineProps({
  color: {
    type: String,
    default: 'gray', // navy | blue | gray | amber | red
  },
})

const colorClasses = {
  navy: 'bg-navy-900 text-white',
  blue: 'bg-accent-blue text-white',
  gray: 'bg-slate-200 text-ink-900',
  amber: 'bg-warning-bg text-amber-800 border border-warning',
  red: 'bg-danger text-white',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
    :class="colorClasses[color]"
  >
    <slot />
  </span>
</template>
