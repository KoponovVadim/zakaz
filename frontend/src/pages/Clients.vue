<template>
  <div>
    <div class="page-head">
      <h1>Клиенты</h1>
      <form class="inline-form" @submit.prevent="create">
        <input v-model="name" placeholder="Новый клиент" />
        <button type="submit" :disabled="saving"><Plus :size="18" /> {{ saving ? 'Добавляем' : 'Добавить' }}</button>
      </form>
    </div>
    <p v-if="message" class="notice">{{ message }}</p>
    <p v-if="error" class="error">Ошибка: {{ error }}</p>
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
const saving = ref(false)
const message = ref('')
const error = ref('')
const columns = [
  { key: 'name', label: 'Название' },
  { key: 'sites_count', label: 'Сайты' },
  { key: 'orders_count', label: 'Заказы' },
  { key: 'comment', label: 'Комментарий' }
]

async function load() {
  try {
    clients.value = await api('/clients')
    error.value = ''
  } catch (err) {
    error.value = err.message
  }
}

async function create() {
  if (!name.value.trim()) return
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    await api('/clients', { method: 'POST', body: JSON.stringify({ name: name.value.trim(), comment: '' }) })
    message.value = 'Клиент добавлен'
    name.value = ''
    await load()
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
