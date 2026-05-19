import { useState } from 'react'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useUserStore } from '@/store/user'
import type { FormInstance } from 'antd'
import './LoginPage.css'

const { Title, Text } = Typography

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const navigate = useNavigate()
  const { login } = useUserStore()
  const [form] = Form.useForm()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    setError('') // 清除之前的错误

    try {
      await login(values.username, values.password)
      message.success('登录成功')
      navigate('/')
    } catch (err: any) {
      // 打印错误对象用于调试
      console.log('登录错误:', err)

      // 提取错误信息
      let errorMsg = '用户名或密码错误'
      if (err?.response?.data?.detail) {
        errorMsg = err.response.data.detail
      } else if (err?.message) {
        errorMsg = err.message
      } else if (typeof err === 'string') {
        errorMsg = err
      }

      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <Card className="login-card">
        <div className="login-header">
          <div className="login-icon">🏥</div>
          <Title level={2} style={{ marginBottom: 8 }}>
            CT影像AI分析系统
          </Title>
          <Text type="secondary">基于AI Agent的智能医学影像诊断平台</Text>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
            validateStatus={error ? 'error' : ''}
            help={error || ''}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="login-footer">
          <Text type="secondary">默认账号：admin / admin123</Text>
        </div>
      </Card>
    </div>
  )
}

export default LoginPage
