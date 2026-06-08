<template>
  <div>
    <div class="page-head">
      <div>
        <h1>{{ site?.name || 'Сайт' }}</h1>
        <p class="muted">{{ site?.url }}</p>
      </div>
      <RouterLink v-if="site" class="button" :to="`/clients/${site.client_id}`">К клиенту</RouterLink>
    </div>

    <div v-if="site" class="stats">
      <div><b>{{ healthLabel(site) }}</b><span>Жив/мертв</span></div>
      <div><b>{{ site.status }}</b><span>Статус</span></div>
      <div><b>{{ site.joomla_version }}</b><span>Joomla</span></div>
      <div><b>{{ orders.length }}</b><span>Заявки</span></div>
    </div>

    <section v-if="site">
      <div class="toolbar">
        <button type="button" @click="download('leadhub-connector.php')"><Download :size="18" /> leadhub-connector.php</button>
        <button type="button" @click="download('lh.php')"><Download :size="18" /> lh.php</button>
        <button type="button" @click="ping"><PlugZap :size="18" /> Проверить</button>
        <button type="button" @click="discover"><Search :size="18" /> Discover</button>
        <button type="button" @click="sync"><RefreshCw :size="18" /> Sync</button>
        <button type="button" @click="activate"><Power :size="18" /> Активировать</button>
        <button type="button" class="danger" @click="deleteSite"><Trash2 :size="18" /> Удалить сайт</button>
      </div>
      <p v-if="message" class="notice">{{ message }}</p>
      <p v-if="site.last_error" class="error">Ошибка: {{ site.last_error }}</p>
    </section>

    <section>
      <div class="page-head compact">
        <h2>Заявки и заказы сайта</h2>
        <button type="button" @click="downloadCsv">CSV</button>
      </div>

      <form class="filters site-orders" @submit.prevent="loadOrders">
        <input v-model="filters.search" placeholder="Поиск" />
        <select v-model="filters.source_type">
          <option value="">Все источники</option>
          <option value="rsform">RSForm</option>
          <option value="virtuemart">VirtueMart</option>
        </select>
        <select v-model="filters.internal_status">
          <option value="">Все статусы</option>
          <option value="new">new</option>
          <option value="in_progress">in_progress</option>
          <option value="done">done</option>
          <option value="cancelled">cancelled</option>
        </select>
        <input v-model="filters.date_from" type="date" />
        <input v-model="filters.date_to" type="date" />
        <select v-model="sortKey">
          <option value="created_at">По дате</option>
          <option value="customer_name">По клиенту</option>
          <option value="amount">По сумме</option>
          <option value="internal_status">По статусу</option>
        </select>
        <button type="submit">Применить</button>
      </form>

      <DataTable :columns="orderColumns" :rows="sortedOrders">
        <template #external_number="{ row }">
          <RouterLink :to="`/orders/${row.id}`">{{ row.external_number || row.external_id }}</RouterLink>
        </template>
        <template #amount="{ row }">{{ row.amount ? `${row.amount} ${row.currency || ''}` : '' }}</template>
        <template #internal_status="{ row }"><StatusBadge :value="row.internal_status" /></template>
      </DataTable>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download, PlugZap, Power, RefreshCw, Search, Trash2 } from 'lucide-vue-next'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const site = ref(null)
const orders = ref([])
const message = ref('')
const sortKey = ref('created_at')
const filters = reactive({
  search: '',
  source_type: '',
  internal_status: '',
  date_from: '',
  date_to: ''
})

const orderColumns = [
  { key: 'source_type', label: 'Источник' },
  { key: 'external_number', label: 'Номер' },
  { key: 'customer_name', label: 'Клиент' },
  { key: 'customer_phone', label: 'Телефон' },
  { key: 'amount', label: 'Сумма' },
  { key: 'internal_status', label: 'Статус' }
]

const sortedOrders = computed(() => {
  return [...orders.value].sort((a, b) => {
    const av = a[sortKey.value] || ''
    const bv = b[sortKey.value] || ''
    if (sortKey.value === 'amount') return Number(bv || 0) - Number(av || 0)
    return String(bv).localeCompare(String(av))
  })
})

function healthClass(currentSite) {
  if (currentSite.status === 'error' || currentSite.status === 'disabled') return 'dead'
  if (currentSite.status === 'connected' || currentSite.status === 'active') return 'alive'
  return 'unknown'
}

function healthLabel(currentSite) {
  const map = { alive: 'Жив', dead: 'Мертв', unknown: 'Не проверен' }
  return map[healthClass(currentSite)]
}

function queryString() {
  const params = new URLSearchParams({ site_id: route.params.id })
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value)
  }
  return params.toString()
}

async function loadSite() {
  site.value = await api(`/sites/${route.params.id}`)
}

async function loadOrders() {
  orders.value = await api(`/orders?${queryString()}`)
}

async function reload() {
  await loadSite()
  await loadOrders()
}

async function download(filename) {
  const response = await fetch(`/api/sites/${route.params.id}/connector/download?filename=${encodeURIComponent(filename)}`, {
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

async function downloadCsv() {
  const response = await fetch(`/api/orders/export.csv?${queryString()}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('zakaz_token')}` }
  })
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `site-${route.params.id}-orders.csv`
  link.click()
  URL.revokeObjectURL(url)
}

async function ping() {
  message.value = (await api(`/sites/${route.params.id}/ping`, { method: 'POST' })).message
  await reload()
}

async function discover() {
  const response = await api(`/sites/${route.params.id}/discover`, { method: 'POST' })
  message.value = `${response.message}: ${JSON.stringify(response.data?.sources || {})}`
  await reload()
}

async function sync() {
  const response = await api(`/sites/${route.params.id}/sync`, { method: 'POST' })
  message.value = `${response.message}: created ${response.data?.created || 0}, updated ${response.data?.updated || 0}`
  await reload()
}

async function activate() {
  await api(`/sites/${route.params.id}/activate`, { method: 'POST' })
  await reload()
}

async function deleteSite() {
  if (!site.value) return
  const clientId = site.value.client_id
  if (!confirm(`Удалить сайт "${site.value.name}" вместе с его заявками и логами синхронизации?`)) return
  await api(`/sites/${route.params.id}`, { method: 'DELETE' })
  await router.push(`/clients/${clientId}`)
}

onMounted(reload)
</script>
