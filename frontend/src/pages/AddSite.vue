<template>
  <div>
    <div class="page-head">
      <h1>Добавить сайт</h1>
    </div>
    <form class="form-grid" @submit.prevent="submit">
      <label>Клиент
        <select v-model.number="form.client_id" required>
          <option disabled value="">Выберите клиента</option>
          <option v-for="client in clients" :key="client.id" :value="client.id">{{ client.name }}</option>
        </select>
      </label>
      <label>Название сайта<input v-model="form.name" required /></label>
      <label>URL сайта<input v-model="form.url" placeholder="https://site.ru" required /></label>
      <label>Версия Joomla
        <select v-model="form.joomla_version">
          <option value="3">Joomla 3</option>
          <option value="4">Joomla 4</option>
          <option value="5">Joomla 5</option>
        </select>
      </label>
      <fieldset>
        <legend>Источники</legend>
        <label class="check"><input v-model="form.rsform_enabled" type="checkbox" /> RSForm</label>
        <label class="check"><input v-model="form.virtuemart_enabled" type="checkbox" /> VirtueMart</label>
      </fieldset>
      <button type="submit">Создать подключение</button>
    </form>
    <div v-if="created" class="result">
      <h2>Подключение создано</h2>
      <button type="button" @click="downloadConnector(created.id)">Скачать leadhub-connector.php</button>
      <p>Загрузите файл в корень сайта: public_html/leadhub-connector.php</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'

const route = useRoute()
const clients = ref([])
const created = ref(null)
const form = reactive({
  client_id: '',
  name: '',
  url: '',
  joomla_version: '3',
  rsform_enabled: true,
  virtuemart_enabled: true
})

onMounted(async () => {
  clients.value = await api('/clients')
  if (route.query.client_id) {
    form.client_id = Number(route.query.client_id)
  }
})

async function submit() {
  created.value = await api('/sites', { method: 'POST', body: JSON.stringify(form) })
}

async function downloadConnector(id) {
  const response = await fetch(`/api/sites/${id}/connector/download`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('zakaz_token')}` }
  })
  if (!response.ok) {
    alert(await response.text())
    return
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'leadhub-connector.php'
  link.click()
  URL.revokeObjectURL(url)
}
</script>
