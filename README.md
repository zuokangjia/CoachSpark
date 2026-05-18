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
| **前端** | Next.js 16 + React 19 + TypeScript + Tailwind v4 + Zustand | 看板 UI、表单、结果展示、状态管理 |
| **API 框架** | FastAPI + Pydantic v2 | 高性能异步 API、自动 OpenAPI 文档、数据验证 |
| **AI 编排** | LangGraph + LangChain | 多步骤 AI 工作流、状态管理、自动重试验证 |
| **数据库** | SQLite / PostgreSQL + SQLAlchemy + Alembic | 零配置启动、ORM 抽象、数据库迁移 |
| **LLM** | OpenRouter (Gemini/Claude/GPT 多模型切换) | 核心 AI 分析能力 |
| **Embedding** | BGE-M3 (1024 维向量) | 知识库和画像证据的语义检索 |
| **部署** | Docker + Vercel (前端) + Railway/Render (后端) | 容器化部署 |

### 架构图

```
┌───────────────────────────────────────────┐
│              前端 (Next.js 16)              │
│   看板 UI · 练习中心 · 知识库 · 画像展示     │
└──────────────────┬────────────────────────┘
                   │ HTTP / REST
                   ▼
┌───────────────────────────────────────────┐
│              FastAPI (Python)              │
│  ┌─────────────┐  ┌───────────────────┐   │
│  │  V1 Routes  │  │   V2 Routes       │   │
│  │ · 公司/面试   │  │ · Persona 画像    │   │
│  │ · 复盘/备战   │  │ · Practice 练习   │   │
│  │ · 匹配/看板   │  │ · Knowledge 知识库│   │
│  │ · 简历/推送   │  │ · Review V2      │   │
│  └─────────────┘  └───────────────────┘   │
└──────────────────┬────────────────────────┘
                   │
          ┌────────┼────────────┐
          ▼        ▼            ▼
┌────────────┐ ┌────────┐ ┌──────────────┐
│  SQLite /  │ │ BGE-M3 │ │  LangGraph   │
│ PostgreSQL │ │Embedder│ │   AI 工作流   │
│            │ │        │ │ Match/Review │
│ Companies  │ │ Persona│ │ Prep/Practice│
│ Interviews │ │Evidence│ │              │
│ Knowledge  │ │ RAG    │ │              │
│ Practice   │ │检索    │ │              │
└────────────┘ └────────┘ └──────────────┘
```

### 项目结构

