import api from './api'
import type {
  User,
  Patient,
  Study,
  AnalysisTask,
  PaginatedResponse,
  Token,
} from '@/types'

/** 认证相关API */
export const authAPI = {
  /** 登录 */
  login: (username: string, password: string) =>
    api.post<Token>('/auth/login', { username, password }),

  /** 注册 */
  register: (data: any) =>
    api.post<User>('/auth/register', data),

  /** 获取当前用户 */
  getCurrentUser: () =>
    api.get<User>('/auth/me'),
}

/** 检查相关API */
export const studyAPI = {
  /** 获取检查列表 */
  list: (params?: {
    skip?: number
    limit?: number
    patient_id?: string
    modality?: string
    body_part?: string
    status?: string
  }) =>
    api.get<PaginatedResponse<Study>>('/studies', { params }),

  /** 获取检查详情 */
  get: (studyId: string) =>
    api.get<Study>(`/studies/${studyId}`),

  /** 创建检查 */
  create: (data: any) =>
    api.post<Study>('/studies', data),

  /** 删除检查 */
  delete: (studyId: string) =>
    api.delete(`/studies/${studyId}`),

  /** 获取系列列表 */
  listSeries: (studyId: string) =>
    api.get(`/studies/${studyId}/series`),

  /** 上传DICOM文件 */
  uploadDicom: (studyId: string, files: File[]) => {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    return api.post(`/upload/studies/${studyId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /** 获取上传状态 */
  getUploadStatus: (studyId: string) =>
    api.get(`/upload/studies/${studyId}/upload-status`),

  /** 删除所有影像 */
  deleteImages: (studyId: string) =>
    api.delete(`/upload/studies/${studyId}/images`),

  /** 获取影像列表 */
  listImages: (studyId: string) =>
    api.get(`/upload/studies/${studyId}/images`),

  /** 获取患者列表 */
  listPatients: (params?: { skip?: number; limit?: number; keyword?: string }) =>
    api.get<Patient[]>('/patients', { params }),
}

/** 分析相关API */
export const analysisAPI = {
  /** 创建分析任务 */
  create: (studyId: string, taskType: string) =>
    api.post<AnalysisTask>('/analysis/analyze', {
      study_id: studyId,
      task_type: taskType,
    }),

  /** 获取分析任务 */
  get: (taskId: string) =>
    api.get<AnalysisTask>(`/analysis/${taskId}`),

  /** 获取分析任务列表 */
  list: (params?: { skip?: number; limit?: number; status?: string; study_id?: string }) =>
    api.get<AnalysisTask[]>('/analysis', { params }),

  /** 删除分析任务 */
  delete: (taskId: string) =>
    api.delete(`/analysis/${taskId}`),
}

/** 报告相关API */
export const reportAPI = {
  /** 获取检查报告 */
  getByStudy: (studyId: string) =>
    api.get(`/studies/${studyId}/reports`),

  /** 创建报告 */
  create: (studyId: string, data: any) =>
    api.post(`/studies/${studyId}/reports`, data),

  /** AI生成报告 */
  aiGenerate: (studyId: string) =>
    api.post(`/studies/${studyId}/reports/ai-generate`),

  /** 更新报告 */
  update: (reportId: string, data: any) =>
    api.put(`/reports/${reportId}`, data),

  /** 签发报告 */
  sign: (reportId: string) =>
    api.post(`/reports/${reportId}/sign`),

  /** 获取报告列表 */
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get('/reports', { params }),

  /** 删除报告 */
  delete: (reportId: string) =>
    api.delete(`/reports/${reportId}`),
}

export default api
