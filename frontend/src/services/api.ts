import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { AxiosInstance } from 'axios'
import { message } from 'antd'
import { useUserStore } from '@/store/user'

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: any) => {
    // 204 No Content响应返回空对象
    if (response.status === 204) {
      return { success: true }
    }
    return response.data
  },
  (error: AxiosError) => {
    console.log('API拦截器捕获错误:', error)
    console.log('错误状态:', error.response?.status)
    console.log('错误数据:', error.response?.data)
    console.log('请求URL:', error.config?.url)

    if (error.response) {
      const status = error.response.status
      const data: any = error.response.data
      const isLoginRequest = error.config?.url?.includes('auth/login')

      console.log('是否为登录请求:', isLoginRequest)

      switch (status) {
        case 401:
          // 登录请求不自动跳转，让页面处理错误提示
          if (!isLoginRequest) {
            message.error('登录已过期，请重新登录')
            // 使用 zustand store 的 logout 方法清除所有状态
            useUserStore.getState().logout()
            window.location.href = '/login'
          }
          break
        case 403:
          message.error('权限不足')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 500:
          message.error('服务器错误')
          break
        default:
          if (!isLoginRequest) {
            message.error(data?.detail || '请求失败')
          }
      }
    } else if (error.request) {
      message.error('网络错误，请检查网络连接')
    } else {
      message.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

export default api
