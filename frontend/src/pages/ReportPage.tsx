import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Card,
  Button,
  Space,
  Typography,
  Descriptions,
  Tag,
  Spin,
  Empty,
  Alert,
  Modal,
  Form,
  Input,
  message,
  Row,
  Col,
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  CheckCircleOutlined,
  RobotOutlined,
  PrinterOutlined,
} from '@ant-design/icons'
import { useState } from 'react'
import { studyAPI, reportAPI } from '@/services'

const { Title, Paragraph } = Typography
const { TextArea } = Input

const ReportPage: React.FC = () => {
  const { studyId } = useParams<{ studyId: string }>()
  const navigate = useNavigate()
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [form] = Form.useForm()

  // 获取检查信息
  const { data: study, isLoading: studyLoading } = useQuery({
    queryKey: ['study', studyId],
    queryFn: async () => {
      const response: any = await studyAPI.get(studyId!)
      return response
    },
    enabled: !!studyId,
  })

  // 获取报告（404表示暂无报告，不报错）
  const { data: report, isLoading: reportLoading, refetch } = useQuery({
    queryKey: ['report', studyId],
    queryFn: async () => {
      try {
        const response: any = await reportAPI.getByStudy(studyId!)
        return response
      } catch (error: any) {
        if (error?.response?.status === 404) {
          return null
        }
        throw error
      }
    },
    enabled: !!studyId,
  })

  // AI生成报告
  const generateMutation = useMutation({
    mutationFn: () => reportAPI.aiGenerate(studyId!),
    onSuccess: () => {
      message.success('AI报告生成成功')
      refetch()
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || error?.message || '生成失败'
      message.error(errorMsg)
    },
  })

  // 更新报告
  const updateMutation = useMutation({
    mutationFn: (data: any) => reportAPI.update(report!.id, data),
    onSuccess: () => {
      message.success('更新成功')
      setEditModalOpen(false)
      refetch()
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || error?.message || '更新失败'
      message.error(errorMsg)
    },
  })

  // 签发报告
  const signMutation = useMutation({
    mutationFn: () => reportAPI.sign(report!.id),
    onSuccess: () => {
      message.success('签发成功')
      refetch()
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || error?.message || '签发失败'
      message.error(errorMsg)
    },
  })

  const handleEdit = () => {
    if (report) {
      form.setFieldsValue({
        findings: report.findings,
        impression: report.impression,
        recommendation: report.recommendation,
        clinical_history: report.clinical_history,
      })
    }
    setEditModalOpen(true)
  }

  const handleEditSubmit = (values: any) => {
    updateMutation.mutate(values)
  }

  const handleSign = () => {
    if (!report) return

    Modal.confirm({
      title: '确认签发报告',
      content: '签发后报告将无法修改，确认要签发吗？',
      onOk: () => {
        signMutation.mutate()
      },
    })
  }

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

  if (studyLoading || reportLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!study) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Empty description="检查不存在" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/studies/${studyId}`)}>
            返回
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            诊断报告 - {study.study_id}
          </Title>
          {report && (
            <Tag color={getStatusColor(report.status)}>
              {getStatusText(report.status)}
            </Tag>
          )}
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* 左侧：患者和检查信息 */}
        <Col xs={24} lg={8}>
          <Card title="患者信息">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="患者姓名">
                {study.patient?.name || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="患者ID">
                {study.patient?.patient_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="性别">
                {study.patient?.gender || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="出生日期">
                {study.patient?.birth_date || '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="检查信息" style={{ marginTop: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="检查号">{study.study_id}</Descriptions.Item>
              <Descriptions.Item label="检查类型">{study.modality}</Descriptions.Item>
              <Descriptions.Item label="检查部位">{study.body_part}</Descriptions.Item>
              <Descriptions.Item label="检查日期">{study.study_date}</Descriptions.Item>
              <Descriptions.Item label="影像数量">{study.images_count} 张</Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 操作按钮 */}
          <Card title="操作" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {!report ? (
                <Button
                  type="primary"
                  icon={<RobotOutlined />}
                  block
                  onClick={() => generateMutation.mutate()}
                  loading={generateMutation.isPending}
                >
                  AI生成报告
                </Button>
              ) : (
                <>
                  <Button
                    icon={<EditOutlined />}
                    block
                    onClick={handleEdit}
                    disabled={report.status === 'signed'}
                  >
                    编辑报告
                  </Button>
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    block
                    onClick={handleSign}
                    disabled={report.status === 'signed'}
                  >
                    签发报告
                  </Button>
                  <Button
                    icon={<PrinterOutlined />}
                    block
                    onClick={() => window.print()}
                  >
                    打印报告
                  </Button>
                </>
              )}
            </Space>
          </Card>
        </Col>

        {/* 右侧：报告内容 */}
        <Col xs={24} lg={16}>
          {!report ? (
            <Card>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无报告"
              >
                {study.status === 'completed' && (
                  <Button
                    type="primary"
                    icon={<RobotOutlined />}
                    onClick={() => generateMutation.mutate()}
                    loading={generateMutation.isPending}
                  >
                    使用AI生成报告
                  </Button>
                )}
              </Empty>
            </Card>
          ) : (
            <Card
              title="报告内容"
              extra={
                report.ai_generated && (
                  <Tag icon={<RobotOutlined />} color="blue">
                    AI生成
                  </Tag>
                )
              }
            >
              {report.ai_generated && (
                <Alert
                  message="AI辅助诊断"
                  description="本报告由AI系统自动生成，仅供医生参考，请结合临床情况综合判断。"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Descriptions column={1} bordered>
                <Descriptions.Item label="临床病史">
                  <Paragraph style={{ marginBottom: 0 }}>
                    {report.clinical_history || '无'}
                  </Paragraph>
                </Descriptions.Item>

                <Descriptions.Item label="影像发现">
                  <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                    {report.findings}
                  </Paragraph>
                </Descriptions.Item>

                <Descriptions.Item label="诊断意见">
                  <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                    {report.impression}
                  </Paragraph>
                </Descriptions.Item>

                <Descriptions.Item label="建议">
                  <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                    {report.recommendation || '无特殊建议'}
                  </Paragraph>
                </Descriptions.Item>

                {report.review_comment && (
                  <Descriptions.Item label="审核意见">
                    <Paragraph style={{ marginBottom: 0 }}>
                      {report.review_comment}
                    </Paragraph>
                  </Descriptions.Item>
                )}

                <Descriptions.Item label="报告日期">
                  {report.report_date || '-'}
                </Descriptions.Item>

                {report.signed_at && (
                  <Descriptions.Item label="签发时间">
                    {report.signed_at}
                  </Descriptions.Item>
                )}

                {report.ai_confidence && (
                  <Descriptions.Item label="AI置信度">
                    {(report.ai_confidence * 100).toFixed(1)}%
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          )}
        </Col>
      </Row>

      {/* 编辑报告弹窗 */}
      <Modal
        title="编辑报告"
        open={editModalOpen}
        onCancel={() => setEditModalOpen(false)}
        onOk={() => form.submit()}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" onFinish={handleEditSubmit}>
          <Form.Item
            name="clinical_history"
            label="临床病史"
          >
            <TextArea rows={2} placeholder="请输入临床病史" />
          </Form.Item>

          <Form.Item
            name="findings"
            label="影像发现"
            rules={[{ required: true, message: '请输入影像发现' }]}
          >
            <TextArea rows={6} placeholder="请输入影像发现" />
          </Form.Item>

          <Form.Item
            name="impression"
            label="诊断意见"
            rules={[{ required: true, message: '请输入诊断意见' }]}
          >
            <TextArea rows={4} placeholder="请输入诊断意见" />
          </Form.Item>

          <Form.Item
            name="recommendation"
            label="建议"
          >
            <TextArea rows={3} placeholder="请输入建议" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ReportPage
