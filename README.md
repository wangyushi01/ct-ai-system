# CT影像AI智能分析系统

<div align="center">

基于多Agent编排的CT影像智能辅助诊断系统

</div>

---

## 项目简介

本系统是一个基于多Agent编排架构的CT影像智能辅助诊断平台，集成了 DeepSeek 大模型进行医学影像诊断推理与结构化报告生成。系统支持肺结节、肺炎、脑出血、肝脏病变等多种疾病的AI检测与辅助诊断。

### 核心能力

- 🔍 多病种检测：支持肺结节、肺炎、脑出血、肝脏病变四种疾病检测
- 🤖 LLM诊断推理：基于DeepSeek大模型进行智能诊断推理
- 📝 自动报告生成：AI自动生成结构化诊断报告
- 📊 实时进度推送：WebSocket实时推送分析进度
- 🔄 智能降级策略：无LLM/模型时自动降级为规则引擎

---

## 功能特性

### 影像管理
- 📁 DICOM影像上传（支持 .dcm / .zip 格式）
- 📋 检查列表查询与详情查看
- 🔄 检查状态追踪（上传中 → 待分析 → 分析中 → 已完成）

### AI智能分析
- 🎯 四种检测类型：肺结节、肺炎、脑出血、肝脏病变
- 📡 实时WebSocket进度推送
- 🖼️ 分析结果可视化（病灶位置、大小、置信度）
- 📚 分析历史记录查看与管理

### 报告管理
- 🤖 AI自动生成结构化诊断报告（DeepSeek驱动）
- 📄 报告包含：影像表现、诊断意见、后续建议
- 📝 支持手动触发AI生成报告
- 📋 报告列表查看与管理

---

## 快速开始

### 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.9+ | 后端运行环境 |
| Node.js | 18+ | 前端构建环境 |
| Docker | 20.10+ | 容器化部署（推荐） |
| Docker Compose | 2.0+ | 服务编排 |

### Docker部署

**1. 克隆项目**

```bash
git clone https://github.com/wangyushi01/ct-ai-system.git
cd ct-ai-system
```

**2. 配置环境变量**

编辑 `docker-compose.yml`，配置 DeepSeek API Key：

```yaml
environment:
  DEEPSEEK_API_KEY: "sk-your-deepseek-api-key"
```

> 也可使用 OpenAI，配置 `OPENAI_API_KEY` 即可

**3. 构建并启动服务**

```bash
# 构建镜像
docker compose build

# 启动所有服务
docker compose up -d
```

> 后端镜像包含 PyTorch、MONAI 等依赖，首次构建约需 10-15 分钟

**4. 初始化数据库**

```bash
docker exec -it ct-ai-backend python scripts/init_db.py
```

**5. 访问系统**

| 服务 | 地址 | 说明 |
|------|------|------|
| 系统首页 | http://localhost:3000 | 前端应用 |
| API文档 | http://localhost:8001/docs | Swagger UI |
| MinIO控制台 | http://localhost:9005 | 用户名/密码: minioadmin |
| RabbitMQ管理 | http://localhost:15672 | 用户名/密码: guest |

**默认登录账号**

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

### 本地开发

**1. 启动基础设施**

```bash
docker compose up -d postgres redis minio rabbitmq
```

**2. 启动后端**

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，配置 DATABASE_URL、REDIS_URL、MINIO_ENDPOINT、DEEPSEEK_API_KEY 等

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**3. 启动前端**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000 即可使用系统。

---

## 系统架构

### 技术栈

| 层级 | 技术栈 |
|------|--------|
| 前端 | React 18, TypeScript, Ant Design 5, Zustand, Vite |
| 后端 | FastAPI, SQLAlchemy (async), Pydantic, WebSocket |
| 数据库 | PostgreSQL 15, Redis 6 |
| 存储 | MinIO (DICOM影像) |
| 消息队列 | RabbitMQ |
| AI/ML | PyTorch, MONAI, LangChain, DeepSeek/OpenAI |

### 四层架构设计

```
┌─────────────────────────────────────────────────────┐
│                   前端展示层                          │
│        React 18 + TypeScript + Ant Design 5          │
├─────────────────────────────────────────────────────┤
│                   业务服务层                          │
│          FastAPI + SQLAlchemy + PostgreSQL            │
├─────────────────────────────────────────────────────┤
│                 Agent 编排层                          │
│   LangChain + DeepSeek/OpenAI (诊断推理 + 报告生成)    │
│   PreprocessAgent → DetectionAgent → DiagnosisAgent  │
│                      → ReportAgent                   │
├─────────────────────────────────────────────────────┤
│                 模型服务层                            │
│        PyTorch + MONAI + 算法检测 (病灶识别)           │
│   LungNodule | Pneumonia | BrainHemorrhage | Liver   │
└─────────────────────────────────────────────────────┘
```

### Agent编排流程

