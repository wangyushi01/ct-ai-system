import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User } from '@/types'
import { authAPI } from '@/services'

interface UserState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean

  // Actions
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  updateUser: (user: User) => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true })
        try {
          const response: any = await authAPI.login(username, password)
          const { access_token, refresh_token, user } = response

          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)

          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
      },

      fetchUser: async () => {
        set({ isLoading: true })
        try {
          const user: any = await authAPI.getCurrentUser()
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          // 清除所有认证状态
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
          throw error
        }
      },

      updateUser: (user: User) => {
        set({ user })
      },
    }),
    {
      name: 'user-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
