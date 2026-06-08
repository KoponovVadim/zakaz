<template>
  <span class="badge" :class="value">{{ value }}</span>
</template>

<script setup>
defineProps({ value: { type: String, required: true } })
</script>
