<template>
  <div>
    <div class="page-head">
      <h1>Сайты</h1>
      <RouterLink class="button" to="/sites/add"><Plus :size="18" /> Добавить сайт</RouterLink>
    </div>
    <DataTable :columns="columns" :rows="sites">
      <template #name="{ row }"><RouterLink :to="`/sites/${row.id}`">{{ row.name }}</RouterLink></template>
      <template #health="{ row }">
        <span class="health" :class="healthClass(row)">{{ healthLabel(row) }}</span>
      </template>
      <template #status="{ row }"><SiteStatusBadge :value="row.status" /></template>
      <template #last_ping_at="{ row }">{{ formatDate(row.last_ping_at) }}</template>
      <template #actions="{ row }">
        <div class="row-actions">
          <button class="icon-button" title="Скачать leadhub-connector.php" @click="download(row.id, 'leadhub-connector.php')"><Download :size="18" /></button>
          <button class="icon-button" title="Проверить сайт" @click="ping(row.id)"><PlugZap :size="18" /></button>
          <button class="icon-button danger" title="Удалить сайт" @click="deleteSite(row)"><Trash2 :size="18" /></button>
        </div>
      </template>
    </DataTable>
    <p v-if="message" class="notice">{{ message }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Download, PlugZap, Plus, Trash2 } from 'lucide-vue-next'
import DataTable from '../components/DataTable.vue'
import SiteStatusBadge from '../components/SiteStatusBadge.vue'
import { api } from '../api/client'

const sites = ref([])
const message = ref('')
const columns = [
  { key: 'name', label: 'Сайт' },
  { key: 'url', label: 'URL' },
  { key: 'health', label: 'Жив/мертв' },
  { key: 'status', label: 'Статус' },
  { key: 'last_ping_at', label: 'Последняя проверка' },
  { key: 'actions', label: '' }
]

function healthClass(site) {
  if (site.status === 'error' || site.status === 'disabled') return 'dead'
  if (site.status === 'connected' || site.status === 'active') return 'alive'
  return 'unknown'
}

function healthLabel(site) {
  const map = { alive: 'Жив', dead: 'Мертв', unknown: 'Не проверен' }
  return map[healthClass(site)]
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : '-'
}

async function download(id, filename) {
  const response = await fetch(`/api/sites/${id}/connector/download?filename=${encodeURIComponent(filename)}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('zakaz_token')}` }
  })
  if (!response.ok) {
    message.value = await response.text()
    return
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

async function load() {
  sites.value = await api('/sites')
}

async function ping(id) {
  message.value = (await api(`/sites/${id}/ping`, { method: 'POST' })).message
  await load()
}

async function deleteSite(site) {
  if (!confirm(`Удалить сайт "${site.name}" вместе с его заявками и логами синхронизации?`)) return
  await api(`/sites/${site.id}`, { method: 'DELETE' })
  message.value = 'Сайт удален'
  await load()
}

onMounted(load)
</script>
