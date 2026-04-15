"""
Seed script to populate database with realistic test data.
Run: python seed_data.py
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, engine, Base
from app.db.models import Company, Interview, UserProfile, Resume, QuestionCategory, Question, generate_uuid

Base.metadata.create_all(bind=engine)
db = SessionLocal()
today = date.today()


def add_iv(**kwargs):
    iv = Interview(**kwargs)
    db.add(iv)
    return iv


def _seed_questions(db):
    """Seed question bank with categories and questions (idempotent)."""
    # Check if already seeded
    existing_count = db.query(Question).count()
    if existing_count > 0:
        print(f"  Questions already seeded ({existing_count} questions found), skipping...")
        return

    # Categories
    cat_data = [
        ("算法", "算法与数据结构相关题目"),
        ("系统设计", "系统架构与设计题目"),
        ("React", "React 核心知识"),
        ("JavaScript", "JavaScript 语言基础与进阶"),
        ("CSS", "CSS 布局与原理"),
        ("工程化", "Webpack、Vite 等构建工具"),
        ("性能优化", "前端性能优化策略"),
        ("Node.js", "Node.js 运行时与后端相关"),
    ]
    categories = {}
    for name, desc in cat_data:
        existing = db.query(QuestionCategory).filter(QuestionCategory.name == name).first()
        if existing:
            categories[name] = existing
        else:
            cat = QuestionCategory(id=generate_uuid(), name=name, description=desc)
            db.add(cat)
            categories[name] = cat
    db.flush()

    questions_data = [
        # React
        {
            "category_name": "React",
            "title": "React Fiber 架构解决了什么问题？其核心设计是什么？",
            "content": "详细解释 React Fiber 架构的背景、解决的问题以及核心设计思想。",
            "answer_template": "1. 解决的问题：同步渲染长时间阻塞主线程，无法中断和恢复\n2. 核心设计：(1) 链表结构替代递归树 (2) 时间切片 (3) 优先级调度 (4) Lane 模型\n3. Fiber 节点结构：child/sibling/return 指针\n4. 渲染流程：render 阶段（可中断）-> commit 阶段（不可中断）",
            "difficulty": 5,
            "knowledge_points": ["React Fiber", "React 架构", "时间切片"],
            "company_tags": ["字节跳动", "Google"],
            "hints": ["思考为什么需要中断渲染", "链表结构相比递归树有什么优势"],
        },
        {
            "category_name": "React",
            "title": "React Diff 算法的优化策略有哪些？",
            "content": "解释 React 的 DOM Diff 算法策略，包括 key 的作用、same-level 比较等。",
            "answer_template": "1. 三个策略：(1) Web UI 只跨层级移动 (2) 同一层级节点通过 key 判定 (3) 同一节点通过 tag/key 判定类型\n2. Diff 过程：先比较顶层元素，类型不同则销毁重建\n3. 列表 Diff：key 的核心作用是判断元素是否可复用\n4. 常见错误：使用 index 作为 key 导致性能问题",
            "difficulty": 4,
            "knowledge_points": ["React Diff", "Virtual DOM", "key 作用"],
            "company_tags": ["字节跳动", "阿里巴巴"],
            "hints": ["为什么需要三种策略配合使用", "key 如何影响元素复用"],
        },
        {
            "category_name": "React",
            "title": "useEffect cleanup 函数的作用是什么？与 componentWillUnmount 有何区别？",
            "content": "解释 useEffect cleanup 的执行时机，以及与 class 组件生命周期的区别。",
            "answer_template": "1. 执行时机：下一次 effect 执行前、组件卸载时\n2. 与 componentWillUnmount 区别：cleanup 在每次 effect 执行前运行，componentWillUnmount 只在卸载时运行一次\n3. React 18 StrictMode 会在开发环境双重调用\n4. 常见场景：取消订阅、清除定时器、取消请求",
            "difficulty": 3,
            "knowledge_points": ["React Hooks", "useEffect", "生命周期"],
            "company_tags": ["Google", "腾讯"],
            "hints": ["考虑依赖变化时的行为", "React 18 有什么特殊行为"],
        },
        # JavaScript
        {
            "category_name": "JavaScript",
            "title": "var/let/const 的区别是什么？什么是暂时性死区？",
            "content": "比较三种变量声明方式的作用域、声明提升和暂时性死区。",
            "answer_template": "1. var：函数作用域、存在声明提升（初始化不提升）\n2. let：块级作用域、存在暂时性死区（TDZ）\n3. const：块级作用域、不能重新赋值、必须初始化\n4. 暂时性死区：let/const 在声明前访问会报错\n5. 最佳实践：默认使用 const，需要修改时用 let，不用 var",
            "difficulty": 2,
            "knowledge_points": ["JavaScript 作用域", "var/let/const", "暂时性死区"],
            "company_tags": ["Google", "腾讯"],
            "hints": ["考虑声明提升的具体行为", "块级作用域是什么意思"],
        },
        {
            "category_name": "JavaScript",
            "title": "闭包是什么？有什么应用场景？有什么可能导致的问题？",
            "content": "解释 JavaScript 闭包的概念、应用场景以及潜在问题。",
            "answer_template": "1. 闭包：函数能访问其词法作用域之外的变量\n2. 应用场景：模块化、私有变量、防抖节流、柯里化\n3. 问题：内存泄漏、循环引用、this 指向问题\n4. for 循环中使用 var 的经典问题：所有回调共享同一个 i",
            "difficulty": 3,
            "knowledge_points": ["闭包", "作用域", "内存管理"],
            "company_tags": ["Google", "阿里巴巴"],
            "hints": ["思考为什么需要闭包来突破作用域限制", "如何用闭包解决循环中的问题"],
        },
        {
            "category_name": "JavaScript",
            "title": "Promise 与 async/await 的区别是什么？",
            "content": "比较 Promise 构造函数和 async/await 语法糖的区别和使用场景。",
            "answer_template": "1. Promise：ES6 引入，then/catch 链式调用\n2. async/await：Promise 的语法糖，更好的可读性\n3. 区别：async/await 让异步代码看起来像同步；try/catch 统一错误处理；await 是阻塞的，Promise.all 可并行\n4. 注意事项：forEach 中 await 会串行执行",
            "difficulty": 3,
            "knowledge_points": ["Promise", "async/await", "异步编程"],
            "company_tags": ["腾讯", "美团"],
            "hints": ["思考两者在错误处理上的区别", "如何用 async/await 实现 Promise.all 的并行效果"],
        },
        # 算法
        {
            "category_name": "算法",
            "title": "手写一个防抖函数，要求支持 immediate 参数",
            "content": "实现一个防抖函数，功能包括：基础防抖、立即执行选项、取消功能。",
            "answer_template": "防抖函数关键点：(1) this 绑定 (2) arguments 传递 (3) immediate 模式下先执行再等冷静期 (4) cancel 方法取消待执行的定时器",
            "difficulty": 3,
            "knowledge_points": ["防抖", "节流", "手写实现"],
            "company_tags": ["京东", "阿里巴巴"],
            "hints": ["考虑如何取消 pending 的定时器", "immediate 为 true 时的行为是什么"],
        },
        {
            "category_name": "算法",
            "title": "实现一个深拷贝函数，要求处理循环引用",
            "content": "实现一个深拷贝函数，支持基本类型、对象、数组、日期、正则，并处理循环引用。",
            "answer_template": "深拷贝关键点：(1) WeakMap 处理循环引用 (2) 类型判断（Date/RegExp等） (3) hasOwnProperty 避免继承属性 (4) 递归处理嵌套对象",
            "difficulty": 4,
            "knowledge_points": ["深拷贝", "循环引用", "数据结构"],
            "company_tags": ["字节跳动", "美团"],
            "hints": ["为什么需要 WeakMap 而不是普通 Map", "还有哪些类型需要特殊处理"],
        },
        # CSS
        {
            "category_name": "CSS",
            "title": "解释 CSS Box Model，什么是 box-sizing: border-box 与 content-box 的区别？",
            "content": "详细解释 CSS 盒模型的概念，以及两种 box-sizing 值的计算方式的区别。",
            "answer_template": "1. CSS 盒模型：内容（content）+ 内边距（padding）+ 边框（border）+ 外边距（margin）\n2. content-box（默认）：width = content，padding/border 额外计算\n3. border-box：width = content + padding + border，margin 额外计算\n4. 实际应用：border-box 更符合直觉，常用于组件开发",
            "difficulty": 2,
            "knowledge_points": ["CSS Box Model", "box-sizing", "盒模型"],
            "company_tags": ["京东", "阿里巴巴"],
            "hints": ["考虑一个 100px 宽的元素 padding 20px 后的实际宽度"],
        },
        {
            "category_name": "CSS",
            "title": "Flex 布局的原理是什么？常用属性有哪些？",
            "content": "解释 Flex 布局的工作原理，以及主轴和交叉轴的概念。",
            "answer_template": "1. 容器属性：display: flex; flex-direction; justify-content; align-items; flex-wrap\n2. 项目属性：flex-grow; flex-shrink; flex-basis; align-self\n3. 主轴与交叉轴：flex-direction 决定主轴方向，交叉轴垂直于主轴",
            "difficulty": 2,
            "knowledge_points": ["Flexbox", "CSS 布局", "主轴交叉轴"],
            "company_tags": ["美团", "京东"],
            "hints": ["justify-content 和 align-items 分别作用于哪个轴", "flex: 1 1 0 是什么意思"],
        },
        # 系统设计
        {
            "category_name": "系统设计",
            "title": "设计一个短视频 Feed 流的前端架构",
            "content": "考虑性能、体验和工程化角度，设计一个抖音/快手风格的短视频 Feed 系统。",
            "answer_template": "1. 核心问题：首屏加载、滑动流畅度、预加载与缓存\n2. 列表策略：虚拟列表（只渲染可见区域）、窗口化渲染\n3. 预加载：提前加载下一个视频、预取缩略图\n4. 缓存策略：内存缓存 LRU、磁盘缓存、CDN\n5. 性能指标：首屏 < 1s、FPS 60、TTI < 3s",
            "difficulty": 5,
            "knowledge_points": ["系统设计", "Feed 流", "虚拟列表", "性能优化"],
            "company_tags": ["字节跳动", "Google"],
            "hints": ["考虑无限滚动场景下 DOM 爆炸问题", "视频的预加载时机如何确定"],
        },
        {
            "category_name": "系统设计",
            "title": "如何设计一个前端监控 SDK？",
            "content": "设计一个前端监控 SDK，需要覆盖性能监控、错误追踪和用户行为。",
            "answer_template": "1. 性能监控：Performance API 获取 FCP/LCP/CLS/FID；Resource Timing API 监控静态资源\n2. 错误追踪：全局 error 事件、unhandledrejection、React ComponentStack\n3. 行为采集：PV/UV、页面停留时长、点击热力图、用户路径\n4. 数据上报：Beacon API / img 标签、采样率控制、批量上报合并",
            "difficulty": 5,
            "knowledge_points": ["前端监控", "性能指标", "错误追踪"],
            "company_tags": ["字节跳动", "阿里巴巴"],
            "hints": ["Beacon API 相比 xhr 有什么优势", "如何减少监控代码对主线程的影响"],
        },
        # Node.js
        {
            "category_name": "Node.js",
            "title": "Node.js Event Loop 的阶段有哪些？setTimeout/setImmediate/process.nextTick 的区别是什么？",
            "content": "详细解释 Node.js 事件循环的各个阶段，以及三种异步调度的区别。",
            "answer_template": "1. Event Loop 6个阶段：timers -> pending callbacks -> idle/prepare -> poll -> check -> close callbacks\n2. process.nextTick：在当前阶段结束前调用，优先级高于 setImmediate\n3. setImmediate：在 check 阶段执行\n4. 区别：nextTick 在同阶段开头，setImmediate 在 check 阶段",
            "difficulty": 4,
            "knowledge_points": ["Node.js Event Loop", "事件循环", "异步调度"],
            "company_tags": ["腾讯", "阿里巴巴"],
            "hints": ["什么场景下 setImmediate 比 setTimeout 先执行", "nextTick 为什么能打断 setImmediate"],
        },
        # 性能优化
        {
            "category_name": "性能优化",
            "title": "前端首屏加载优化有哪些策略？",
            "content": "从渲染原理出发，列举首屏加载优化的各种策略。",
            "answer_template": "1. 资源优化：代码分割/懒加载、Tree Shaking、压缩混淆、图片优化\n2. 渲染优化：SSR/预渲染/客户端水合、Streaming SSR、内联关键 CSS\n3. 缓存策略：浏览器缓存（Cache-Control/ETag）、Service Worker 缓存、CDN 边缘缓存\n4. 请求优化：DNS 预解析（prefetch）、预连接（preconnect）、资源提示",
            "difficulty": 4,
            "knowledge_points": ["性能优化", "首屏优化", "Webpack"],
            "company_tags": ["Google", "字节跳动"],
            "hints": ["什么是关键渲染路径", "Streaming SSR 和传统 SSR 有什么区别"],
        },
    ]

    for q_data in questions_data:
        cat = categories.get(q_data["category_name"])
        if not cat:
            continue
        q = Question(
            id=generate_uuid(),
            category_id=cat.id,
            title=q_data["title"],
            content=q_data["content"],
            answer_template=q_data["answer_template"],
            difficulty=q_data["difficulty"],
            knowledge_points=q_data["knowledge_points"],
            company_tags=q_data["company_tags"],
            hints=q_data["hints"],
        )
        db.add(q)

    print(f"  Seeded {len(questions_data)} questions in {len(categories)} categories")


def create_test_data():
    try:
        resume = Resume(
            id=generate_uuid(),
            full_name="张三",
            phone="138-0000-0000",
            email="zhangsan@example.com",
            summary="5 年前端开发经验，专注于 React 生态和大型应用架构设计。主导过多个从 0 到 1 的项目，擅长性能优化和工程化体系建设。",
            skills=[
                "React",
                "TypeScript",
                "JavaScript",
                "Node.js",
                "Vue.js",
                "Webpack",
                "Vite",
                "HTML/CSS",
                "Redux",
                "GraphQL",
                "PostgreSQL",
                "Docker",
                "CI/CD",
            ],
            education=[
                {
                    "school": "浙江大学",
                    "degree": "硕士",
                    "major": "计算机科学与技术",
                    "start_date": "2016-09",
                    "end_date": "2019-06",
                    "description": "GPA 3.7/4.0，研究方向：Web 性能优化",
                },
                {
                    "school": "华中科技大学",
                    "degree": "本科",
                    "major": "软件工程",
                    "start_date": "2012-09",
                    "end_date": "2016-06",
                    "description": "",
                },
            ],
            work_experience=[
                {
                    "company": "某互联网公司",
                    "position": "高级前端工程师",
                    "start_date": "2021-07",
                    "end_date": "至今",
                    "description": "负责核心业务线前端架构设计与性能优化。主导微前端迁移，将单体应用拆分为 5 个独立子应用。建设前端监控体系，FCP 从 2.8s 优化至 1.2s。",
                    "technologies": "React, TypeScript, Webpack, Module Federation, Node.js",
                },
                {
                    "company": "某创业公司",
                    "position": "前端工程师",
                    "start_date": "2019-07",
                    "end_date": "2021-06",
                    "description": "参与 SaaS 平台从 0 到 1 开发，负责数据可视化和表单引擎模块。",
                    "technologies": "Vue.js, ECharts, Element UI, Python",
                },
            ],
            projects=[
                {
                    "name": "低代码平台",
                    "description": "内部低代码开发平台，支持拖拽式页面搭建和自定义 DSL。",
                    "role": "核心开发",
                    "start_date": "2022-03",
                    "end_date": "2023-01",
                    "technologies": "React, TypeScript, JSON Schema, Monaco Editor",
                    "achievements": "运营活动页面搭建效率提升 60%，月活用户 200+",
                },
                {
                    "name": "前端监控 SDK",
                    "description": "自研前端性能监控和错误追踪 SDK，覆盖 PV/UV、FCP/LCP、JS 错误、API 异常。",
                    "role": "负责人",
                    "start_date": "2022-06",
                    "end_date": "2022-09",
                    "technologies": "TypeScript, Performance API, Beacon API",
                    "achievements": "接入 12 个业务线，日均上报 500 万条数据",
                },
            ],
            certifications=["AWS Cloud Practitioner"],
        )
        db.add(resume)

        profile = UserProfile(
            id=generate_uuid(),
            skills=[
                "React",
                "TypeScript",
                "JavaScript",
                "Node.js",
                "Webpack",
                "性能优化",
                "系统设计",
            ],
            weak_points={
                "React Diff algorithm": {
                    "count": 2,
                    "avg_score": 5.0,
                    "first_seen": "2026-03-15",
                    "last_seen": "2026-03-23",
                    "trend": "stable",
                    "rounds": [1, 2],
                },
                "System Design": {
                    "count": 1,
                    "avg_score": 5.0,
                    "first_seen": "2026-03-23",
                    "last_seen": "2026-03-23",
                    "trend": "new",
                    "rounds": [2],
                },
                "CSS fundamentals": {
                    "count": 1,
                    "avg_score": 6.0,
                    "first_seen": "2026-03-25",
                    "last_seen": "2026-03-25",
                    "trend": "new",
                    "rounds": [1],
                },
            },
            strong_points=[
                "React Hooks",
                "Project architecture",
                "State management",
                "Clear communication",
            ],
            career_direction="前端架构 / 技术专家",
            interview_count=8,
            offer_count=1,
        )
        db.add(profile)

        companies = []

        # 1. Google - Frontend Engineer (tomorrow round 2)
        google = Company(
            id=generate_uuid(),
            name="Google",
            position="Frontend Engineer",
            status="interviewing",
            applied_date=today - timedelta(days=14),
            next_event_date=today + timedelta(days=1),
            next_event_type="interview",
            jd_text="5+ years frontend experience. Deep knowledge of React, TypeScript, and web performance.",
        )
        db.add(google)
        db.flush()
        companies.append(google)

        add_iv(
            id=generate_uuid(),
            company_id=google.id,
            round=1,
            interview_date=today - timedelta(days=7),
            format="video",
            interviewer="Alice Wang",
            raw_notes="React hooks and closure. useEffect cleanup OK but closure trap failed.",
            ai_analysis={
                "questions": [
                    {
                        "question": "useEffect cleanup timing vs componentWillUnmount",
                        "your_answer_summary": "Cleanup runs before next render and on unmount. Differs from componentWillUnmount as it responds to any dependency change.",
                        "score": 8,
                        "assessment": "Accurate answer covering dependency array impact. Missed React 18 StrictMode double-invoke behavior.",
                        "improvement": "Study React 18 StrictMode dev-only double invoke for useEffect.",
                    },
                    {
                        "question": "Output: for(var i=0;i<3;i++){setTimeout(()=>console.log(i),0)}",
                        "your_answer_summary": "Three 3s because var is function-scoped and setTimeout is async.",
                        "score": 5,
                        "assessment": "Knew result but missed closure capturing reference vs value.",
                        "improvement": "Explain closure reference capture vs value, and how let block scope solves this.",
                    },
                    {
                        "question": "Most challenging frontend project",
                        "your_answer_summary": "Internal low-code platform with drag-and-drop, custom DSL and render engine.",
                        "score": 8,
                        "assessment": "Solid project experience with clear architecture description.",
                        "improvement": "Add quantifiable metrics like improved ops efficiency by 40 percent.",
                    },
                ],
                "weak_points": ["Closure in loops", "React StrictMode behavior"],
                "strong_points": [
                    "React Hooks deep understanding",
                    "Project architecture experience",
                ],
                "next_round_prediction": [
                    "System Design",
                    "Browser rendering pipeline",
                    "Performance optimization",
                ],
                "interviewer_signals": [
                    "Interviewer asked 3 DSL details, team likely has similar needs",
                    "Closure trap not followed up, probably considered a basic requirement",
                    "Left 10 minutes for questions, good sign for passing",
                ],
            },
            expected_result_date=today - timedelta(days=5),
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=google.id,
            round=2,
            interview_date=today + timedelta(days=1),
            format="onsite",
            interviewer="Bob Chen",
            ai_analysis={},
            expected_result_date=today + timedelta(days=5),
            result_status="pending",
        )

        # 2. Tencent - Web Developer (result overdue)
        tencent = Company(
            id=generate_uuid(),
            name="Tencent",
            position="Web Developer",
            status="interviewing",
            applied_date=today - timedelta(days=20),
            jd_text="Proficient in Vue.js ecosystem. Node.js backend experience. Understanding of microservices architecture.",
        )
        db.add(tencent)
        db.flush()
        companies.append(tencent)

        add_iv(
            id=generate_uuid(),
            company_id=tencent.id,
            round=1,
            interview_date=today - timedelta(days=8),
            format="video",
            interviewer="Charlie Liu",
            raw_notes="Node.js event loop phases incomplete. Confused setImmediate vs nextTick.",
            ai_analysis={
                "questions": [
                    {
                        "question": "Node.js Event Loop phases in order",
                        "your_answer_summary": "Named timers, poll, check. Missed close callbacks and I/O callbacks.",
                        "score": 4,
                        "assessment": "Only named main phases. Confused setImmediate with process.nextTick.",
                        "improvement": "Master all 6 phases: timers, pending callbacks, idle/prepare, poll, check, close callbacks.",
                    },
                    {
                        "question": "Promise vs Observable differences and use cases",
                        "your_answer_summary": "Promise is single async, Observable is stream that emits multiple times.",
                        "score": 7,
                        "assessment": "Core difference clear. Missed backpressure concept.",
                        "improvement": "Study backpressure mechanism and Observable advantages.",
                    },
                    {
                        "question": "Microservices projects and challenges",
                        "your_answer_summary": "Split monolith into 5 microservices. Mentioned service discovery and API Gateway.",
                        "score": 6,
                        "assessment": "Has practical experience but description is shallow.",
                        "improvement": "Prepare specific microservice incident case studies.",
                    },
                ],
                "weak_points": ["Node.js Event Loop", "Microservices troubleshooting"],
                "strong_points": [
                    "Reactive programming concepts",
                    "Service decomposition experience",
                ],
                "next_round_prediction": [
                    "System Architecture",
                    "High-concurrency design",
                ],
                "interviewer_signals": [
                    "Event loop is basic, poor answer may fail round 1",
                    "Few follow-ups on microservices, role focuses on frontend",
                ],
            },
            expected_result_date=today - timedelta(days=3),
            result_status="pending",
        )

        # 3. Alibaba - Senior Frontend (unreviewed, 3 days ago)
        alibaba = Company(
            id=generate_uuid(),
            name="Alibaba",
            position="Senior Frontend Engineer",
            status="interviewing",
            applied_date=today - timedelta(days=10),
            jd_text="Expert in React ecosystem. Deep understanding of webpack/vite. Web performance optimization.",
        )
        db.add(alibaba)
        db.flush()
        companies.append(alibaba)

        add_iv(
            id=generate_uuid(),
            company_id=alibaba.id,
            round=1,
            interview_date=today - timedelta(days=3),
            format="video",
            interviewer="David Zhang",
            raw_notes="React performance and Webpack. useMemo, React.memo, virtual list but missed time slicing.",
            ai_analysis={},
            expected_result_date=today + timedelta(days=2),
            result_status="pending",
        )

        # 4. ByteDance - Frontend Architect (rejected, 2 rounds)
        bytedance = Company(
            id=generate_uuid(),
            name="ByteDance",
            position="Frontend Architect",
            status="rejected",
            applied_date=today - timedelta(days=30),
            jd_text="Deep understanding of React source code. System design for frontend infrastructure.",
        )
        db.add(bytedance)
        db.flush()
        companies.append(bytedance)

        add_iv(
            id=generate_uuid(),
            company_id=bytedance.id,
            round=1,
            interview_date=today - timedelta(days=20),
            format="video",
            interviewer="Eva Li",
            raw_notes="React Fiber and Diff. Fiber: linked list and time slicing but missed priority. Diff: key and same-level but double-ended unclear.",
            ai_analysis={
                "questions": [
                    {
                        "question": "What problem does React Fiber solve? Core design?",
                        "your_answer_summary": "Changed recursive rendering to linked list, can interrupt and resume.",
                        "score": 6,
                        "assessment": "Core idea correct but missed Lane priority model and Fiber node flags.",
                        "improvement": "Study Lane priority model and Fiber node pointer relationships.",
                    },
                    {
                        "question": "React Diff algorithm optimization strategies",
                        "your_answer_summary": "Key importance, same-level comparison, type replacement.",
                        "score": 5,
                        "assessment": "Basic strategies correct but lacked double-ended diff understanding.",
                        "improvement": "Study full Diff algorithm with minimum move operations.",
                    },
                ],
                "weak_points": ["React Fiber internals", "React Diff algorithm"],
                "strong_points": [
                    "Project architecture experience",
                    "Clear communication",
                ],
                "next_round_prediction": [
                    "System Design",
                    "Performance optimization cases",
                ],
                "interviewer_signals": [
                    "Fiber and Diff are core, shallow answers likely to fail",
                    "Interviewer followed up on Diff twice, hard requirement",
                ],
            },
            expected_result_date=today - timedelta(days=18),
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=bytedance.id,
            round=2,
            interview_date=today - timedelta(days=12),
            format="onsite",
            interviewer="Frank Wu",
            raw_notes="System design: TikTok feed. Pagination, lazy loading, virtual list but missed prefetch. First screen: only SSR, missed streaming SSR.",
            ai_analysis={
                "questions": [
                    {
                        "question": "Design a short video feed frontend architecture",
                        "your_answer_summary": "Virtual list, pagination, lazy loading, CDN.",
                        "score": 5,
                        "assessment": "Reasonable basics but missing prefetch, offline cache. Not architect-level depth.",
                        "improvement": "Study complete feed architecture with prefetch and cache strategy.",
                    },
                    {
                        "question": "How to optimize first screen load to under 1 second?",
                        "your_answer_summary": "SSR, code splitting, resource compression.",
                        "score": 4,
                        "assessment": "Only standard solutions. Missed streaming SSR, Selective Hydration, Resource Hints.",
                        "improvement": "Study streaming SSR, Partial Prerendering, Edge Rendering.",
                    },
                    {
                        "question": "React Diff optimization for list scenarios",
                        "your_answer_summary": "Use unique keys, avoid index as key.",
                        "score": 5,
                        "assessment": "Same question as round 1, no noticeable improvement.",
                        "improvement": "Should have reviewed Diff algorithm after round 1.",
                    },
                ],
                "weak_points": [
                    "System Design",
                    "React Diff algorithm",
                    "Performance optimization at scale",
                ],
                "strong_points": [
                    "Basic architecture thinking",
                    "Communication skills",
                ],
                "next_round_prediction": [],
                "interviewer_signals": [
                    "React Diff asked again with no improvement, fatal",
                    "System design lacks architect-level depth, likely rejection reason",
                    "Interviewer did not introduce team at end, usually a fail signal",
                ],
            },
            expected_result_date=today - timedelta(days=10),
            result_status="rejected",
        )

        # 5. Meituan - Frontend Dev (just applied)
        meituan = Company(
            id=generate_uuid(),
            name="Meituan",
            position="Frontend Developer",
            status="applied",
            applied_date=today,
            jd_text="Vue.js, Mini-program development, CSS animation, responsive design.",
        )
        db.add(meituan)
        companies.append(meituan)

        # 6. PDD - 3 rounds passed, waiting for offer
        pdd = Company(
            id=generate_uuid(),
            name="PDD",
            position="Senior Frontend Engineer",
            status="interviewing",
            applied_date=today - timedelta(days=25),
            next_event_date=today + timedelta(days=2),
            next_event_type="offer",
            jd_text="React, TypeScript, Node.js. E-commerce experience. Performance optimization.",
        )
        db.add(pdd)
        db.flush()
        companies.append(pdd)

        add_iv(
            id=generate_uuid(),
            company_id=pdd.id,
            round=1,
            interview_date=today - timedelta(days=18),
            format="video",
            ai_analysis={
                "questions": [
                    {
                        "question": "TypeScript generics usage with practical example",
                        "your_answer_summary": "Basic generics with API request wrapper example.",
                        "score": 7,
                        "assessment": "Correct basics with practical example. Missed generic constraints and conditional types.",
                        "improvement": "Study advanced generics: extends constraint, infer inference, conditional types.",
                    },
                ],
                "weak_points": ["Advanced TypeScript"],
                "strong_points": ["Practical API design"],
                "next_round_prediction": ["React internals"],
            },
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=pdd.id,
            round=2,
            interview_date=today - timedelta(days=10),
            format="video",
            ai_analysis={
                "questions": [
                    {
                        "question": "React state management comparison",
                        "your_answer_summary": "Compared Redux, MobX, Zustand, Context API with use cases.",
                        "score": 8,
                        "assessment": "Comprehensive comparison with project-based recommendations.",
                        "improvement": "Add Recoil and Jotai atomic state management solutions.",
                    },
                ],
                "weak_points": [],
                "strong_points": [
                    "State management expertise",
                    "Technology comparison ability",
                ],
                "next_round_prediction": ["System Design", "Leadership"],
            },
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=pdd.id,
            round=3,
            interview_date=today - timedelta(days=3),
            format="onsite",
            ai_analysis={
                "questions": [
                    {
                        "question": "How to lead frontend team technical growth?",
                        "your_answer_summary": "Tech sharing, Code Review, tech debt management, onboarding plan.",
                        "score": 7,
                        "assessment": "Clear thinking with management experience. Lacked quantifiable metrics.",
                        "improvement": "Prepare specific team improvement cases with metrics.",
                    },
                ],
                "weak_points": ["Quantifiable leadership results"],
                "strong_points": ["Team management experience", "Technical vision"],
                "next_round_prediction": [],
            },
            expected_result_date=today + timedelta(days=2),
            result_status="pending",
        )

        # 7. JD.com - rejected after round 1
        jingdong = Company(
            id=generate_uuid(),
            name="JD.com",
            position="Frontend Engineer",
            status="rejected",
            applied_date=today - timedelta(days=15),
            jd_text="React, Vue, CSS, Webpack, performance optimization.",
        )
        db.add(jingdong)
        db.flush()
        companies.append(jingdong)

        add_iv(
            id=generate_uuid(),
            company_id=jingdong.id,
            round=1,
            interview_date=today - timedelta(days=10),
            format="video",
            ai_analysis={
                "questions": [
                    {
                        "question": "CSS box model, box-sizing values",
                        "your_answer_summary": "content-box and border-box, missed inherit and initial.",
                        "score": 6,
                        "assessment": "Basic values correct but missed CSS keywords. Should be perfect for round 1.",
                        "improvement": "Review CSS fundamentals to avoid losing points on basics.",
                    },
                    {
                        "question": "Webpack loader vs plugin difference",
                        "your_answer_summary": "Loader transforms files, plugin extends functionality. Examples: babel-loader, HtmlWebpackPlugin.",
                        "score": 7,
                        "assessment": "Clear concepts with good examples. Missed tapable and hook mechanism.",
                        "improvement": "Study Webpack plugin system tapable hook mechanism.",
                    },
                    {
                        "question": "Write a debounce function",
                        "your_answer_summary": "Basic version written but missed this binding and immediate option.",
                        "score": 5,
                        "assessment": "Core logic correct but missing edge cases.",
                        "improvement": "When hand-coding, address: this binding, arguments, immediate option, cancel method.",
                    },
                ],
                "weak_points": ["CSS fundamentals", "Hand-coding completeness"],
                "strong_points": ["Webpack concepts", "Clear explanations"],
                "next_round_prediction": [],
                "interviewer_signals": [
                    "CSS basics incomplete, may leave impression of weak fundamentals",
                    "Incomplete hand-coding, frontend round 1 coding is mandatory",
                ],
            },
            result_status="rejected",
        )

        db.commit()

        # Seed question bank
        _seed_questions(db)

        db.commit()
        print("=" * 60)
        print("Test data seeded successfully!")
        print("=" * 60)
        for c in companies:
            ivs = db.query(Interview).filter(Interview.company_id == c.id).all()
            print(f"\n{c.name} ({c.position}) - Status: {c.status}")
            for iv in ivs:
                a = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
                qc = len(a.get("questions", []))
                icon = (
                    "PASS"
                    if iv.result_status == "passed"
                    else "FAIL"
                    if iv.result_status == "rejected"
                    else "WAIT"
                )
                print(f"  Round {iv.round} ({iv.format}) - {qc} questions [{icon}]")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
