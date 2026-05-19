/** 用户相关类型 */
export interface User {
  id: string
  username: string
  email: string
  full_name?: string
  role: UserRole
  department?: string
  phone?: string
  avatar_url?: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export enum UserRole {
  ADMIN = 'admin',
  RADIOLOGIST = 'radiologist',
  CLINICIAN = 'clinician',
  VIEWER = 'viewer',
}

/** 检查相关类型 */
export interface Patient {
  id: string
  patient_id: string
  name: string
  gender: string
  birth_date: string
  phone?: string
  contact_person?: string
  contact_phone?: string
  created_at: string
}

export enum ModalityType {
  CT = 'CT',
  MR = 'MR',
  US = 'US',
  XR = 'XR',
  PT = 'PT',
}

export enum BodyPart {
  CHEST = 'CHEST',
  HEAD = 'HEAD',
  ABDOMEN = 'ABDOMEN',
  PELVIS = 'PELVIS',
  SPINE = 'SPINE',
  EXTREMITY = 'EXTREMITY',
}

export enum StudyStatus {
  PENDING = 'pending',
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  ANALYZING = 'analyzing',
  COMPLETED = 'completed',
  REPORTED = 'reported',
  FAILED = 'failed',
}

export interface Study {
  id: string
  study_id: string
  patient_id: string
  accession_number?: string
  study_date: string
  modality: ModalityType
  body_part: BodyPart
  study_description?: string
  referring_physician?: string
  status: StudyStatus
  images_count: number
  file_size?: number
  created_at: string
  updated_at: string
  patient?: Patient
}

/** 分析相关类型 */
export enum AnalysisType {
  LUNG_NODULE = 'lung_nodule',
  PNEUMONIA = 'pneumonia',
  BRAIN_HEMORRHAGE = 'brain_hemorrhage',
  LIVER_LESION = 'liver_lesion',
}

export enum TaskStatus {
  QUEUED = 'queued',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface DetectionItem {
  id: string
  label: string
  confidence: number
  location: {
    x?: number
    y?: number
    z?: number
    region?: string
    side?: string
    liver_segment?: string
    lobe?: string
  }
  size?: {
    diameter?: number
    volume?: number
    width?: number
    height?: number
    depth?: number
  }
  properties?: {
    shape?: string
    margin?: string
    density?: string
    texture?: string
    calcification?: string
    pattern?: string
    distribution?: string
    severity?: string
    enhancement?: string
    mass_effect?: string
    midline_shift?: number
  }
}

export interface AnalysisTask {
  id: string
  study_id: string
  task_type: AnalysisType
  status: TaskStatus
  priority: number
  progress: number
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at: string
  detections: DetectionItem[]
}

/** 报告相关类型 */
export enum ReportStatus {
  DRAFT = 'draft',
  REVIEWING = 'reviewing',
  REVIEWED = 'reviewed',
  SIGNED = 'signed',
}

export interface Report {
  id: string
  study_id: string
  radiologist_id?: string
  reviewer_id?: string
  report_type: string
  findings: string
  impression: string
  recommendation?: string
  clinical_history?: string
  status: ReportStatus
  ai_generated: boolean
  ai_confidence?: number
  review_comment?: string
  report_date?: string
  signed_at?: string
  created_at: string
  updated_at: string
}

export interface DiagnosisResult {
  primary_diagnosis: string
  differential_diagnosis: Array<{
    diagnosis: string
    probability: number
  }>
  probability: number
  risk_level: string
  recommendations: string[]
}

/** API响应类型 */
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  total: number
  items: T[]
}

/** Token类型 */
export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}
