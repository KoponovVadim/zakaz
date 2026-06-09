<template>
  <div>
    <div class="page-head">
      <h1>Заказ {{ order?.external_number || order?.external_id || route.params.id }}</h1>
      <RouterLink class="button" to="/orders">К списку</RouterLink>
    </div>

    <div v-if="order" class="detail-grid">
      <section>
        <h2>Основное</h2>
        <dl class="meta">
          <dt>Источник</dt><dd>{{ order.source_type }}</dd>
          <dt v-if="order.source_type === 'rsform'">Форма</dt><dd v-if="order.source_type === 'rsform'">{{ order.source_form_name || 'Форма не определена' }}</dd>
          <dt>Клиент</dt><dd><RouterLink :to="`/clients/${order.client_id}`">{{ order.client_name || order.client_id }}</RouterLink></dd>
          <dt>Сайт</dt><dd>{{ order.site_name || order.site_id }}</dd>
          <dt>Статус сайта</dt><dd>{{ order.external_status || '-' }}</dd>
          <dt>Внутренний статус</dt>
          <dd>
            <select v-model="status" @change="saveStatus">
              <option value="new">new</option>
              <option value="in_progress">in_progress</option>
              <option value="done">done</option>
              <option value="cancelled">cancelled</option>
            </select>
          </dd>
          <dt>Клиент</dt><dd>{{ order.customer_name || '-' }}</dd>
          <dt>Телефон</dt><dd>{{ order.customer_phone || '-' }}</dd>
          <dt>Email</dt><dd>{{ order.customer_email || '-' }}</dd>
          <dt>Сумма</dt><dd>{{ order.amount ? `${order.amount} ${order.currency || ''}` : '-' }}</dd>
        </dl>
      </section>

      <section>
        <h2>Сообщение</h2>
        <p class="message">{{ order.message || order.title || 'Нет текста' }}</p>
      </section>
    </div>

    <section v-if="order?.items?.length">
      <h2>Товары</h2>
      <DataTable :columns="itemColumns" :rows="order.items" />
    </section>

    <section v-if="order">
      <h2>Комментарии</h2>
      <form class="inline-form" @submit.prevent="addComment">
        <input v-model="commentText" placeholder="Комментарий" />
        <button type="submit">Добавить</button>
      </form>
      <div class="notes">
        <article v-for="comment in order.comments" :key="comment.id">
          <time>{{ formatDate(comment.created_at) }}</time>
          <p>{{ comment.text }}</p>
        </article>
      </div>
    </section>

    <section v-if="order?.status_history?.length">
      <h2>История статусов</h2>
      <div class="notes">
        <article v-for="item in order.status_history" :key="item.id">
          <time>{{ formatDate(item.created_at) }}</time>
          <p>{{ item.old_status || '-' }} → {{ item.new_status }}</p>
        </article>
      </div>
    </section>

    <section v-if="order">
      <h2>Raw payload</h2>
      <pre>{{ JSON.stringify(order.raw_payload, null, 2) }}</pre>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from '../components/DataTable.vue'
import { api } from '../api/client'

const route = useRoute()
const order = ref(null)
const status = ref('new')
const commentText = ref('')
const itemColumns = [
  { key: 'sku', label: 'SKU' },
  { key: 'name', label: 'Название' },
  { key: 'quantity', label: 'Кол-во' },
  { key: 'price', label: 'Цена' }
]

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : ''
}

async function load() {
  order.value = await api(`/orders/${route.params.id}`)
  status.value = order.value.internal_status
}

async function saveStatus() {
  order.value = await api(`/orders/${route.params.id}/status`, {
    method: 'PUT',
    body: JSON.stringify({ internal_status: status.value })
  })
  await load()
}

async function addComment() {
  if (!commentText.value.trim()) return
  await api(`/orders/${route.params.id}/comments`, {
    method: 'POST',
    body: JSON.stringify({ text: commentText.value })
  })
  commentText.value = ''
  await load()
}

onMounted(load)
</script>
