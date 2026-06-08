<template>
  <div>
    <div class="page-head">
      <h1>Сайты</h1>
      <RouterLink class="button" to="/sites/add"><Plus :size="18" /> Добавить сайт</RouterLink>
    </div>
    <DataTable :columns="columns" :rows="sites">
      <template #status="{ row }"><SiteStatusBadge :value="row.status" /></template>
      <template #actions="{ row }">
        <div class="row-actions">
          <button class="icon-button" title="Скачать connector.php" @click="download(row.id)"><Download :size="18" /></button>
          <button class="icon-button" title="Ping" @click="ping(row.id)"><PlugZap :size="18" /></button>
          <button class="icon-button" title="Discover" @click="discover(row.id)"><Search :size="18" /></button>
          <button class="icon-button" title="Sync" @click="sync(row.id)"><RefreshCw :size="18" /></button>
          <button class="icon-button" title="Активировать" @click="activate(row.id)"><Power :size="18" /></button>
        </div>
      </template>
    </DataTable>
    <p v-if="message" class="notice">{{ message }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Download, PlugZap, Plus, Power, RefreshCw, Search } from 'lucide-vue-next'
import DataTable from '../components/DataTable.vue'
import SiteStatusBadge from '../components/SiteStatusBadge.vue'
import { api } from '../api/client'

const sites = ref([])
const message = ref('')
const columns = [
  { key: 'name', label: 'Сайт' },
  { key: 'url', label: 'URL' },
  { key: 'joomla_version', label: 'Joomla' },
  { key: 'status', label: 'Статус' },
  { key: 'actions', label: '' }
]

async function download(id) {
  const response = await fetch(`/api/sites/${id}/connector/download`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('zakaz_token')}` }
  })
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'leadhub-connector.php'
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

async function discover(id) {
  message.value = (await api(`/sites/${id}/discover`, { method: 'POST' })).message
  await load()
}

async function sync(id) {
  const response = await api(`/sites/${id}/sync`, { method: 'POST' })
  message.value = `${response.message}: created ${response.data?.created || 0}, updated ${response.data?.updated || 0}`
  await load()
}

async function activate(id) {
  await api(`/sites/${id}/activate`, { method: 'POST' })
  await load()
}

onMounted(load)
</script>