```
CoachSpark/
├── frontend/                              # Next.js 16 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                  # 投递看板（主页）
│   │   │   ├── layout.tsx                # 根布局 + 全局样式
│   │   │   ├── globals.css               # Tailwind v4 + 设计令牌
│   │   │   ├── company/[id]/             # 公司详情页
│   │   │   │   ├── page.tsx              # 详情 + 面试链
│   │   │   │   ├── review/page.tsx       # 面试复盘
│   │   │   │   └── prep/page.tsx         # 备战计划
│   │   │   ├── practice/                 # 练习中心
│   │   │   │   ├── page.tsx              # 练习看板
│   │   │   │   ├── knowledge/page.tsx    # 知识库管理
│   │   │   │   ├── drill/page.tsx        # 专项练习
│   │   │   │   ├── drills/session/[id]/  # 练习会话
│   │   │   │   ├── drills/history/       # 练习历史
│   │   │   │   ├── eight-part/page.tsx   # 八股训练
│   │   │   │   ├── import/page.tsx       # 导入题目
│   │   │   │   └── history/page.tsx      # 答题历史
│   │   │   ├── match/page.tsx            # 岗位匹配
│   │   │   ├── offers/page.tsx           # Offer 比较
│   │   │   ├── profile/page.tsx          # 用户画像
│   │   │   └── components/               # 共享组件
│   │   │       ├── company-card.tsx
│   │   │       ├── add-company-modal.tsx
│   │   │       ├── status-transition-modal.tsx
│   │   │       ├── dashboard-nav.tsx
│   │   │       └── theme-script.tsx
│   │   └── lib/
│   │       ├── api-client.ts             # 后端 API 客户端
│   │       ├── utils.ts                  # 工具函数 + 列定义
│   │       └── store/                    # Zustand 状态管理
│   │           ├── company-store.ts
│   │           └── theme-store.ts
│   ├── .env.local
│   ├── next.config.mjs
│   └── package.json
│
├── backend/                               # FastAPI 后端
│   ├── app/
│   │   ├── main.py                       # FastAPI 入口 + CORS + lifespan
│   │   ├── config.py                     # Pydantic Settings 配置
│   │   ├── api/
│   │   │   ├── v1/                       # V1 API 路由
│   │   │   │   ├── companies.py          # 公司 CRUD + 状态管理
│   │   │   │   ├── interviews.py         # 面试记录 CRUD
│   │   │   │   ├── match.py              # 岗位匹配分析
│   │   │   │   ├── review.py             # 面试复盘（V1）
│   │   │   │   ├── prep.py               # 备战计划生成
│   │   │   │   ├── offers.py             # Offer 管理
│   │   │   │   ├── dashboard.py          # 仪表盘统计
│   │   │   │   ├── profile.py            # 用户画像（V1）
│   │   │   │   ├── company_brief.py      # 面试前简报
│   │   │   │   ├── resume.py             # 简历管理
│   │   │   │   └── push.py               # 通知推送
│   │   │   └── v2/                       # V2 API 路由
│   │   │       ├── persona.py            # Persona 画像系统
│   │   │       ├── practice.py           # 练习系统
│   │   │       ├── knowledge.py          # 知识库
│   │   │       └── review.py             # 复盘（V2）
│   │   ├── services/                     # 业务逻辑层
│   │   │   ├── company_service.py
│   │   │   ├── status_service.py         # 状态流转 + Offer 创建
│   │   │   ├── review_service.py
│   │   │   ├── match_service.py
│   │   │   ├── prep_service.py
│   │   │   ├── context_builder.py        # AI 上下文构建
│   │   │   ├── insight_service.py        # 洞察分析
│   │   │   ├── profile_service.py
│   │   │   ├── persona_v2_service.py     # Persona V2 画像引擎
│   │   │   ├── practice_service.py       # 练习服务
│   │   │   ├── knowledge_indexer.py      # 知识库索引引擎
│   │   │   ├── rag_retrieval_service.py  # 向量检索服务
│   │   │   └── push_service.py           # 推送通知服务
│   │   ├── ai/                           # AI 层
│   │   │   ├── llm.py                    # LLM + Embedder 客户端
│   │   │   ├── json_utils.py             # JSON 稳定输出工具
│   │   │   ├── graphs/                   # LangGraph 工作流
│   │   │   │   ├── match_graph.py        # 岗位匹配
│   │   │   │   ├── review_graph.py       # 面试复盘
│   │   │   │   └── prep_graph.py         # 备战计划
│   │   │   └── prompts/                  # Prompt 模板
│   │   │       ├── match.py
│   │   │       ├── review.py
│   │   │       └── prep.py
│   │   ├── db/                           # 数据库层
│   │   │   ├── session.py                # SQLite/PostgreSQL 连接
│   │   │   ├── models.py                 # SQLAlchemy 模型
│   │   │   └── repository.py             # 数据访问层
│   │   ├── models/                       # Pydantic schemas
│   │   └── core/                         # 核心配置
│   │       ├── config.py
│   │       ├── logging.py
│   │       └── skill_mapping.py          # 技能分类映射
│   ├── alembic/                          # 数据库迁移
│   ├── scripts/                          # 运维脚本
│   │   ├── seed_knowledge_db.py          # 知识库种子
│   │   ├── test_rag_pipeline.py          # RAG 测试
│   │   └── ...
│   └── requirements.txt
│
├── concept.md                            # 原始产品概念
├── AGENTS.md                             # AI Agent 指引
└── README.md
```

---

## 核心功能模块

### MVP 功能（V1）

| 优先级 | 模块 | 功能描述 | 状态 |
|--------|------|---------|------|
| P0 | 投递看板 | 看板视图（已投递 → 面试中 → 已结束）、公司卡片 CRUD、状态拖拽 | ✅ |
| P0 | 岗位匹配分析 | 粘贴 JD + 简历 → AI 返回匹配度、优势、差距、投递建议 | ✅ |
| P0 | 面试复盘 | 文字输入 → AI 生成结构化报告（问题列表 + 评分 + 改进建议 + 下一轮预测） | ✅ |
| P1 | 备战计划 | 基于复盘薄弱点 + 可用天数 → 生成每日待办计划 | ✅ |
| P1 | 面试链 | 公司维度时间线 + 薄弱点跨轮次追踪标签 | ✅ |
| P1 | 状态流转 | 推进流程弹窗 + 自动创建 Offer + 拒绝分析 | ✅ |
| P1 | 仪表盘 | 投递统计 + 面试统计 + 薄弱点排行 + 今日简报 | ✅ |
| P1 | 简历管理 | 结构化简历存储、CRUD、重建 | ✅ |
| P2 | Offer 比较 | 多维度对比表格 + AI 建议 | ✅ |
| P2 | 推送通知 | 面试提醒 + 投递过期提醒、Webhook 通道（钉钉/企微/飞书） | ✅ |

### V2 增强模块

