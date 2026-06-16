import api from './api'

export const authService = {
  login: async (credentials) => {
    const { data } = await api.post('/auth/login', credentials)
    return data
  },
  register: async (userData) => {
    const { data } = await api.post('/auth/register', userData)
    return data
  },
  logout: async () => {
    await api.post('/auth/logout')
  },
  refresh: async (refreshToken) => {
    const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return data
  },
  getMe: async () => {
    const { data } = await api.get('/auth/me')
    return data
  },
  updateProfile: async (profileData) => {
    const { data } = await api.put('/auth/profile', profileData)
    return data
  },
  changePassword: async (passwords) => {
    const { data } = await api.put('/auth/password', passwords)
    return data
  },
  forgotPassword: async (email) => {
    const { data } = await api.post('/auth/forgot-password', { email })
    return data
  },
  resetPassword: async (token, newPassword) => {
    const { data } = await api.post('/auth/reset-password', { token, new_password: newPassword })
    return data
  },
}