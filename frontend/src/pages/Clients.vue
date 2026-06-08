<template>
  <div>
    <div class="page-head">
      <h1>Клиенты</h1>
      <form class="inline-form" @submit.prevent="create">
        <input v-model="name" placeholder="Новый клиент" />
        <button type="submit"><Plus :size="18" /> Добавить</button>
      </form>
    </div>
    <DataTable :columns="columns" :rows="clients">
      <template #name="{ row }"><RouterLink :to="`/clients/${row.id}`">{{ row.name }}</RouterLink></template>
    </DataTable>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Plus } from 'lucide-vue-next'
import DataTable from '../components/DataTable.vue'
import { api } from '../api/client'

const clients = ref([])
const name = ref('')
const columns = [
  { key: 'name', label: 'Название' },
  { key: 'sites_count', label: 'Сайты' },
  { key: 'orders_count', label: 'Заказы' },
  { key: 'comment', label: 'Комментарий' }
]

async function load() {
  clients.value = await api('/clients')
}

async function create() {
  if (!name.value.trim()) return
  await api('/clients', { method: 'POST', body: JSON.stringify({ name: name.value, comment: '' }) })
  name.value = ''
  await load()
}

onMounted(load)
</script>
