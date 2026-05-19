import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useUserStore } from './store/user'
import { Spin } from 'antd'
import MainLayout from './components/layout/MainLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import StudyListPage from './pages/StudyListPage'
import StudyDetailPage from './pages/StudyDetailPage'
import AnalysisPage from './pages/AnalysisPage'
import AnalysisListPage from './pages/AnalysisListPage'
import ReportPage from './pages/ReportPage'
import ReportListPage from './pages/ReportListPage'

function App() {
  const { isAuthenticated, isLoading, fetchUser } = useUserStore()
  const [isInitialized, setIsInitialized] = React.useState(false)

  // 应用启动时，如果有token，必须验证其有效性
  React.useEffect(() => {
    // 开发环境：清除旧的认证状态，避免重定向循环
    if (import.meta.env.DEV) {
      const token = localStorage.getItem('access_token')
      if (token) {
        // 有 token 时才尝试验证，否则清除所有状态
        fetchUser().finally(() => {
          setIsInitialized(true)
        })
      } else {
        // 无 token 时清除 persist 数据
        localStorage.removeItem('user-storage')
        setIsInitialized(true)
      }
    } else {
      // 生产环境：保持原有逻辑
      const token = localStorage.getItem('access_token')
      const persistedAuth = localStorage.getItem('user-storage')
      if (token || persistedAuth) {
        fetchUser().finally(() => {
          setIsInitialized(true)
        })
      } else {
        setIsInitialized(true)
      }
    }
  }, [fetchUser])

  // 初始化验证完成前显示loading
  if (!isInitialized || isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <Routes>
      {/* 公开路由 */}
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/" replace />
          ) : (
            <LoginPage />
          )
        }
      />

      {/* 受保护路由 */}
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <MainLayout />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      >
        <Route path="" element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="studies" element={<StudyListPage />} />
        <Route path="studies/:studyId" element={<StudyDetailPage />} />
        <Route path="studies/:studyId/analysis" element={<AnalysisPage />} />
        <Route path="studies/:studyId/report" element={<ReportPage />} />
        <Route path="analysis" element={<AnalysisListPage />} />
        <Route path="reports" element={<ReportListPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}

export default App
