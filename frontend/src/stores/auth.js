import { defineStore } from 'pinia'
import request from '@/api/request'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: sessionStorage.getItem('token') || '',
    username: sessionStorage.getItem('username') || '',
    role: sessionStorage.getItem('role') || '',
    userId: Number(sessionStorage.getItem('userId') || 0),
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
  },

  actions: {
    async login(username, password) {
      const res = await request.post('/auth/login', { username, password })
      if (res.access_token) {
        this.token = res.access_token
        this.username = res.user.username
        const roleMap = { 'ADMIN': 'admin', 'DATA_MANAGER': 'data_manager', 'FARMER': 'farmer' }
        const role = roleMap[res.user.role] || res.user.role.toLowerCase()
        this.role = role
        this.userId = res.user.id
        sessionStorage.setItem('token', res.access_token)
        sessionStorage.setItem('username', res.user.username)
        sessionStorage.setItem('role', role)
        sessionStorage.setItem('userId', String(res.user.id))
      }
      return res
    },

    logout() {
      this.token = ''
      this.username = ''
      this.role = ''
      this.userId = 0
      sessionStorage.clear()
    },

    async fetchMe() {
      try {
        const res = await request.get('/auth/me')
        this.username = res.username
        const roleMap = { 'ADMIN': 'admin', 'DATA_MANAGER': 'data_manager', 'FARMER': 'farmer' }
        const role = roleMap[res.role] || res.role.toLowerCase()
        this.role = role
        this.userId = res.id
        sessionStorage.setItem('username', res.username)
        sessionStorage.setItem('role', role)
        sessionStorage.setItem('userId', String(res.id))
      } catch {
        this.logout()
      }
    },

    async checkAuth() {
      if (!this.token) return
      await this.fetchMe()
    },
  },
})
