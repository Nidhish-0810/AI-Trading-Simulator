import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { authService } from '../services/auth.service'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setAccessToken: (token) => set({ accessToken: token }),

      login: async (credentials) => {
        set({ isLoading: true, error: null })
        try {
          const data = await authService.login(credentials)
          set({
            user: data.user,
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          return { success: true }
        } catch (err) {
          const message = err.response?.data?.detail || 'Login failed. Please try again.'
          set({ isLoading: false, error: message, isAuthenticated: false })
          return { success: false, message }
        }
      },

      register: async (userData) => {
        set({ isLoading: true, error: null })
        try {
          const data = await authService.register(userData)
          set({
            user: data.user,
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          return { success: true }
        } catch (err) {
          const message = err.response?.data?.detail || 'Registration failed. Please try again.'
          set({ isLoading: false, error: message, isAuthenticated: false })
          return { success: false, message }
        }
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        })
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get()
        if (!refreshToken) {
          get().logout()
          return false
        }
        try {
          const data = await authService.refresh(refreshToken)
          set({ accessToken: data.access_token })
          return true
        } catch {
          get().logout()
          return false
        }
      },

      updateProfile: async (profileData) => {
        set({ isLoading: true })
        try {
          const updated = await authService.updateProfile(profileData)
          set((state) => ({
            user: { ...state.user, ...updated },
            isLoading: false,
          }))
          return { success: true }
        } catch (err) {
          const message = err.response?.data?.detail || 'Profile update failed.'
          set({ isLoading: false, error: message })
          return { success: false, message }
        }
      },

      clearError: () => set({ error: null }),

      // Demo login for quick access
      demoLogin: () => {
        set({
          user: {
            id: 'demo-1',
            username: 'TraderPro',
            email: 'demo@tradeai.com',
            avatar: null,
            created_at: new Date().toISOString(),
            portfolio_value: 125420.50,
            starting_capital: 100000,
          },
          accessToken: 'demo-token',
          refreshToken: 'demo-refresh',
          isAuthenticated: true,
          isLoading: false,
        })
      },
    }),
    {
      name: 'tradeai-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
