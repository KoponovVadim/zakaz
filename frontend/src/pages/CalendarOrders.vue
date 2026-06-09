<template>
  <div>
    <div class="page-head">
      <h1>Календарь заказов</h1>
      <button type="button" @click="downloadCsv">CSV</button>
    </div>

    <form class="calendar-controls" @submit.prevent="load">
      <div class="segmented">
        <button v-for="item in modes" :key="item.value" type="button" :class="{ active: mode === item.value }" @click="setMode(item.value)">
          {{ item.label }}
        </button>
      </div>
      <input v-if="mode === 'day' || mode === 'week'" v-model="selectedDate" type="date" />
      <input v-if="mode === 'month'" v-model="selectedMonth" type="month" />
      <input v-if="mode === 'year'" v-model="selectedYear" type="number" min="2000" max="2100" />
      <button type="submit">Показать</button>
    </form>

    <form class="filters calendar-filters" @submit.prevent="load">
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
        <option value="all">Все источники</option>
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
        <option value="">Все внутренние статусы</option>
        <option value="new">new</option>
        <option value="in_progress">in_progress</option>
        <option value="done">done</option>
        <option value="cancelled">cancelled</option>
        <option value="spam">spam</option>
      </select>
      <input v-model="filters.external_status" placeholder="Внешний статус" />
      <button type="submit">Применить</button>
    </form>

    <div class="stats calendar-summary">
      <div><b>{{ summary.total_count || 0 }}</b><span>Всего обращений</span></div>
      <div><b>{{ summary.rsform_count || 0 }}</b><span>RSForm заявок</span></div>
      <div><b>{{ summary.virtuemart_count || 0 }}</b><span>VirtueMart заказов</span></div>
      <div><b>{{ money(summary.revenue) }}</b><span>Сумма заказов</span></div>
      <div><b>{{ money(summary.average_order_amount) }}</b><span>Средний чек</span></div>
      <div><b>{{ summary.status_counts?.done || 0 }}</b><span>Выполнено</span></div>
      <div><b>{{ summary.status_counts?.in_progress || 0 }}</b><span>В работе</span></div>
      <div><b>{{ summary.status_counts?.cancelled || 0 }}</b><span>Отменено</span></div>
    </div>

    <section v-if="mode === 'day'">
      <div class="page-head compact">
        <h2>{{ formatDate(period.date_from) }}</h2>
      </div>
      <div class="hour-list">
        <article v-for="group in dayGroups" :key="group.hour" class="hour-group">
          <h3>{{ group.hour }}:00</h3>
          <DataTable :columns="dayColumns" :rows="group.orders">
            <template #work_datetime="{ row }">{{ formatTime(row.work_datetime) }}</template>
            <template #source_type="{ row }"><span class="badge">{{ row.source_type }}</span></template>
            <template #identity="{ row }">
              <RouterLink :to="`/orders/${row.id}`">{{ row.source_form_name || row.external_number || row.external_id }}</RouterLink>
            </template>
            <template #amount="{ row }">{{ row.amount ? money(row.amount) : '' }}</template>
            <template #composition="{ row }">
              <div class="composition">
                <div v-for="(item, index) in row.composition.slice(0, 6)" :key="index">
                  <template v-if="row.source_type === 'virtuemart'">
                    {{ item.name }} — {{ item.quantity }} × {{ money(item.price) }} = {{ money(item.total) }}
                  </template>
                  <template v-else>
                    <b>{{ item.label }}:</b> {{ item.value }}
                  </template>
                </div>
                <details v-if="row.source_type === 'rsform' && Object.keys(row.raw_fields || {}).length">
                  <summary>Raw поля</summary>
                  <pre>{{ JSON.stringify(row.raw_fields, null, 2) }}</pre>
                </details>
              </div>
            </template>
            <template #internal_status="{ row }"><StatusBadge :value="row.internal_status" /></template>
          </DataTable>
        </article>
      </div>
    </section>

    <section v-if="mode === 'week'" class="week-grid">
      <article v-for="bucket in buckets" :key="bucket.date" class="period-card" @click="openDay(bucket.date)">
        <h3>{{ bucket.label }}</h3>
        <p><b>{{ bucket.total_count }}</b> всего, RSForm {{ bucket.rsform_count }}, VM {{ bucket.virtuemart_count }}</p>
        <p>{{ money(bucket.revenue) }}</p>
        <ul>
          <li v-for="order in bucket.latest_orders" :key="order.id">{{ order.title }} · {{ order.client_name }}</li>
        </ul>
        <button type="button">Открыть день</button>
      </article>
    </section>

    <section v-if="mode === 'month'" class="month-grid">
      <article v-for="cell in monthCells" :key="cell.key" class="day-cell" :class="{ muted: !cell.inMonth, empty: !cell.total_count }" @click="cell.inMonth && openDay(cell.date)">
        <b>{{ new Date(cell.date).getDate() }}</b>
        <span v-if="cell.total_count">{{ cell.total_count }} обращ.</span>
        <small v-if="cell.total_count">RS {{ cell.rsform_count }} · VM {{ cell.virtuemart_count }}</small>
        <small v-if="cell.revenue">{{ money(cell.revenue) }}</small>
      </article>
    </section>

    <section v-if="mode === 'year'" class="year-grid">
      <article v-for="bucket in buckets" :key="bucket.date" class="period-card" @click="openMonth(bucket.date)">
        <h3>{{ monthName(bucket.date) }}</h3>
        <p><b>{{ bucket.total_count }}</b> всего, RSForm {{ bucket.rsform_count }}, VM {{ bucket.virtuemart_count }}</p>
        <p>{{ money(bucket.revenue) }} · средний {{ money(bucket.average_order_amount) }}</p>
        <ul>
          <li v-for="product in bucket.top_products" :key="`${product.name}-${product.sku}`">{{ product.name }} · {{ product.quantity }}</li>
        </ul>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../api/client'

