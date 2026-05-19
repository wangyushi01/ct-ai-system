import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App'
import './index.css'

dayjs.locale('zh-cn')

// 创建QueryClient实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider
          locale={zhCN}
          theme={{
            algorithm: theme.defaultAlgorithm,
            token: {
              colorPrimary: '#1890ff',
              borderRadius: 6,
            },
          }}
        >
          <App />
        </ConfigProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
