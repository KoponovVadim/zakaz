<template>
  <StatusBadge :value="value" />
</template>

<script setup>
import StatusBadge from './StatusBadge.vue'
defineProps({ value: { type: String, required: true } })
</script>
