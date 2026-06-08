import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AdminLayout from './layouts/AdminLayout.vue'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import Clients from './pages/Clients.vue'
import ClientDetail from './pages/ClientDetail.vue'
import Sites from './pages/Sites.vue'
import AddSite from './pages/AddSite.vue'
import Orders from './pages/Orders.vue'
import OrderDetail from './pages/OrderDetail.vue'
import DirectAnalytics from './pages/DirectAnalytics.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    {
      path: '/',
      component: AdminLayout,
      meta: { auth: true },
      children: [
        { path: '', component: Dashboard },
        { path: 'clients', component: Clients },
        { path: 'clients/:id', component: ClientDetail },
        { path: 'sites', component: Sites },
        { path: 'sites/add', component: AddSite },
        { path: 'orders', component: Orders },
        { path: 'orders/:id', component: OrderDetail },
        { path: 'analytics/direct', component: DirectAnalytics }
      ]
    }
  ]
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.token) return '/login'
})

export default router
