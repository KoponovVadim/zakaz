<template>
  <div>
    <div class="page-head">
      <h1>Дашборд</h1>
      <button type="button" @click="refreshAll">Обновить</button>
    </div>

    <div class="stats">
      <div><b>{{ clients.length }}</b><span>Клиенты</span></div>
      <div><b>{{ sites.length }}</b><span>Сайты</span></div>
      <div><b>{{ aliveCount }}</b><span>Живые</span></div>
      <div><b>{{ deadCount }}</b><span>Проблемные</span></div>
    </div>

    <section v-for="client in clients" :key="client.id" class="client-block">
      <div class="page-head compact">
        <h2><RouterLink :to="`/clients/${client.id}`">{{ client.name }}</RouterLink></h2>
        <RouterLink :to="`/sites/add?client_id=${client.id}`">Добавить сайт</RouterLink>
      </div>

      <DataTable :columns="columns" :rows="sitesByClient(client.id)">
        <template #name="{ row }">
          <RouterLink :to="`/sites/${row.id}`">{{ row.name }}</RouterLink>
        </template>
        <template #health="{ row }">
          <span class="health" :class="healthClass(row)">{{ healthLabel(row) }}</span>
        </template>
        <template #status="{ row }"><SiteStatusBadge :value="row.status" /></template>
        <template #last_ping_at="{ row }">{{ formatDate(row.last_ping_at) }}</template>
        <template #actions="{ row }">
          <button class="icon-button" title="Проверить сайт" @click="ping(row.id)"><PlugZap :size="18" /></button>
        </template>
      </DataTable>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { PlugZap } from 'lucide-vue-next'
import DataTable from '../components/DataTable.vue'
import SiteStatusBadge from '../components/SiteStatusBadge.vue'
import { api } from '../api/client'

const clients = ref([])
const sites = ref([])
let timer = null

const columns = [
  { key: 'name', label: 'Сайт' },
  { key: 'url', label: 'URL' },
  { key: 'health', label: 'Жив/мертв' },
  { key: 'status', label: 'Статус' },
  { key: 'last_ping_at', label: 'Последняя проверка' },
  { key: 'actions', label: '' }
]

const aliveCount = computed(() => sites.value.filter((site) => healthClass(site) === 'alive').length)
const deadCount = computed(() => sites.value.filter((site) => healthClass(site) === 'dead').length)

function sitesByClient(clientId) {
  return sites.value.filter((site) => site.client_id === clientId)
}

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

async function load() {
  clients.value = await api('/clients')
  sites.value = await api('/sites')
}

async function ping(id) {
  await api(`/sites/${id}/ping`, { method: 'POST' })
  await load()
}

async function refreshAll() {
  await load()
}

onMounted(async () => {
  await load()
  timer = window.setInterval(load, 15000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>
