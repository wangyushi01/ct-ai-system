import React from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Dropdown, Avatar, theme, Button } from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useUserStore } from '@/store/user'
import type { MenuProps } from 'antd'
import './MainLayout.css'

const { Header, Sider, Content } = Layout

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = React.useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useUserStore()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const menuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
      onClick: () => navigate('/dashboard'),
    },
    {
      key: '/studies',
      icon: <FileTextOutlined />,
      label: '检查管理',
      onClick: () => navigate('/studies'),
    },
    {
      key: '/analysis',
      icon: <ExperimentOutlined />,
      label: 'AI分析',
      onClick: () => navigate('/analysis'),
    },
    {
      key: '/reports',
      icon: <BarChartOutlined />,
      label: '报告中心',
      onClick: () => navigate('/reports'),
    },
  ]

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout()
        navigate('/login')
      },
    },
  ]

  const getSelectedKey = () => {
    const path = location.pathname
    if (path.startsWith('/studies')) return '/studies'
    if (path.startsWith('/analysis')) return '/analysis'
    if (path.startsWith('/reports')) return '/reports'
    return path
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div className="logo">
          <div className="logo-icon">🏥</div>
          {!collapsed && <div className="logo-text">CT影像AI</div>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200 }}>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              width: 64,
              height: 64,
            }}
          />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div className="user-info">
              <Avatar
                size={32}
                icon={<UserOutlined />}
                src={user?.avatar_url}
                style={{ marginRight: 8 }}
              />
              <span className="user-name">{user?.full_name || user?.username}</span>
            </div>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