| 模块 | 功能描述 | 状态 |
|------|---------|------|
| **Persona 画像 V2** | 证据驱动的用户画像系统，面试复盘自动提取证据 → 聚合技能状态 → 生成快照 | ✅ |
| **知识库** | Markdown 文档导入、分块、BGE-M3 向量嵌入、语义检索 | ✅ |
| **题库系统** | 分类题库 + 八股模板 + 用户练习记录 + AI 生成题目 | ✅ |
| **专项练习** | Drill 题目组 + 会话管理 + 评分反馈 + 历史追踪 | ✅ |
| **RAG 检索** | 画像证据向量检索、Persona 维度解释增强、支持 pgvector 切换 | ✅ |

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

### 核心实体

| 模型 | 说明 |
|------|------|
| **Company** | 公司/岗位，status 驱动状态机 |
| **Interview** | 面试记录，含 ai_analysis JSON |
| **PrepPlan** | 备战计划，按天拆解 |
| **Offer** | Offer 信息，与公司关联 |
| **Resume** | 结构化简历（技能/教育/工作经历/项目） |
| **UserProfile** | V1 用户画像 |

### Persona V2 模型

| 模型 | 说明 |
|------|------|
| **ProfileEvidence** | 画像证据——每次面试复盘中提取的强弱项 |
| **UserSkillState** | 技能状态聚合（level/trend/confidence） |
| **UserProfileSnapshot** | 时点快照，支持历史对比 |
| **SkillTaxonomy** | 技能分类映射（别名/分类/外部引用） |

### 练习系统模型

| 模型 | 说明 |
|------|------|
| **QuestionCategory** | 知识领域分类（树形结构） |
| **Question** | 题目（多题型/知识点/难度/公司标签） |
| **UserQuestionPerformance** | 用户答题记录（分数/反馈/用时） |
| **Drill** | 题目组（按主题组织） |
| **DrillSession** | 练习会话（进度/分数/用时） |
| **EightPartTemplate** | 八股模板 |
| **GeneratedQuestion** | AI 生成的题目 |

### 知识库模型

| 模型 | 说明 |
|------|------|
| **KnowledgeItem** | 知识条目（含向量） |
| **KnowledgeDocument** | 导入的文档 |
| **KnowledgeChunk** | 文档分块（含向量，支持语义检索） |

### 通知模型

| 模型 | 说明 |
|------|------|
| **Notification** | 通知记录（类型/通道/状态/重试） |

---

## API 端点

### V1 API

#### Companies

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/companies` | 获取所有公司列表 |
| POST | `/api/v1/companies` | 创建新公司 |
| GET | `/api/v1/companies/{id}` | 获取公司详情 |
| PUT | `/api/v1/companies/{id}` | 更新公司信息 |
| DELETE | `/api/v1/companies/{id}` | 删除公司 |

#### Interviews

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/companies/{company_id}/interviews` | 获取公司所有面试记录 |
| POST | `/api/v1/companies/{company_id}/interviews` | 创建面试记录 |
| GET | `/api/v1/interviews/{id}` | 获取面试详情 |

#### AI Endpoints

| Method | Path | 描述 |
|--------|------|------|
| POST | `/api/v1/match` | 岗位匹配分析 |
| POST | `/api/v1/review/analyze` | 面试复盘分析 |
| POST | `/api/v1/prep/generate` | 备战计划生成 |

#### 辅助

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v1/dashboard` | 仪表盘统计 |
| GET | `/api/v1/company-brief/today` | 今日简报 |
| GET | `/api/v1/company-brief/{company_id}` | 面试前简报 |
| GET/PUT | `/api/v1/resume/` | 简历管理 |
| POST | `/api/v1/resume/rebuild` | 重建简历 |
| GET | `/api/v1/push/check` | 检查待推送通知 |
| POST | `/api/v1/push/send` | 手动触发推送 |

### V2 API

#### Persona 画像

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v2/persona/latest` | 获取最新画像快照 |
| POST | `/api/v2/persona/rebuild` | 重建画像快照 |
| GET | `/api/v2/persona/explain?dimension=xxx` | RAG 增强的维度解释 |
| GET | `/api/v2/persona/snapshots` | 历史快照列表 |
| GET | `/api/v2/persona/compare` | 快照对比 |

