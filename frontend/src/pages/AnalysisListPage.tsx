import { useState } from 'react'
import {
  Table,
  Card,
  Tag,
  Button,
  Space,
  Select,
  Typography,
  Progress,
  Popconfirm,
  message,
} from 'antd'
import { EyeOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { analysisAPI } from '@/services'
import type { AnalysisTask } from '@/types'
import { TaskStatus } from '@/types'
import dayjs from 'dayjs'

const { Title } = Typography

const AnalysisListPage: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<any>({})
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })

  const { data: tasks, isLoading, refetch } = useQuery({
    queryKey: ['analysis', 'list', filters, pagination],
    queryFn: async () => {
      const response: any = await analysisAPI.list({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        status: filters.status,
      })
      return response
    },
  })

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      queued: 'default',
      running: 'processing',
      completed: 'success',
      failed: 'error',
      cancelled: 'default',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      queued: '队列中',
      running: '运行中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消',
    }
    return texts[status] || status
  }

  const getTaskTypeName = (type: string) => {
    const names: Record<string, string> = {
      lung_nodule: '肺结节检测',
      pneumonia: '肺炎检测',
      brain_hemorrhage: '脑出血检测',
      liver_lesion: '肝脏病变检测',
    }
    return names[type] || type
  }

  const deleteMutation = useMutation({
    mutationFn: (taskId: string) => analysisAPI.delete(taskId),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['analysis'] })
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '删除失败')
    },
  })

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: string) => (
        <Typography.Text copyable ellipsis style={{ width: 80 }}>
          {id.slice(0, 8)}...
        </Typography.Text>
      ),
    },
    {
      title: '检查ID',
      dataIndex: 'study_id',
      key: 'study_id',
      width: 100,
      render: (studyId: string) => (
        <Typography.Text ellipsis style={{ width: 80 }}>
          {studyId.slice(0, 8)}...
        </Typography.Text>
      ),
    },
    {
      title: '分析类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      render: (type: string) => getTaskTypeName(type),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TaskStatus) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: AnalysisTask) => (
        <Progress
          percent={Math.round(progress)}
          size="small"
          status={record.status === 'failed' ? 'exception' : undefined}
        />
      ),
    },
    {
      title: '检测数量',
      dataIndex: 'detections',
      key: 'detections',
      width: 100,
      render: (detections: any[]) => detections.length,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: AnalysisTask) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/studies/${record.study_id}/analysis`)}
            disabled={record.status !== 'completed'}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这个分析任务吗？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>AI 分析</Title>
        <Space>
          <Select
            placeholder="选择状态"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, status: value || undefined })}
          >
            <Select.Option value="queued">队列中</Select.Option>
            <Select.Option value="running">运行中</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
            <Select.Option value="failed">失败</Select.Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={tasks || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1000 }}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: tasks?.length || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
          }}
        />
      </Card>
    </div>
  )
}

export default AnalysisListPage