```
Orchestrator.analyze(study_id, analysis_type)
  │
  ├─ 1. PreprocessAgent
  │     从 MinIO 加载 DICOM → 窗宽窗位调整 → 归一化 → 去噪
  │
  ├─ 2. DetectionAgent
  │     选择检测器 → PyTorch 模型推理（或算法检测） → NMS 去重
  │
  ├─ 3. DiagnosisAgent
  │     检测结果 → DeepSeek 诊断推理 → 风险评级 → 鉴别诊断
  │     （无 LLM 时降级为规则引擎）
  │
  └─ 4. ReportAgent
        检测 + 诊断 → DeepSeek 生成报告 → 影像表现/意见/建议
        （无 LLM 时降级为模板生成）
```

---

## 项目结构

```
ct-ai-system/
├── backend/
│   ├── app/
│   │   ├── agents/                # Agent编排层
│   │   ├── ml/                    # 模型服务层
│   │   ├── api/v1/endpoints/      # API接口
│   │   ├── models/                # 数据库模型
│   │   ├── schemas/               # 请求/响应Schema
│   │   ├── services/              # 业务逻辑
│   │   ├── core/                  # 配置/日志/安全
│   │   └── db/                    # 数据库连接
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/                 # 页面组件
│   │   ├── components/            # 公共组件
│   │   ├── services/              # API调用
│   │   ├── store/                 # 状态管理
│   │   └── types/                 # TypeScript类型
│   ├── nginx.conf
│   └── Dockerfile
│
├── start.sh                       # 快速启动脚本
├── stop.sh                        # 停止服务脚本
├── status.sh                      # 状态查看脚本
└── docker-compose.yml
```

---

## 配置说明

### 环境变量

创建 `.env` 文件（可参考 `.env.example`）：

```bash
# LLM配置
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
USE_MOCK_AI=false

# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ct_ai_db

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9004
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=ct-images

# JWT密钥
SECRET_KEY=your-secret-key-change-in-production

# CORS配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 自定义AI模型

将训练好的 PyTorch 模型文件放入 `models/` 目录：

```
models/
├── lung_nodule.pth      # 肺结节检测模型
├── pneumonia.pth         # 肺炎检测模型
├── brain_hemorrhage.pth  # 脑出血检测模型
└── liver_lesion.pth      # 肝脏病变检测模型
```

系统启动时自动检测模型文件，有则加载模型推理，无则降级为算法检测。

---

## 降级策略

| 场景 | 处理方式 |
|------|----------|
| 无 DeepSeek/OpenAI Key | 使用规则引擎和模板 |
| 无训练好的模型权重 | 使用算法检测（阈值分割 + 连通域分析） |
| LangChain 加载失败 | 自动降级为 MockAIAgent |
| LLM 响应解析失败 | 静默降级为规则引擎 |

---

## API文档

启动服务后访问 http://localhost:8001/docs 查看完整API文档。

### 主要API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/me` | GET | 获取当前用户信息 |
| `/api/v1/studies` | GET | 获取检查列表 |
| `/api/v1/studies/{study_id}` | GET | 获取检查详情 |
| `/api/v1/analysis/analyze` | POST | 创建AI分析任务 |
| `/api/v1/analysis/{task_id}` | GET | 获取分析任务状态 |
| `/api/v1/studies/{study_id}/reports` | GET | 获取检查报告 |
| `/api/v1/studies/{study_id}/reports/ai-generate` | POST | AI生成报告 |

---

## 常见问题

### 数据库连接失败

```bash
# 检查PostgreSQL状态
docker compose ps postgres

# 查看日志
docker logs ct-ai-postgres
```

### 前端无法访问后端

```bash
# 检查后端状态
curl http://localhost:8001/health

# 查看后端日志
docker logs ct-ai-backend
```

### AI分析失败

```bash
# 查看后端日志，检查LLM调用情况
docker logs ct-ai-backend --tail 50 | grep -iE "LLM|DeepSeek|错误"
```

### MinIO上传失败

访问 http://localhost:9005 确认 MinIO 正常运行，检查 `ct-images` 桶是否存在。

---


### 开发规范

- Python 遵循 PEP 8，JavaScript/TypeScript 使用 ESLint
- 使用清晰的 commit message 格式
- 添加新功能时请编写相应的测试用例

---

## 待办事项

- [ ] 支持更多影像模态（MRI、超声等）
- [ ] 增加更多疾病检测模型
- [ ] 支持影像三维可视化
- [ ] 添加影像标注功能
- [ ] 支持批量分析
- [ ] 添加用户权限管理
- [ ] 完善单元测试覆盖率


---

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [React](https://react.dev/) - 用于构建用户界面的JavaScript库
- [MONAI](https://monai.io/) - 医学影像AI深度学习框架
- [DeepSeek](https://www.deepseek.com/) - 提供LLM API支持

---

<div align="center">

如果这个项目对你有帮助，请给个 Star 支持一下！

Made with ❤️ by CT-AI Team

</div>
