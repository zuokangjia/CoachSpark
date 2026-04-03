# Dev Log — 2026-04-03

## MVP 核心骨架搭建

### 产品定义
- **项目名**: CoachSpark — AI-Powered Interview Preparation Coach
- **一句话**: 围绕真实求职过程构建的 AI 教练系统，管理从投递到 Offer 全流程
- **核心差异化**: 记住每次面试表现、追踪薄弱点跨轮次关联、自动生成个性化备战路径

### 技术栈决策
| 层 | 选型 | 理由 |
|----|------|------|
| 前端 | Next.js 16 + TypeScript + Tailwind v4 + Zustand | 开发速度最快，Zustand 轻量够用 |
| 后端 | FastAPI + Pydantic v2 | 当前 Python 最热门框架，异步性能高 |
| AI 编排 | LangGraph + LangChain | 多节点有向图工作流，支持验证+回退重试 |
| 数据库 | SQLite + SQLAlchemy + Alembic | MVP 零配置，SQLAlchemy 抽象层支持后期切 PG |
| LLM | OpenRouter (多模型兼容) | 不锁定单一供应商，支持 Gemini/Claude/GPT 切换 |
| 端口 | 后端 8080 / 前端 5173 | 避免 8000/3000 端口冲突 |

### 已完成功能

#### 后端 (FastAPI)
- [x] 项目骨架: pyproject.toml, requirements.txt, Dockerfile, docker-compose.yml
- [x] 数据库层: SQLite + SQLAlchemy session + Alembic 迁移配置
- [x] 数据模型: Company, Interview, PrepPlan (含关系)
- [x] Repository 层: 通用 CRUD + 公司关联查询
- [x] Pydantic Schemas: 14 个请求/响应模型
- [x] AI 客户端: ChatOpenAI singleton (支持 OpenRouter base_url)
- [x] Prompt 模板: match / review / prep 三套结构化 prompt
- [x] LangGraph 工作流:
  - Match Graph: 提取 JD 要求 → 提取简历信息 → 对比评分 → 生成建议
  - Review Graph: 提取问题 → 评分 → 生成洞察 → 预测下一轮 → 验证输出(不达标回退)
  - Prep Graph: 排序薄弱点 → 提取 JD 方向 → 按天分配任务 → 生成每日详情
- [x] Service 层: company / interview / match / review / prep 五个 service
- [x] API 路由: 5 个 router, 12 个端点 (CRUD + 3 个 AI 端点)
- [x] main.py: CORS, lifespan (自动建表), health check

#### 前端 (Next.js)
- [x] 项目初始化: Next.js 16 + TypeScript + Tailwind v4
- [x] 依赖安装: zustand, axios, @dnd-kit, lucide-react, clsx, tailwind-merge
- [x] API 客户端: axios 封装, 5 个 API 模块
- [x] Zustand Store: company store (CRUD + 拖拽状态同步)
- [x] 投递看板: 三列看板视图 + @dnd-kit 拖拽 + 添加公司弹窗
- [x] 公司详情: 公司信息 + 面试链时间线 + 添加面试弹窗
- [x] 面试复盘: 表单输入 + AI 分析结果展示 (评分/薄弱点/优势/预测/信号)
- [x] 备战计划: 表单输入 + 按天任务卡片 + 完成打卡
- [x] Offers 页: 占位页面 (V2)
- [x] 全局导航: DashboardNav 组件, 路由高亮

### 关键问题修复

#### 1. 路由 404
- **原因**: `(dashboard)` 路由组不产生 URL 路径，与根 `page.tsx` 冲突
- **修复**: 去掉路由组，所有页面平铺在 `app/` 下，导航栏抽成独立组件

#### 2. OpenRouter 兼容
- **原因**: 默认配置只支持 OpenAI 直连
- **修复**: config 增加 `openai_base_url`，llm.py 传入 `openai_api_base`

#### 3. LangGraph 类型安全
- **prep_graph.py**: `weak_points` 是 `List[str]` 但调用了 `.get("frequency")`
- **review_graph.py**: LLM 返回可能不是 dict，`q["score"]` 可能 KeyError
- **match_graph.py**: LLM 返回可能不是 dict
- **修复**: 所有 LLM 输出节点增加 `isinstance(result, dict)` 守卫

#### 4. 前后端字段名对齐
- Review: 前端用 `user_answer`/`feedback` → 后端返回 `your_answer_summary`/`assessment`+`improvement`
- Prep: 前端用 `focus_area` → 后端返回 `focus`；tasks 从对象数组改为字符串数组
- Prep: 前端 `jd_directions` 从字符串改为逗号分隔数组

### 项目结构
```
CoachSpark/
├── backend/                    # FastAPI 后端 (端口 8080)
│   ├── app/
│   │   ├── api/v1/             # 5 个路由模块
│   │   ├── ai/
│   │   │   ├── graphs/         # 3 个 LangGraph 工作流
│   │   │   └── prompts/        # 3 套 Prompt 模板
│   │   ├── db/                 # SQLAlchemy + SQLite
│   │   ├── models/             # Pydantic schemas
│   │   └── services/           # 业务逻辑层
│   └── alembic/                # 数据库迁移
├── frontend/                   # Next.js 前端 (端口 5173)
│   └── src/app/
│       ├── page.tsx            # 投递看板 (首页)
│       ├── components/         # 共享组件
│       ├── company/[id]/       # 公司详情
│       ├── company/[id]/review/  # 面试复盘
│       ├── company/[id]/prep/    # 备战计划
│       └── offers/             # 占位页
├── dev-logs/                   # 开发记录
├── concept.md                  # 原始产品概念
└── README.md                   # 完整项目文档
```

### 下一步 (V2)
- [ ] 填入真实 OpenRouter API Key 验证 AI 功能
- [ ] Offer 比较功能
- [ ] Redis 缓存层
- [ ] Celery 异步任务队列
- [ ] 语音输入复盘
- [ ] PostgreSQL 迁移
