import { useState } from 'react'
import {
  Table,
  Card,
  Button,
  Space,
  Tag,
  Typography,
  Input,
  Select,
  Modal,
  Form,
  Popconfirm,
  message,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EyeOutlined,
  DeleteOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { studyAPI } from '@/services'
import type { Study } from '@/types'

const { Title } = Typography

const StudyListPage: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<any>({})
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 })
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()

  // 获取检查列表
  const { data: studiesData, isLoading } = useQuery({
    queryKey: ['studies', filters, pagination],
    queryFn: async () => {
      const response: any = await studyAPI.list({
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        ...filters,
      })
      return response
    },
  })

  // 删除检查
  const deleteMutation = useMutation({
    mutationFn: async (studyId: string) => {
      await studyAPI.delete(studyId)
    },
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['studies'] })
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || error?.message || '删除失败'
      message.error(errorMsg)
    },
  })

  const getStatusColor = (status: any) => {
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

  const getStatusText = (status: any) => {
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

  const columns = [
    {
      title: '检查号',
      dataIndex: 'study_id',
      key: 'study_id',
      width: 150,
    },
    {
      title: '患者',
      dataIndex: ['patient', 'name'],
      key: 'patient',
      width: 100,
    },
    {
      title: '类型',
      dataIndex: 'modality',
      key: 'modality',
      width: 80,
    },
    {
      title: '部位',
      dataIndex: 'body_part',
      key: 'body_part',
      width: 100,
    },
    {
      title: '检查日期',
      dataIndex: 'study_date',
      key: 'study_date',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: any) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '影像数',
      dataIndex: 'images_count',
      key: 'images_count',
      width: 80,
      align: 'right' as const,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: Study) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/studies/${record.study_id}`)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<ExperimentOutlined />}
            onClick={() => navigate(`/studies/${record.study_id}/analysis`)}
          >
            分析
          </Button>
          <Popconfirm
            title="确定要删除这个检查吗？"
            onConfirm={() => deleteMutation.mutate(record.study_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const handleCreateStudy = async (values: any) => {
    try {
      // 构建创建检查的数据
      const studyData = {
        study_id: values.study_id,
        patient_id: values.patient_id,
        patient_name: values.patient_name,
        gender: values.gender,
        birth_date: values.birth_date,
        phone: values.phone,
        modality: values.modality,
        body_part: values.body_part,
        study_description: values.study_description,
        study_date: dayjs().toISOString(),
      }

      await studyAPI.create(studyData)
      message.success('创建成功')
      setCreateModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['studies'] })
    } catch (error: any) {
      console.error('创建失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '创建失败'
      message.error(errorMsg)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>检查管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
          新建检查
        </Button>
      </div>

      <Card>
        {/* 筛选条件 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            placeholder="搜索检查号或患者"
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
            onChange={(e) => setFilters({ ...filters, keyword: e.target.value || undefined })}
            allowClear
          />
          <Select
            placeholder="选择类型"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, modality: value })}
          >
            <Select.Option value="CT">CT</Select.Option>
            <Select.Option value="MR">MR</Select.Option>
            <Select.Option value="US">US</Select.Option>
          </Select>
          <Select
            placeholder="选择部位"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, body_part: value })}
          >
            <Select.Option value="CHEST">胸部</Select.Option>
            <Select.Option value="HEAD">头部</Select.Option>
            <Select.Option value="ABDOMEN">腹部</Select.Option>
          </Select>
          <Select
            placeholder="选择状态"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, status: value })}
          >
            <Select.Option value="pending">待处理</Select.Option>
            <Select.Option value="processing">处理中</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
          </Select>
        </Space>

        {/* 表格 */}
        <Table
          columns={columns}
          dataSource={studiesData?.items || []}
          loading={isLoading}
          rowKey="study_id"
          scroll={{ x: 1200 }}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: studiesData?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) =>
              setPagination({ current: page, pageSize }),
          }}
        />
      </Card>

      {/* 创建检查弹窗 */}
      <Modal
        title="新建检查"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateStudy}>
          <Form.Item
            name="study_id"
            label="检查号"
            rules={[{ required: true, message: '请输入检查号' }]}
          >
            <Input placeholder="例如：ST2024001" />
          </Form.Item>

          {/* 患者基本信息 */}
          <Card size="small" title="患者信息" style={{ marginBottom: 16 }}>
            <Form.Item
              name="patient_name"
              label="患者姓名"
              rules={[{ required: true, message: '请输入患者姓名' }]}
            >
              <Input placeholder="请输入患者姓名" />
            </Form.Item>
            <Form.Item
              name="patient_id"
              label="患者ID"
              rules={[{ required: true, message: '请输入患者ID' }]}
            >
              <Input placeholder="例如：P2024001" />
            </Form.Item>
            <Form.Item
              name="gender"
              label="性别"
              rules={[{ required: true, message: '请选择性别' }]}
            >
              <Select placeholder="请选择性别">
                <Select.Option value="男">男</Select.Option>
                <Select.Option value="女">女</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="birth_date"
              label="出生日期"
              rules={[{ required: true, message: '请选择出生日期' }]}
            >
              <Input type="date" />
            </Form.Item>
            <Form.Item name="phone" label="联系电话">
              <Input placeholder="请输入联系电话" />
            </Form.Item>
          </Card>

          {/* 检查信息 */}
          <Card size="small" title="检查信息" style={{ marginBottom: 16 }}>
            <Form.Item
              name="modality"
              label="检查类型"
              rules={[{ required: true, message: '请选择检查类型' }]}
            >
              <Select placeholder="请选择检查类型">
                <Select.Option value="CT">CT</Select.Option>
                <Select.Option value="MR">MR</Select.Option>
                <Select.Option value="US">US</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="body_part"
              label="检查部位"
              rules={[{ required: true, message: '请选择检查部位' }]}
            >
              <Select placeholder="请选择检查部位">
                <Select.Option value="CHEST">胸部</Select.Option>
                <Select.Option value="HEAD">头部</Select.Option>
                <Select.Option value="ABDOMEN">腹部</Select.Option>
                <Select.Option value="PELVIS">盆腔</Select.Option>
                <Select.Option value="SPINE">脊柱</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="study_description"
              label="检查描述"
            >
              <Input.TextArea rows={2} placeholder="请输入检查描述" />
            </Form.Item>
          </Card>
        </Form>
      </Modal>
    </div>
  )
}

export default StudyListPage
