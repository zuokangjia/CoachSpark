# CoachSpark — AI-Powered Interview Preparation Coach

> 你的私人 AI 求职教练 — 从投递到 Offer，每一步都有数据支撑、有 AI 指路。

---

## 产品定义

CoachSpark 是一个围绕**真实求职过程**构建的 AI 教练系统。它不是题库，不是面试模拟——而是管理你从投递到 Offer 全流程的信息中枢 + AI 备战教练。

**核心差异化**：
- 记住你每一次面试的表现
- 追踪你的薄弱点并跨轮次关联
- 自动生成个性化的备战路径
- 面的越多，建议越精准

---

## 技术架构

### 技术栈

| 层 | 技术 | 作用 |
|----|------|------|
| **前端** | Next.js 16 + TypeScript + Tailwind v4 + Zustand | 看板 UI、表单、结果展示、状态管理 |
| **API 框架** | FastAPI + Pydantic v2 | 高性能异步 API、自动 OpenAPI 文档、数据验证 |
| **AI 编排** | LangGraph + LangChain | 多步骤 AI 工作流、状态管理、自动重试验证 |
| **数据库** | SQLite + SQLAlchemy + Alembic | 零配置数据库、ORM 抽象、数据库迁移 |
| **LLM** | OpenRouter (支持多模型切换: Gemini/Claude/GPT) | 核心 AI 分析能力 |
| **部署** | Docker + Vercel (前端) + Railway/Render (后端) | 容器化部署 |

### 架构图

```
┌─────────────────────────────────────────┐
│            前端 (Next.js)                │
│         看板 UI + 表单 + 结果展示         │
└──────────────────┬──────────────────────┘
                   │ HTTP / REST
                   ▼
┌─────────────────────────────────────────┐
│              FastAPI (Python)            │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ Middleware  │  │ Request/Response │  │
│  │ (CORS/Log)  │  │ Validation       │  │
│  │             │  │ (Pydantic v2)    │  │
│  └─────────────┘  └──────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
          ┌────────┼────────┐
          ▼                 ▼
┌──────────────────┐ ┌──────────────────┐
│     SQLite       │ │   LangGraph 引擎   │
│  (零配置数据库)   │ │                  │
│                  │ │  Match Graph     │
│  - 用户数据       │ │  Review Graph    │
│  - 面试记录       │ │  Prep Graph      │
│  - 复盘报告       │ │                  │
│  - 备战计划       │ └────────┬─────────┘
└──────────────────┘          │
                              ▼
                   ┌──────────────────┐
                   │ OpenAI API       │
                   └──────────────────┘
```

### 项目结构

```
CoachSpark/
├── frontend/                          # Next.js 前端
│   ├── app/
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # 投递看板
│   │   │   └── components/
│   │   ├── company/
│   │   │   └── [id]/
│   │   │       ├── page.tsx          # 公司详情 + 面试链
│   │   │       ├── review/page.tsx   # 面试复盘
│   │   │       └── prep/page.tsx     # 备战计划
│   │   ├── offers/page.tsx           # Offer 比较
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/ui/                 # shadcn/ui 组件
│   ├── lib/
│   │   ├── api-client.ts             # 后端 API 客户端
│   │   └── store/                    # Zustand stores
│   ├── .env.local
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   └── package.json
│
├── backend/                           # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 配置管理
│   │   ├── api/v1/                   # API 路由层
│   │   │   ├── companies.py
│   │   │   ├── interviews.py
│   │   │   ├── match.py
│   │   │   ├── review.py
│   │   │   └── prep.py
│   │   ├── core/                     # 核心配置
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── models/                   # Pydantic schemas
│   │   │   ├── company.py
│   │   │   ├── interview.py
│   │   │   ├── match.py
│   │   │   ├── review.py
│   │   │   └── prep.py
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── company_service.py
│   │   │   ├── interview_service.py
│   │   │   ├── match_service.py
│   │   │   ├── review_service.py
│   │   │   └── prep_service.py
│   │   ├── ai/                       # AI 层（核心亮点）
│   │   │   ├── graphs/               # LangGraph 工作流
│   │   │   │   ├── match_graph.py
│   │   │   │   ├── review_graph.py
│   │   │   │   └── prep_graph.py
│   │   │   ├── prompts/              # Prompt 模板
│   │   │   │   ├── match.py
│   │   │   │   ├── review.py
│   │   │   │   └── prep.py
│   │   │   └── llm.py                # LLM 客户端封装
│   │   └── db/                       # 数据库层
│   │       ├── session.py            # SQLite 连接
│   │       ├── models.py             # SQLAlchemy 模型
│   │       └── repository.py         # 数据访问层
│   ├── alembic/                      # 数据库迁移
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── tests/
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   └── requirements.txt
│
├── concept.md                         # 原始产品概念
└── README.md
```

---

## 核心功能模块

### MVP 范围（Week 1-2）

| 优先级 | 模块 | 功能描述 |
|--------|------|---------|
| P0 | 投递看板 | 看板视图（已投递 → 面试中 → 已结束）、公司卡片 CRUD、状态拖拽 |
| P0 | 岗位匹配分析 | 粘贴 JD + 简历 → AI 返回匹配度、优势、差距、投递建议 |
| P0 | 面试复盘 | 文字输入 → AI 生成结构化报告（问题列表 + 评分 + 改进建议 + 下一轮预测） |
| P1 | 备战计划 | 基于复盘薄弱点 + 可用天数 → 生成每日待办计划 |
| P1 | 面试链 | 公司维度时间线 + 薄弱点跨轮次追踪标签 |
| P2 | Offer 比较 | 多维度对比表格 + AI 建议 |

### AI 工作流设计

#### 1. 岗位匹配工作流 (Match Graph)

```
输入: JD 文本 + 简历文本
  ↓
[Node 1] 提取 JD 关键要求（技能、经验、学历）
  ↓
[Node 2] 提取简历关键信息
  ↓
[Node 3] 对比分析（匹配度评分 + 优势 + 差距）
  ↓
[Node 4] 生成投递建议
  ↓
输出: 结构化匹配报告 (JSON)
```

#### 2. 面试复盘工作流 (Review Graph)

```
输入: 面试原始笔记 + 公司上下文 + JD
  ↓
[Node 1] 提取面试问题列表
  ↓
[Node 2] 对每个回答评分（1-10 分 + 理由）
  ↓
[Node 3] 生成改进建议 + 薄弱点 + 优势
  ↓
[Node 4] 预测下一轮可能问的方向
  ↓
[Node 5] 验证输出质量（评分是否有理由、建议是否具体）
  ↓
  ├─ 不达标 → 回退重新生成
  └─ 达标 → 输出
  ↓
输出: 结构化复盘报告 (JSON)
```

#### 3. 备战计划工作流 (Prep Graph)

```
输入: 复盘薄弱点 + JD 关键方向 + 可用天数 + 历史面试链
  ↓
[Node 1] 提取并优先级排序薄弱点
  ↓
[Node 2] 从 JD 提取核心技术方向
  ↓
[Node 3] 按天数分配任务（薄弱点 > JD 核心 > 补充知识）
  ↓
[Node 4] 生成每日待办（学习资料 + 练习 + 口述演练）
  ↓
输出: 按天拆解的备战计划 (JSON)
```

---

## 数据模型

### Company（公司）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(255) | 公司名 |
| position | VARCHAR(255) | 岗位名 |
| jd_text | TEXT | 岗位描述原文 |
| status | VARCHAR(50) | 状态: applied / interviewing / closed |
| applied_date | DATE | 投递日期 |
| next_event_date | DATE | 下次事件日期 |
| next_event_type | VARCHAR(50) | 事件类型: interview / offer / rejection |
| notes | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### Interview（面试）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| company_id | UUID (FK) | 关联公司 |
| round | INT | 面试轮次 |
| interview_date | DATE | 面试日期 |
| format | VARCHAR(50) | 形式: phone / video / onsite |
| interviewer | VARCHAR(255) | 面试官信息 |
| raw_notes | TEXT | 用户原始笔记 |
| ai_analysis | JSON | AI 分析结果 |
| created_at | TIMESTAMP | 创建时间 |

### PrepPlan（备战计划）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| company_id | UUID (FK) | 关联公司 |
| target_round | INT | 目标轮次 |
| days_available | INT | 可用天数 |
| daily_tasks | JSON | 每日任务列表 |
| generated_from | JSON | 来源面试 ID 列表 |
| created_at | TIMESTAMP | 创建时间 |

---

## API 端点

### Companies

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/companies` | 获取所有公司列表 |
| POST | `/api/v1/companies` | 创建新公司 |
| GET | `/api/v1/companies/{id}` | 获取公司详情 |
| PUT | `/api/v1/companies/{id}` | 更新公司信息 |
| DELETE | `/api/v1/companies/{id}` | 删除公司 |

### Interviews

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/companies/{company_id}/interviews` | 获取公司所有面试记录 |
| POST | `/api/v1/companies/{company_id}/interviews` | 创建面试记录 |
| GET | `/api/v1/interviews/{id}` | 获取面试详情 |

### AI Endpoints

| Method | Path | 描述 |
|--------|------|------|
| POST | `/api/v1/match` | 岗位匹配分析 |
| POST | `/api/v1/review/analyze` | 面试复盘分析 |
| POST | `/api/v1/prep/generate` | 备战计划生成 |

---

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 环境变量

```env
# 后端 (.env)
DATABASE_URL=sqlite:///./coachspark.db
OPENAI_API_KEY=sk-or-v1-xxx
OPENAI_MODEL=google/gemini-2.5-flash
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# 前端 (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8080
```

---

## 迭代路线图

| 版本 | 功能 | 技术升级 |
|------|------|---------|
| **MVP** | 看板 + 匹配 + 复盘 + 计划 + 面试链 | SQLite, 同步 AI 调用 |
| **V2** | Offer 比较 + 语音输入复盘 | Redis 缓存, Celery 异步任务 |
| **V3** | 模拟面试 + 行业知识库 | PostgreSQL, RAG 架构 |
| **V4** | 多用户 + 社区 | OAuth 认证, 权限系统 |

---

## 面试故事线

> "CoachSpark 是一个 AI 求职教练系统。技术上我做了几个有意识的设计：
>
> 1. **前后端分离架构**：前端 Next.js 负责 UI，后端 FastAPI 负责业务逻辑和 AI 编排。MVP 阶段用 SQLite 零配置启动，但 SQLAlchemy 抽象层让我随时可以无缝切到 PostgreSQL。
>
> 2. **LangGraph AI 工作流**：这是项目的核心亮点。我没有直接调 OpenAI API，而是用 LangGraph 把每个 AI 功能编排成多节点的有向图。比如面试复盘：提取问题 → 评分 → 生成建议 → 验证输出质量。如果验证不通过，会自动回退重新生成。
>
> 3. **分层架构**：API 层 → Service 层 → AI 层 → Repository 层。每层职责清晰，AI 逻辑完全隔离，不影响业务代码。
>
> 4. **数据库迁移管理**：用 Alembic 管理 schema 变更，确保后期切 PG 时迁移脚本已经就绪。
>
> 5. **可扩展设计**：AI 分析目前是同步调用，但接口设计已经预留了异步化能力——只需加 Celery 层，前端不需要改任何代码。"
