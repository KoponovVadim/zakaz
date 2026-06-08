<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">Zakaz</div>
      <nav>
        <RouterLink to="/">Дашборд</RouterLink>
        <RouterLink to="/clients">Клиенты</RouterLink>
        <RouterLink to="/sites">Сайты</RouterLink>
        <RouterLink to="/orders">Заказы</RouterLink>
      </nav>
    </aside>
    <main>
      <header class="topbar">
        <span>{{ auth.user?.email || 'Администратор' }}</span>
        <button class="ghost" @click="logout"><LogOut :size="18" /> Выйти</button>
      </header>
      <section class="content">
        <RouterView />
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { LogOut } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => auth.loadMe())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
