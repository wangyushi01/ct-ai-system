import { Row, Col, Card, Statistic, Progress, List, Tag, Typography } from 'antd'
import {
  FileTextOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { studyAPI, analysisAPI } from '@/services'
import type { Study, AnalysisTask } from '@/types'

const { Title, Text } = Typography

const DashboardPage: React.FC = () => {
  // 获取检查统计
  const { data: studiesData } = useQuery({
    queryKey: ['studies', 'stats'],
    queryFn: async () => {
      const response: any = await studyAPI.list({ limit: 100 })
      return response
    },
  })

  // 获取分析任务
  const { data: analysisData } = useQuery({
    queryKey: ['analysis', 'recent'],
    queryFn: async () => {
      const response: any = await analysisAPI.list({ limit: 10 })
      return response
    },
  })

  const studies: any = studiesData?.items || []
  const analysisTasks: any = analysisData || []

  // 统计数据
  const stats = {
    total: studies.length,
    completed: studies.filter((s: Study) => s.status === 'completed').length,
    analyzing: studies.filter((s: Study) => s.status === 'analyzing').length,
    pending: studies.filter((s: Study) => s.status === 'pending').length,
  }

  // 最近的检查
  const recentStudies = studies.slice(0, 5)

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'default',
      uploading: 'processing',
      processing: 'blue',
      analyzing: 'cyan',
      completed: 'success',
      reported: 'green',
      failed: 'error',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待处理',
      uploading: '上传中',
      processing: '处理中',
      analyzing: '分析中',
      completed: '已完成',
      reported: '已报告',
      failed: '失败',
    }
    return texts[status] || status
  }

  return (
    <div>
      <Title level={2}>仪表板</Title>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总检查数"
              value={stats.total}
              prefix={<FileTextOutlined />}
              suffix="例"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.completed}
              prefix={<CheckCircleOutlined />}
              suffix="例"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="分析中"
              value={stats.analyzing}
              prefix={<ExperimentOutlined />}
              suffix="例"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待处理"
              value={stats.pending}
              prefix={<ClockCircleOutlined />}
              suffix="例"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 最近检查 */}
        <Col xs={24} lg={14}>
          <Card title="最近检查" extra={<a href="/studies">查看全部</a>}>
            <List
              dataSource={recentStudies}
              renderItem={(item: Study) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{item.study_id}</span>
                        <Tag color={getStatusColor(item.status)}>
                          {getStatusText(item.status)}
                        </Tag>
                      </div>
                    }
                    description={
                      <div>
                        <Text type="secondary">
                          {item.patient?.name} · {item.modality} · {item.body_part}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* 分析任务 */}
        <Col xs={24} lg={10}>
          <Card title="分析任务" extra={<a href="/analysis">查看全部</a>}>
            <List
              dataSource={analysisTasks}
              renderItem={(item: AnalysisTask) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>{item.task_type}</span>
                        <Progress
                          percent={Math.round(item.progress)}
                          size="small"
                          style={{ width: 100 }}
                        />
                      </div>
                    }
                    description={
                      <Text type="secondary">
                        {new Date(item.created_at).toLocaleString()}
                      </Text>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage
