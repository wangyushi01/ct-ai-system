import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Card,
  Button,
  Space,
  Typography,
  Select,
  Row,
  Col,
  List,
  Tag,
  Progress,
  Alert,
  Descriptions,
  Divider,
  Spin,
  message,
} from 'antd'
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { studyAPI, analysisAPI } from '@/services'
import { AnalysisType } from '@/types'
import type { AnalysisTask, DetectionItem } from '@/types'

const { Title, Text, Paragraph } = Typography

const AnalysisPage: React.FC = () => {
  const { studyId } = useParams<{ studyId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)

  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string>(
    AnalysisType.LUNG_NODULE
  )
  const [currentTask, setCurrentTask] = useState<AnalysisTask | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [analysisStatus, setAnalysisStatus] = useState<string>('')

  // 获取检查信息
  const { data: study } = useQuery({
    queryKey: ['study', studyId],
    queryFn: async () => {
      const response: any = await studyAPI.get(studyId!)
      return response
    },
    enabled: !!studyId,
  })

  // 获取该检查的历史分析任务
  const { data: historyTasks } = useQuery({
    queryKey: ['analysis-history', studyId],
    queryFn: async () => {
      const response: any = await analysisAPI.list({ limit: 50, study_id: studyId })
      return response || []
    },
    enabled: !!studyId,
  })

  // 页面加载时，如果有历史任务且没有正在进行的任务，加载最新的
  useEffect(() => {
    if (historyTasks && historyTasks.length > 0 && !isAnalyzing && !currentTask) {
      const completedTasks = historyTasks.filter((t: any) => t.status === 'completed')
      if (completedTasks.length > 0) {
        setCurrentTask(completedTasks[0])
      }
    }
  }, [historyTasks])

  // 创建分析任务
  const analyzeMutation = useMutation({
    mutationFn: (type: string) => analysisAPI.create(studyId!, type),
    onSuccess: (task: any) => {
      setCurrentTask(task)
      setIsAnalyzing(true)
      setAnalysisProgress(0)
      // 连接WebSocket
      connectWebSocket(task.id)
    },
    onError: () => {
      // message.error('启动分析失败')
    },
  })

  // 连接WebSocket
  const connectWebSocket = (taskId: string) => {
    // 使用当前host的websocket协议
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/analysis/ws/${taskId}`
    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      console.log('WebSocket connected')
    }

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type === 'progress') {
        setAnalysisProgress(data.progress)
        setAnalysisStatus(data.message)
      } else if (data.type === 'completed') {
        setAnalysisProgress(100)
        setAnalysisStatus('分析完成')
        setIsAnalyzing(false)
        // 刷新任务数据
        queryClient.invalidateQueries({ queryKey: ['analysis', taskId] })
      } else if (data.type === 'error') {
        setAnalysisStatus(`错误: ${data.message}`)
        setIsAnalyzing(false)
      }
    }

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected')
    }
  }

  // 轮询获取任务状态
  useEffect(() => {
    if (currentTask && isAnalyzing) {
      const interval = setInterval(async () => {
        try {
          const updatedTask: any = await analysisAPI.get(currentTask.id)
          setCurrentTask(updatedTask)

          if (updatedTask.status === 'completed' || updatedTask.status === 'failed') {
            setIsAnalyzing(false)
            setAnalysisProgress(100)
            clearInterval(interval)
          }
        } catch (error) {
          console.error('Failed to fetch task status:', error)
        }
      }, 2000)

      return () => clearInterval(interval)
    }
  }, [currentTask, isAnalyzing])

  // 清理WebSocket连接
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const handleStartAnalysis = () => {
    if (!studyId) return

    if (isAnalyzing) {
      return
    }

    if (!study || study.images_count === 0) {
      message.warning('请先上传影像后再进行分析')
      return
    }

    analyzeMutation.mutate(selectedAnalysisType)
  }

  const getDetectionColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success'
    if (confidence >= 0.6) return 'warning'
    return 'error'
  }

  const getAnalysisTypeName = (type: AnalysisType) => {
    const names: Record<AnalysisType, string> = {
      lung_nodule: '肺结节检测',
      pneumonia: '肺炎检测',
      brain_hemorrhage: '脑出血检测',
      liver_lesion: '肝脏病变检测',
    }
    return names[type]
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/studies/${studyId}`)}>
            返回
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            AI 分析 - {study?.patient?.name}
          </Title>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* 左侧：分析控制 */}
        <Col xs={24} lg={8}>
          <Card title="分析类型">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Text strong>选择分析类型</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  value={selectedAnalysisType}
                  onChange={setSelectedAnalysisType}
                  disabled={isAnalyzing}
                >
                  <Select.Option value={AnalysisType.LUNG_NODULE}>
                    肺结节检测
                  </Select.Option>
                  <Select.Option value={AnalysisType.PNEUMONIA}>
                    肺炎检测
                  </Select.Option>
                  <Select.Option value={AnalysisType.BRAIN_HEMORRHAGE}>
                    脑出血检测
                  </Select.Option>
                  <Select.Option value={AnalysisType.LIVER_LESION}>
                    肝脏病变检测
                  </Select.Option>
                </Select>
              </div>

              <Button
                type="primary"
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={handleStartAnalysis}
                loading={isAnalyzing}
                disabled={!study || study.images_count === 0}
                block
              >
                {isAnalyzing ? '分析中...' : '开始分析'}
              </Button>

              {(!study || study.images_count === 0) && (
                <Alert
                  message="请先上传影像"
                  description="当前检查没有影像数据，请先到检查详情页上传DICOM影像后再进行分析"
                  type="warning"
                  showIcon
                />
              )}

              {isAnalyzing && (
                <Alert
                  message={
                    <div>
                      <div>{analysisStatus || '正在分析...'}</div>
                      <Progress
                        percent={Math.round(analysisProgress)}
                        status="active"
                        style={{ marginTop: 8 }}
                      />
                    </div>
                  }
                  type="info"
                  showIcon
                />
              )}
            </Space>
          </Card>

          {/* 检查信息 */}
          {study && (
            <Card title="检查信息" style={{ marginTop: 16 }}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="检查号">{study.study_id}</Descriptions.Item>
                <Descriptions.Item label="患者">{study.patient?.name}</Descriptions.Item>
                <Descriptions.Item label="类型">{study.modality}</Descriptions.Item>
                <Descriptions.Item label="部位">{study.body_part}</Descriptions.Item>
                <Descriptions.Item label="影像数">{study.images_count}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </Col>

        {/* 右侧：分析结果 */}
        <Col xs={24} lg={16}>
          <Card
            title="分析结果"
            extra={
              currentTask && (
                <Tag
                  icon={
                    currentTask.status === 'completed' ? (
                      <CheckCircleOutlined />
                    ) : (
                      <WarningOutlined />
                    )
                  }
                  color={currentTask.status === 'completed' ? 'success' : 'processing'}
                >
                  {currentTask.status === 'completed'
                    ? '已完成'
                    : currentTask.status === 'failed'
                    ? '失败'
                    : '进行中'}
                </Tag>
              )
            }
          >
            {!currentTask ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: '60px 0',
                  color: '#999',
                }}
              >
                <Paragraph type="secondary">
                  请选择分析类型并点击"开始分析"按钮
                </Paragraph>
              </div>
            ) : (
              <>
                {/* 分析概览 */}
                <div style={{ marginBottom: 24 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>分析类型：</Text>
                      <Text>{getAnalysisTypeName(currentTask.task_type)}</Text>
                    </div>
                    <div>
                      <Text strong>检测数量：</Text>
                      <Text>{currentTask.detections.length} 个</Text>
                    </div>
                    <div>
                      <Text strong>创建时间：</Text>
                      <Text>
                        {new Date(currentTask.created_at).toLocaleString()}
                      </Text>
                    </div>
                  </Space>
                </div>

                <Divider />

                {/* 检测结果列表 */}
                {currentTask.detections.length > 0 ? (
                  <List
                    dataSource={currentTask.detections}
                    renderItem={(item: DetectionItem, index) => (
                      <List.Item
                        key={item.id}
                        style={{
                          padding: 16,
                          background: index % 2 === 0 ? '#fafafa' : 'transparent',
                          borderRadius: 8,
                        }}
                      >
                        <List.Item.Meta
                          title={
                            <div
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                              }}
                            >
                              <Space>
                                <Text strong>
                                  病灶 {index + 1}: {item.label}
                                </Text>
                                <Tag color={getDetectionColor(item.confidence)}>
                                  {(item.confidence * 100).toFixed(1)}%
                                </Tag>
                              </Space>
                            </div>
                          }
                          description={
                            <div style={{ marginTop: 8 }}>
                              {item.location && (
                                <div>
                                  <Text type="secondary">位置：</Text>
                                  <Text>
                                    {item.location.x && `X: ${item.location.x.toFixed(1)} mm`}
                                    {item.location.y && ` Y: ${item.location.y.toFixed(1)} mm`}
                                    {item.location.z && ` Z: ${item.location.z.toFixed(1)} mm`}
                                    {item.location.region && item.location.region}
                                    {item.location.side && item.location.side}
                                  </Text>
                                </div>
                              )}
                              {item.size?.diameter && (
                                <div>
                                  <Text type="secondary">大小：</Text>
                                  <Text>直径 {item.size.diameter.toFixed(1)} mm</Text>
                                </div>
                              )}
                              {item.properties && Object.keys(item.properties).length > 0 && (
                                <div style={{ marginTop: 8 }}>
                                  {Object.entries(item.properties).map(([key, value]) => (
                                    <Tag key={key} color="blue">
                                      {key}: {value}
                                    </Tag>
                                  ))}
                                </div>
                              )}
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    {currentTask.status === 'completed' ? (
                      <Alert
                        message="未检测到异常"
                        description="AI分析未发现明显异常病灶"
                        type="success"
                        showIcon
                      />
                    ) : (
                      <Spin tip="分析中..." />
                    )}
                  </div>
                )}
              </>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default AnalysisPage
