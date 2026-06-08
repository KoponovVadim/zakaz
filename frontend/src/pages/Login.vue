<template>
  <main class="login-page">
    <form class="login-box" @submit.prevent="submit">
      <h1>Заказы с сайтов</h1>
      <label>Email<input v-model="email" type="email" autocomplete="email" /></label>
      <label>Пароль<input v-model="password" type="password" autocomplete="current-password" /></label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit">Войти</button>
    </form>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const email = ref('admin@example.com')
const password = ref('admin12345')
const error = ref('')
const router = useRouter()
const auth = useAuthStore()

async function submit() {
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.message
  }
}
</script>
