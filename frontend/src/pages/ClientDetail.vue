<template>
  <div>
    <div class="page-head">
      <h1>{{ client?.name || 'Клиент' }}</h1>
      <RouterLink class="button" :to="`/sites/add?client_id=${route.params.id}`">Добавить сайт</RouterLink>
    </div>
    <p class="muted">{{ client?.comment }}</p>

    <div class="stats">
      <div><b>{{ sites.length }}</b><span>Сайты</span></div>
      <div><b>{{ aliveCount }}</b><span>Живые</span></div>
      <div><b>{{ deadCount }}</b><span>Проблемные</span></div>
    </div>

    <section>
      <h2>Сайты клиента</h2>
      <DataTable :columns="siteColumns" :rows="sites">
        <template #name="{ row }">
          <RouterLink :to="`/sites/${row.id}`">{{ row.name }}</RouterLink>
        </template>
        <template #health="{ row }">
          <span class="health" :class="healthClass(row)">{{ healthLabel(row) }}</span>
        </template>
        <template #status="{ row }"><SiteStatusBadge :value="row.status" /></template>
        <template #last_ping_at="{ row }">{{ formatDate(row.last_ping_at) }}</template>
        <template #actions="{ row }">
          <div class="row-actions">
            <button class="icon-button" title="Проверить сайт" @click="ping(row.id)"><PlugZap :size="18" /></button>
            <button class="icon-button danger" title="Удалить сайт" @click="deleteSite(row)"><Trash2 :size="18" /></button>
          </div>
        </template>
      </DataTable>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PlugZap, Trash2 } from 'lucide-vue-next'
import DataTable from '../components/DataTable.vue'
import SiteStatusBadge from '../components/SiteStatusBadge.vue'
import { api } from '../api/client'

const route = useRoute()
const client = ref(null)
const sites = ref([])
const siteColumns = [
  { key: 'name', label: 'Сайт' },
  { key: 'url', label: 'URL' },
  { key: 'health', label: 'Жив/мертв' },
  { key: 'status', label: 'Статус' },
  { key: 'last_ping_at', label: 'Последняя проверка' },
  { key: 'actions', label: '' }
]

const aliveCount = computed(() => sites.value.filter((site) => healthClass(site) === 'alive').length)
const deadCount = computed(() => sites.value.filter((site) => healthClass(site) === 'dead').length)

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
  client.value = await api(`/clients/${route.params.id}`)
  sites.value = await api(`/sites?client_id=${route.params.id}`)
}

async function ping(id) {
  await api(`/sites/${id}/ping`, { method: 'POST' })
  await load()
}

async function deleteSite(site) {
  if (!confirm(`Удалить сайт "${site.name}" вместе с его заявками и логами синхронизации?`)) return
  await api(`/sites/${site.id}`, { method: 'DELETE' })
  await load()
}

onMounted(load)
</script>
