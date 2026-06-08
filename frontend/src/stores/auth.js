import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('zakaz_token') || '',
    user: null
  }),
  actions: {
    async login(email, password) {
      const data = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      })
      this.token = data.access_token
      localStorage.setItem('zakaz_token', this.token)
      await this.loadMe()
    },
    async loadMe() {
      if (!this.token) return
      this.user = await api('/auth/me')
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('zakaz_token')
    }
  }
})
