<template>
  <div>
    <div class="page-head">
      <h1>Дашборд</h1>
    </div>
    <div class="stats">
      <div><b>{{ summary.clients }}</b><span>Клиенты</span></div>
      <div><b>{{ summary.sites }}</b><span>Сайты</span></div>
      <div><b>{{ summary.active_sites }}</b><span>Активные</span></div>
      <div><b>{{ summary.orders }}</b><span>Заявки</span></div>
      <div><b>{{ summary.new_orders }}</b><span>Новые</span></div>
    </div>

    <section>
      <div class="page-head compact">
        <h2>Последние заказы</h2>
        <RouterLink to="/orders">Все заказы</RouterLink>
      </div>
      <DataTable :columns="columns" :rows="orders">
        <template #external_number="{ row }">
          <RouterLink :to="`/orders/${row.id}`">{{ row.external_number || row.id }}</RouterLink>
        </template>
        <template #amount="{ row }">
          {{ row.amount ? `${row.amount} ${row.currency || ''}` : '' }}
        </template>
        <template #internal_status="{ row }">
          <StatusBadge :value="row.internal_status" />
        </template>
      </DataTable>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../api/client'

const summary = ref({ clients: 0, sites: 0, active_sites: 0, orders: 0, new_orders: 0 })
const orders = ref([])
const columns = [
  { key: 'external_number', label: 'Номер' },
  { key: 'client_name', label: 'Клиент' },
  { key: 'site_name', label: 'Сайт' },
  { key: 'customer_name', label: 'Покупатель' },
  { key: 'amount', label: 'Сумма' },
  { key: 'internal_status', label: 'Статус' }
]

onMounted(async () => {
  summary.value = await api('/dashboard/summary')
  orders.value = await api('/dashboard/recent-orders')
})
</script>