const modes = [
  { value: 'day', label: 'День' },
  { value: 'week', label: 'Неделя' },
  { value: 'month', label: 'Месяц' },
  { value: 'year', label: 'Год' }
]
const today = new Date().toISOString().slice(0, 10)
const mode = ref('month')
const selectedDate = ref(today)
const selectedMonth = ref(today.slice(0, 7))
const selectedYear = ref(new Date().getFullYear())
const summary = ref({})
const buckets = ref([])
const orders = ref([])
const clients = ref([])
const sites = ref([])
const forms = ref([])
const formKey = ref('')
const period = reactive({ date_from: today, date_to: today })
const filters = reactive({
  search: '',
  client_id: '',
  site_id: '',
  source_type: 'all',
  internal_status: '',
  external_status: ''
})

const dayColumns = [
  { key: 'work_datetime', label: 'Время' },
  { key: 'source_type', label: 'Источник' },
  { key: 'client_name', label: 'Клиент' },
  { key: 'site_name', label: 'Сайт' },
  { key: 'identity', label: 'Форма / номер' },
  { key: 'customer_name', label: 'Имя' },
  { key: 'customer_phone', label: 'Телефон' },
  { key: 'amount', label: 'Сумма' },
  { key: 'internal_status', label: 'Статус' },
  { key: 'composition', label: 'Состав / данные заявки' }
]

const dayGroups = computed(() => {
  const map = new Map()
  for (let hour = 0; hour < 24; hour += 1) map.set(hour, [])
  for (const order of orders.value) {
    const hour = order.work_datetime ? new Date(order.work_datetime).getHours() : 0
    map.get(hour).push(order)
  }
  return [...map.entries()]
    .filter(([, items]) => items.length)
    .map(([hour, items]) => ({ hour: String(hour).padStart(2, '0'), orders: items }))
})

const monthCells = computed(() => {
  if (!period.date_from) return []
  const first = new Date(`${period.date_from}T00:00:00`)
  const start = new Date(first)
  start.setDate(1 - ((first.getDay() + 6) % 7))
  const bucketMap = new Map(buckets.value.map((bucket) => [bucket.date, bucket]))
  const cells = []
  for (let index = 0; index < 42; index += 1) {
    const current = new Date(start)
    current.setDate(start.getDate() + index)
    const iso = current.toISOString().slice(0, 10)
    const bucket = bucketMap.get(iso) || {}
    cells.push({
      key: iso,
      date: iso,
      inMonth: current.getMonth() === first.getMonth(),
      total_count: bucket.total_count || 0,
      rsform_count: bucket.rsform_count || 0,
      virtuemart_count: bucket.virtuemart_count || 0,
      revenue: bucket.revenue || 0
    })
  }
  return cells
})

function dateForMode() {
  if (mode.value === 'month') return `${selectedMonth.value}-01`
  if (mode.value === 'year') return `${selectedYear.value}-01-01`
  return selectedDate.value
}

function queryBase() {
  const params = new URLSearchParams({ mode: mode.value, date: dateForMode() })
  addFilters(params)
  return params
}

function addFilters(params) {
  for (const [key, value] of Object.entries(filters)) {
    if (value && !(key === 'source_type' && value === 'all')) params.set(key, value)
  }
  if (formKey.value) {
    const [siteId, formId] = formKey.value.split(':')
    if (siteId) params.set('site_id', siteId)
    if (formId) params.set('source_form_id', formId)
  }
}

async function load() {
  const params = queryBase()
  summary.value = await api(`/calendar/summary?${params}`)
  const bucketResponse = await api(`/calendar/buckets?${params}`)
  buckets.value = bucketResponse.buckets || []
  period.date_from = summary.value.date_from
  period.date_to = summary.value.date_to
  if (mode.value === 'day') {
    const orderParams = new URLSearchParams({ date_from: period.date_from, date_to: period.date_to })
    addFilters(orderParams)
    orders.value = await api(`/calendar/orders?${orderParams}`)
  } else {
    orders.value = []
  }
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
  forms.value = await api(`/rsform/forms${params.toString() ? `?${params}` : ''}`)
}

function setMode(value) {
  mode.value = value
  load()
}

function openDay(value) {
  selectedDate.value = value
  mode.value = 'day'
  load()
}

function openMonth(value) {
  selectedMonth.value = value.slice(0, 7)
  mode.value = 'month'
  load()
}

async function downloadCsv() {
  const params = new URLSearchParams({ date_from: period.date_from, date_to: period.date_to })
  addFilters(params)
  const response = await fetch(`/api/calendar/export.csv?${params}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('zakaz_token')}` }
  })
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `calendar-${period.date_from}-${period.date_to}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

function money(value) {
  return Number(value || 0).toLocaleString('ru-RU')
}

function formatDate(value) {
  return value ? new Date(`${value}T00:00:00`).toLocaleDateString('ru-RU') : ''
}

function formatTime(value) {
  return value ? new Date(value).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : ''
}

function monthName(value) {
  return new Date(value).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })
}

onMounted(async () => {
  clients.value = await api('/clients')
  sites.value = await api('/sites')
  await load()
})

watch(() => [filters.source_type, filters.client_id, filters.site_id], loadForms)
</script>
