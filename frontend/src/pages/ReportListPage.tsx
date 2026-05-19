import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Table,
  Card,
  Typography,
  Tag,
  Space,
  Select,
  Button,
  Popconfirm,
  message,
} from 'antd'
import { DeleteOutlined } from '@ant-design/icons'
import { reportAPI } from '@/services'

const { Title } = Typography

const ReportListPage: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)

  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['reports', statusFilter],
    queryFn: async () => {
      const response: any = await reportAPI.list({ status: statusFilter })
      return response
    },
  })

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'default',
      reviewing: 'processing',
      reviewed: 'blue',
      signed: 'success',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      draft: '草稿',
      reviewing: '审核中',
      reviewed: '已审核',
      signed: '已签发',
    }
    return texts[status] || status
  }

  const deleteMutation = useMutation({
    mutationFn: (reportId: string) => reportAPI.delete(reportId),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '删除失败')
    },
  })

  const columns = [
    {
      title: '报告ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      ellipsis: true,
      render: (id: string) => id.substring(0, 8) + '...',
    },
    {
      title: '报告类型',
      dataIndex: 'report_type',
      key: 'report_type',
      width: 120,
    },
    {
      title: '影像发现',
      dataIndex: 'findings',
      key: 'findings',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: 'AI生成',
      dataIndex: 'ai_generated',
      key: 'ai_generated',
      width: 80,
      render: (ai: boolean) => ai ? <Tag color="blue">AI</Tag> : <Tag>手动</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => {
              navigate(`/studies/${record.study_id}/report`)
            }}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这个报告吗？"
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
        <Title level={2}>报告中心</Title>
      </div>

      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Select
            placeholder="选择状态"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => setStatusFilter(value)}
          >
            <Select.Option value="draft">草稿</Select.Option>
            <Select.Option value="reviewed">已审核</Select.Option>
            <Select.Option value="signed">已签发</Select.Option>
          </Select>
        </Space>

        <Table
          columns={columns}
          dataSource={reportsData?.items || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 800 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            total: reportsData?.total || 0,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  )
}

export default ReportListPage