#### Practice 练习

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v2/practice/categories` | 获取知识分类树 |
| GET | `/api/v2/practice/questions` | 获取题目列表 |
| GET | `/api/v2/practice/questions/{id}` | 获取题目详情 |
| POST | `/api/v2/practice/questions/{id}/answer` | 提交答案 |
| POST | `/api/v2/practice/drills/generate` | AI 生成题目组 |
| GET | `/api/v2/practice/drills` | 获取题目组 |
| GET | `/api/v2/practice/drills/{id}` | 题目组详情 |
| POST | `/api/v2/practice/drills/{id}/start` | 开始练习会话 |
| POST | `/api/v2/practice/drills/session/{id}/answer` | 提交会话答案 |
| GET | `/api/v2/practice/drills/session/{id}` | 会话详情 |
| GET | `/api/v2/practice/history` | 练习历史 |
| GET | `/api/v2/practice/eight-part` | 八股模板列表 |
| POST | `/api/v2/practice/eight-part/answer` | 提交八股答案 |
| GET | `/api/v2/practice/performance` | 练习统计数据 |

#### Knowledge 知识库

| Method | Path | 描述 |
|--------|------|------|
| GET | `/api/v2/knowledge/items` | 知识条目列表 |
| POST | `/api/v2/knowledge/items` | 创建条目 |
| GET | `/api/v2/knowledge/items/{id}` | 条目详情 |
| PUT | `/api/v2/knowledge/items/{id}` | 更新条目 |
| DELETE | `/api/v2/knowledge/items/{id}` | 删除条目 |
| POST | `/api/v2/knowledge/import/markdown` | 导入 Markdown |
| POST | `/api/v2/knowledge/search` | 语义搜索 |
| GET | `/api/v2/knowledge/categories` | 分类列表 |

---

## 快速开始

### 环境要求

- Node.js >= 20
- Python >= 3.11
- OpenRouter API Key

### 前端

```bash
cd frontend
npm install
npm run dev
```

默认运行在 `http://localhost:5173`。

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
OPENAI_API_KEY=sk-or-v1-xxx              # OpenRouter API Key
OPENAI_MODEL=google/gemini-2.5-flash     # LLM 模型
OPENAI_BASE_URL=https://openrouter.ai/api/v1
EMBEDDING_API_KEY=sk-or-v1-xxx           # Embedding API Key（可与 LLM 共用）
EMBEDDING_MODEL=BAAI/bge-m3              # Embedding 模型
EMBEDDING_BASE_URL=https://openrouter.ai/api/v1
USE_PGVECTOR=false                       # true = PostgreSQL+pgvector, false = SQLite

# 前端 (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 调试脚本

```bash
# 知识库种子
python backend/scripts/seed_knowledge_db.py

# RAG 管线测试
python backend/scripts/test_rag_pipeline.py

# 数据检查
python backend/scripts/check_seeded.py
```

---

## 迭代路线图

| 版本 | 功能 | 技术升级 |
|------|------|---------|
| **MVP** | 看板 + 匹配 + 复盘 + 计划 + 面试链 | SQLite, 同步 AI 调用 |
| **V2** | Persona 画像 + 题库 + 知识库 + 练习系统 | BGE-M3 Embedding, RAG 检索, Persona 证据引擎 |
| **V2.1** | 通知推送 + 简历管理 + 技能分类 | Webhook 通道, 向量维度配置 |
| **V3** | 语音输入复盘 + 模拟面试 | Redis 缓存, Celery 异步任务 |
| **V4** | 多用户 + 社区 | OAuth 认证, PostgreSQL+pgvector, 权限系统 |

---

## 面试故事线

> "CoachSpark 是一个 AI 求职教练系统。技术上我做了几个有意识的设计：
>
> 1. **前后端分离架构**：前端 Next.js 负责 UI，后端 FastAPI 负责业务逻辑和 AI 编排。MVP 阶段用 SQLite 零配置启动，但 SQLAlchemy 抽象层让我随时可以无缝切到 PostgreSQL。
>
> 2. **LangGraph AI 工作流**：这是项目的核心亮点。我没有直接调 OpenAI API，而是用 LangGraph 把每个 AI 功能编排成多节点的有向图。比如面试复盘：提取问题 → 评分 → 生成建议 → 验证输出质量。如果验证不通过，会自动回退重新生成。
>
> 3. **Persona V2 证据驱动画像**：V2 的核心创新。每次复盘产生证据（strength/weakness），证据累积计算技能状态（level/trend/confidence），定期生成快照。配合 BGE-M3 向量检索，支持用 RAG 解释"为什么说这个维度是你的薄弱点"。
>
> 4. **知识库 + 练习系统**：支持 Markdown 导入 → 分块 → 向量化 → 语义检索，基于知识库 AI 实时生成面试题目，而非静态题库。
>
> 5. **分层架构**：API 层 → Service 层 → AI 层 → Repository 层。每层职责清晰，AI 逻辑完全隔离，不影响业务代码。
>
> 6. **可扩展设计**：V1/V2 路由共存，向量存储通过 use_pgvector 开关切换 SQLite JSON 列与 pgvector，为生产环境平滑迁移预留接口。"
