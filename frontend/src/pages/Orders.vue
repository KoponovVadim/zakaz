<template>
  <div>
    <div class="page-head">
      <h1>{{ pageTitle }}</h1>
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
      <select v-if="filters.source_type === 'rsform'" v-model="formKey">
        <option value="">Все формы</option>
        <option v-for="form in forms" :key="form.id" :value="`${form.site_id}:${form.external_form_id}`">
          {{ form.site_name }} — {{ form.name || 'Форма не определена' }}
        </option>
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
      <template #external_created_at="{ row }">
        {{ formatDate(row.external_created_at || row.created_at) }}
      </template>
      <template #external_number="{ row }">
        <RouterLink :to="`/orders/${row.id}`">{{ row.external_number || row.external_id }}</RouterLink>
      </template>
      <template #source_form_name="{ row }">
        {{ row.source_form_name || 'Форма не определена' }}
      </template>
      <template #client_name="{ row }">
        <RouterLink :to="`/clients/${row.client_id}`">{{ row.client_name || row.client_id }}</RouterLink>
      </template>
      <template #message="{ row }">
        {{ shortText(row.message) }}
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../api/client'

const route = useRoute()
const orders = ref([])
const clients = ref([])
const sites = ref([])
const forms = ref([])
const formKey = ref('')
const filters = reactive({
  search: '',
  client_id: '',
  site_id: '',
  source_type: '',
  internal_status: '',
  date_from: '',
  date_to: ''
})

const pageSource = computed(() => {
  if (route.path.endsWith('/rsform')) return 'rsform'
  if (route.path.endsWith('/virtuemart')) return 'virtuemart'
  return ''
})

const pageTitle = computed(() => {
  if (filters.source_type === 'rsform') return 'Заявки RSForm'
  if (filters.source_type === 'virtuemart') return 'Заказы VirtueMart'
  return 'Все обращения'
})

const columns = computed(() => {
  if (filters.source_type === 'rsform') {
    return [
      { key: 'external_created_at', label: 'Дата' },
      { key: 'client_name', label: 'Клиент' },
      { key: 'site_name', label: 'Сайт' },
      { key: 'source_form_name', label: 'Форма' },
      { key: 'customer_name', label: 'Имя' },
      { key: 'customer_phone', label: 'Телефон' },
      { key: 'customer_email', label: 'Email' },
      { key: 'message', label: 'Сообщение' },
      { key: 'internal_status', label: 'Статус' }
    ]
  }
  if (filters.source_type === 'virtuemart') {
    return [
      { key: 'external_created_at', label: 'Дата' },
      { key: 'client_name', label: 'Клиент' },
      { key: 'site_name', label: 'Сайт' },
      { key: 'external_number', label: 'Номер заказа' },
      { key: 'customer_name', label: 'Имя' },
      { key: 'customer_phone', label: 'Телефон' },
      { key: 'customer_email', label: 'Email' },
      { key: 'amount', label: 'Сумма' },
      { key: 'external_status', label: 'Внешний статус' },
      { key: 'internal_status', label: 'Статус' }
    ]
  }
  return [
    { key: 'source_type', label: 'Источник' },
    { key: 'external_number', label: 'Номер' },
    { key: 'client_name', label: 'Клиент' },
    { key: 'site_name', label: 'Сайт' },
    { key: 'customer_name', label: 'Покупатель' },
    { key: 'customer_phone', label: 'Телефон' },
    { key: 'amount', label: 'Сумма' },
    { key: 'internal_status', label: 'Статус' }
  ]
})

function queryString() {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value)
  }
  if (formKey.value) {
    const [siteId, formId] = formKey.value.split(':')
    if (siteId) params.set('site_id', siteId)
    if (formId) params.set('source_form_id', formId)
  }
  return params.toString()
}

function shortText(value) {
  if (!value) return ''
  return value.length > 120 ? `${value.slice(0, 120)}...` : value
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function loadForms() {
  if (filters.source_type !== 'rsform') {
    forms.value = []
    formKey.value = ''
    return
  }
  const params = new URLSearchParams()
  if (filters.client_id) params.set('client_id', filters.client_id)
  if (filters.site_id) params.set('site_id', filters.site_id)
  const query = params.toString()
  forms.value = await api(`/rsform/forms${query ? `?${query}` : ''}`)
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
  filters.source_type = pageSource.value || route.query.source_type || ''
  filters.internal_status = route.query.internal_status || ''
  filters.search = route.query.search || ''
  if (route.query.source_form_id && route.query.site_id) {
    formKey.value = `${route.query.site_id}:${route.query.source_form_id}`
  }
  clients.value = await api('/clients')
  sites.value = await api('/sites')
  await loadForms()
  await load()
})

watch(() => [filters.source_type, filters.client_id, filters.site_id], loadForms)
</script>
