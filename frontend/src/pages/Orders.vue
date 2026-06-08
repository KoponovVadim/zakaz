<template>
  <div>
    <div class="page-head">
      <h1>Заявки и заказы</h1>
      <button type="button" @click="downloadCsv">CSV</button>
    </div>

    <form class="filters" @submit.prevent="load">
      <input v-model="filters.search" placeholder="Поиск" />
      <select v-model="filters.client_id">
        <option value="">Все клиенты</option>
        <option v-for="client in clients" :key="client.id" :value="client.id">{{ client.name }}</option>
      </select>
      <select v-model="filters.site_id">
        <option value="">Все сайты</option>
        <option v-for="site in sites" :key="site.id" :value="site.id">{{ site.name }}</option>
      </select>
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
      <button type="submit">Применить</button>
    </form>

    <DataTable :columns="columns" :rows="orders">
      <template #external_number="{ row }">
        <RouterLink :to="`/orders/${row.id}`">{{ row.external_number || row.external_id }}</RouterLink>
      </template>
      <template #client_name="{ row }">
        <RouterLink :to="`/clients/${row.client_id}`">{{ row.client_name || row.client_id }}</RouterLink>
      </template>
      <template #amount="{ row }">
        {{ row.amount ? `${row.amount} ${row.currency || ''}` : '' }}
      </template>
      <template #internal_status="{ row }">
        <StatusBadge :value="row.internal_status" />
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../api/client'

const route = useRoute()
const orders = ref([])
const clients = ref([])
const sites = ref([])
const filters = reactive({
  search: '',
  client_id: '',
  site_id: '',
  source_type: '',
  internal_status: '',
  date_from: '',
  date_to: ''
})

const columns = [
  { key: 'source_type', label: 'Источник' },
  { key: 'external_number', label: 'Номер' },
  { key: 'client_name', label: 'Клиент' },
  { key: 'site_name', label: 'Сайт' },
  { key: 'customer_name', label: 'Покупатель' },
  { key: 'customer_phone', label: 'Телефон' },
  { key: 'amount', label: 'Сумма' },
  { key: 'internal_status', label: 'Статус' }
]

function queryString() {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value)
  }
  return params.toString()
}

async function load() {
  const query = queryString()
  orders.value = await api(`/orders${query ? `?${query}` : ''}`)
}

async function downloadCsv() {
  const query = queryString()
  const response = await fetch(`/api/orders/export.csv${query ? `?${query}` : ''}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('zakaz_token')}` }
  })
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'orders.csv'
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  filters.client_id = route.query.client_id || ''
  filters.site_id = route.query.site_id || ''
  filters.source_type = route.query.source_type || ''
  filters.internal_status = route.query.internal_status || ''
  filters.search = route.query.search || ''
  clients.value = await api('/clients')
  sites.value = await api('/sites')
  await load()
})
</script>
