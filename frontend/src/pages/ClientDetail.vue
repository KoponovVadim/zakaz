<template>
  <div>
    <div class="page-head">
      <h1>{{ client?.name || 'Клиент' }}</h1>
      <RouterLink class="button" to="/sites/add">Добавить сайт</RouterLink>
    </div>
    <p class="muted">{{ client?.comment }}</p>

    <div class="stats">
      <div><b>{{ client?.sites_count || 0 }}</b><span>Сайты</span></div>
      <div><b>{{ client?.orders_count || 0 }}</b><span>Заказы</span></div>
    </div>

    <section>
      <h2>Сайты клиента</h2>
      <DataTable :columns="siteColumns" :rows="sites">
        <template #status="{ row }"><SiteStatusBadge :value="row.status" /></template>
      </DataTable>
    </section>

    <section>
      <div class="page-head compact">
        <h2>Последние заказы</h2>
        <RouterLink :to="`/orders?client_id=${route.params.id}`">Все заказы клиента</RouterLink>
      </div>
      <DataTable :columns="orderColumns" :rows="orders">
        <template #external_number="{ row }">
          <RouterLink :to="`/orders/${row.id}`">{{ row.external_number || row.id }}</RouterLink>
        </template>
        <template #internal_status="{ row }"><StatusBadge :value="row.internal_status" /></template>
      </DataTable>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from '../components/DataTable.vue'
import SiteStatusBadge from '../components/SiteStatusBadge.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../api/client'

const route = useRoute()
const client = ref(null)
const sites = ref([])
const orders = ref([])
const siteColumns = [
  { key: 'name', label: 'Сайт' },
  { key: 'url', label: 'URL' },
  { key: 'joomla_version', label: 'Joomla' },
  { key: 'status', label: 'Статус' }
]
const orderColumns = [
  { key: 'external_number', label: 'Номер' },
  { key: 'site_name', label: 'Сайт' },
  { key: 'customer_name', label: 'Покупатель' },
  { key: 'customer_phone', label: 'Телефон' },
  { key: 'internal_status', label: 'Статус' }
]

onMounted(async () => {
  client.value = await api(`/clients/${route.params.id}`)
  sites.value = await api(`/sites?client_id=${route.params.id}`)
  orders.value = await api(`/orders?client_id=${route.params.id}&limit=10`)
})
</script>
