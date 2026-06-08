<template>
  <div>
    <div class="page-head">
      <h1>Директ</h1>
    </div>
    <form class="inline-form" @submit.prevent="upload">
      <input type="file" accept=".csv,text/csv" @change="file = $event.target.files[0]" />
      <button type="submit">Импорт CSV</button>
    </form>
    <div class="stats">
      <div><b>{{ summary.cost }}</b><span>Расход</span></div>
      <div><b>{{ summary.clicks }}</b><span>Клики</span></div>
      <div><b>{{ summary.impressions }}</b><span>Показы</span></div>
    </div>
    <p v-if="message" class="notice">{{ message }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const summary = ref({ cost: 0, clicks: 0, impressions: 0 })
const file = ref(null)
const message = ref('')

onMounted(async () => {
  summary.value = await api('/analytics/direct/summary')
})

async function upload() {
  if (!file.value) return
  const form = new FormData()
  form.append('file', file.value)
  const response = await fetch('/api/analytics/direct/import-csv', {
    method: 'POST',
    headers: { Authorization: `Bearer ${localStorage.getItem('zakaz_token')}` },
    body: form
  })
  const data = await response.json()
  message.value = `${data.filename}: ${data.status}`
}
</script>
