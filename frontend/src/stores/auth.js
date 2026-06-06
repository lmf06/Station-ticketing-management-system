import { defineStore } from 'pinia'
import { api } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    role: (state) => state.user?.role || '',
  },
  actions: {
    async fetchMe() {
      const { data } = await api.get('/auth/me')
      this.user = data.user
    },
    async login(payload) {
      const { data } = await api.post('/auth/login', payload)
      this.user = data.user
    },
    async register(payload) {
      const { data } = await api.post('/auth/register', payload)
      this.user = data.user
    },
    async logout() {
      await api.post('/auth/logout')
      this.user = null
    },
  },
})
