import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  Card,
  Descriptions,
  Button,
  Space,
  Typography,
  Tag,
  Spin,
  Row,
  Col,
  Empty,
  Upload,
  Progress,
  message,
  Alert,
  Popconfirm,
  Table,
} from 'antd'
import {
  ArrowLeftOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  UploadOutlined,
  InboxOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { studyAPI } from '@/services'
import type { UploadChangeParam, UploadFile } from 'antd/es/upload'

const { Title, Paragraph, Text } = Typography

const StudyDetailPage: React.FC = () => {
  const { studyId } = useParams<{ studyId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const { data: study, isLoading } = useQuery({
    queryKey: ['study', studyId],
    queryFn: async () => {
      const response: any = await studyAPI.get(studyId!)
      return response
    },
    enabled: !!studyId,
  })

  // 获取影像列表
  const { data: imagesData } = useQuery({
    queryKey: ['images', studyId],
    queryFn: async () => {
      const response: any = await studyAPI.listImages(studyId!)
      return response
    },
    enabled: !!studyId,
  })

  // 删除影像
  const deleteImagesMutation = useMutation({
    mutationFn: () => studyAPI.deleteImages(studyId!),
    onSuccess: () => {
      message.success('影像已删除')
      queryClient.invalidateQueries({ queryKey: ['study', studyId] })
      queryClient.invalidateQueries({ queryKey: ['images', studyId] })
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '删除失败'
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

  // 上传mutation
  const uploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      const response: any = await studyAPI.uploadDicom(studyId!, files)
      return response
    },
    onSuccess: (data) => {
      message.success(`成功上传 ${data.uploaded_count} 个文件`)
      setFileList([])
      setUploadProgress(100)
      queryClient.invalidateQueries({ queryKey: ['study', studyId] })
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '上传失败'
      message.error(errorMsg)
      setUploadProgress(0)
    },
  })

  const handleUpload = () => {
    const files = fileList.map(f => f.originFileObj).filter(Boolean) as File[]
    if (files.length === 0) {
      message.warning('请选择要上传的DICOM文件')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    // 模拟上传进度
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval)
          return 90
        }
        return prev + 10
      })
    }, 200)

    uploadMutation.mutate(files, {
      onSettled: () => {
        clearInterval(interval)
        setUploading(false)
        setUploadProgress(100)
      }
    })
  }

  const uploadProps = {
    multiple: true,
    fileList,
    onChange: (info: UploadChangeParam) => {
      setFileList(info.fileList)
    },
    beforeUpload: (file: File) => {
      const isValid = file.name.endsWith('.dcm') || file.name.endsWith('.dicom') || file.name.endsWith('.dicm')
      if (!isValid) {
        message.error('只能上传DICOM格式文件 (.dcm, .dicom, .dicm)')
        return Upload.LIST_IGNORE
      }
      const isLt100M = file.size / 1024 / 1024 < 100
      if (!isLt100M) {
        message.error('文件大小不能超过100MB')
        return Upload.LIST_IGNORE
      }
      return false  // 阻止自动上传
    },
    onRemove: (file: UploadFile) => {
      setFileList(prev => prev.filter(f => f.uid !== file.uid))
    }
  }

  if (isLoading) {
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
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/studies')}>
            返回列表
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            {study.study_id}
          </Title>
          <Tag color={getStatusColor(study.status)}>
            {getStatusText(study.status)}
          </Tag>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* 基本信息 */}
        <Col xs={24} lg={12}>
          <Card title="基本信息">
            <Descriptions column={1} bordered>
              <Descriptions.Item label="检查号">{study.study_id}</Descriptions.Item>
              <Descriptions.Item label="流水号">
                {study.accession_number || '-'}
              </Descriptions.Item>
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
                {study.patient?.birth_date
                  ? dayjs(study.patient.birth_date).format('YYYY-MM-DD')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="联系电话">
                {study.patient?.phone || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="检查日期">
                {dayjs(study.study_date).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="检查类型">{study.modality}</Descriptions.Item>
              <Descriptions.Item label="检查部位">{study.body_part}</Descriptions.Item>
              <Descriptions.Item label="送检医师">
                {study.referring_physician || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="影像数量">{study.images_count} 张</Descriptions.Item>
              <Descriptions.Item label="文件大小">
                {study.file_size ? `${study.file_size.toFixed(2)} MB` : '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        {/* 检查描述 */}
        <Col xs={24} lg={12}>
          <Card title="检查描述">
            <Paragraph>
              {study.study_description || '暂无描述'}
            </Paragraph>
          </Card>

          {/* 影像上传 */}
          <Card
            title="影像上传"
            style={{ marginTop: 16 }}
            extra={
              <Space>
                <Text type="secondary">支持 .dcm, .dicom, .dicm 格式</Text>
              </Space>
            }
          >
            <Upload.Dragger {...uploadProps} style={{ marginBottom: 16 }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持批量上传DICOM文件，单个文件不超过100MB</p>
            </Upload.Dragger>

            {uploading && (
              <Progress percent={uploadProgress} status="active" style={{ marginBottom: 16 }} />
            )}

            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={handleUpload}
              disabled={fileList.length === 0 || uploading}
              loading={uploading}
              block
            >
              {uploading ? '上传中...' : `开始上传 (${fileList.length} 个文件)`}
            </Button>

            {study.images_count > 0 && (
              <Alert
                message={`当前已有 ${study.images_count} 张影像`}
                type="info"
                style={{ marginTop: 16 }}
              />
            )}
          </Card>

          {/* 影像浏览 */}
          <Card
            title="影像浏览"
            style={{ marginTop: 16 }}
            extra={
              <Space>
                <Text type="secondary">{study.images_count} 张影像</Text>
                {study.images_count > 0 && (
                  <Popconfirm
                    title="确定要删除所有影像吗？此操作不可恢复"
                    onConfirm={() => deleteImagesMutation.mutate()}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button size="small" danger icon={<DeleteOutlined />}>
                      删除全部影像
                    </Button>
                  </Popconfirm>
                )}
              </Space>
            }
          >
            {study.images_count === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无影像，请先上传"
              />
            ) : imagesData?.series?.length > 0 ? (
              <div>
                {imagesData.series.map((s: any) => (
                  <Card
                    key={s.series_id}
                    size="small"
                    title={`系列 ${s.series_number} - ${s.series_description || '未命名'}`}
                    style={{ marginBottom: 8 }}
                  >
                    <Table
                      size="small"
                      pagination={false}
                      dataSource={s.images}
                      rowKey="id"
                      columns={[
                        { title: '序号', dataIndex: 'image_number', width: 60 },
                        { title: 'UID', dataIndex: 'sop_instance_uid', ellipsis: true },
                        { title: '尺寸', key: 'size', width: 100, render: (_: any, r: any) => `${r.rows}×${r.columns}` },
                        { title: '大小', key: 'filesize', width: 80, render: (_: any, r: any) => r.file_size ? `${(r.file_size / 1024).toFixed(0)}KB` : '-' },
                      ]}
                    />
                  </Card>
                ))}
              </div>
            ) : (
              <Spin />
            )}
          </Card>

          {/* 操作按钮 */}
          <Card title="操作" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type="primary"
                icon={<ExperimentOutlined />}
                block
                onClick={() => navigate(`/studies/${study.study_id}/analysis`)}
              >
                AI 分析
              </Button>
              <Button
                icon={<FileTextOutlined />}
                block
                onClick={() => navigate(`/studies/${study.study_id}/report`)}
              >
                查看报告
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default StudyDetailPage
