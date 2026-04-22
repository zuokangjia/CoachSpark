"""
Seed data for Knowledge Base and Eight-Part Templates
知识库和八股题目种子数据
"""

from app.db.session import SessionLocal
from app.db.models import (
    KnowledgeItem,
    EightPartTemplate,
    QuestionCategory,
    generate_uuid,
)


def seed_knowledge_base():
    """知识库种子数据"""
    knowledge_items = [
        # 算法
        {
            "category": "算法",
            "title": "数组与链表",
            "content": "数组支持O(1)随机访问，但插入删除O(n)；链表插入删除O(1)但访问O(n)。结合两者优点的结构：跳表、哈希链表。",
            "concepts": ["时间复杂度", "空间复杂度", "数组", "链表", "跳表"],
            "examples": ["LRU Cache实现", "链表反转", "合并K个有序链表"],
            "tags": ["数据结构", "基础算法"],
        },
        {
            "category": "算法",
            "title": "二叉树与遍历",
            "content": "二叉树遍历：前序（根左右）、中序（左根右）、后序（左右根）。层序遍历用队列。前序可恢复树结构。",
            "concepts": ["二叉树", "递归", "迭代", "队列", "莫里斯遍历"],
            "examples": ["二叉树最大深度", "验证二叉搜索树", "序列化二叉树"],
            "tags": ["数据结构", "树"],
        },
        {
            "category": "算法",
            "title": "动态规划",
            "content": "DP三要素：最优子结构、状态定义、转移方程。常见类型：坐标DP、序列DP、区间DP、树形DP。优化：空间压缩、单调队列。",
            "concepts": ["最优子结构", "重叠子问题", "状态压缩", "空间优化"],
            "examples": ["最长公共子序列", "背包问题", "编辑距离", "股票买卖时机"],
            "tags": ["算法思想", "高级"],
        },
        {
            "category": "算法",
            "title": "图算法",
            "content": "图的表示：邻接矩阵、邻接表。遍历：DFS/BFS。最短路：Dijkstra、Bellman-Ford、Floyd。连通分量：Union-Find。",
            "concepts": [
                "最短路径",
                "最小生成树",
                "拓扑排序",
                "欧拉回路",
                "Union-Find",
            ],
            "examples": ["岛屿数量", "课程表顺序", "最短路径"],
            "tags": ["数据结构", "高级"],
        },
        {
            "category": "算法",
            "title": "排序与搜索",
            "content": "排序：快排(平均O(nlogn))、归并(稳定O(nlogn))、堆排(O(nlogn))。搜索：二分查找及其变体。",
            "concepts": ["快速排序", "归并排序", "堆排序", "二分查找", "旋转数组"],
            "examples": ["数组第K大元素", "搜索区间", "排序矩阵查找"],
            "tags": ["基础算法", "高频"],
        },
        {
            "category": "算法",
            "title": "位运算与数学",
            "content": "位运算：与、或、异或、左移右移。常见技巧：lowbit、位计数、布隆过滤器。数学：质数、斐波那契、矩阵快速幂。",
            "concepts": ["位运算", "lowbit", "布隆过滤器", "蓄水池抽样", "概率算法"],
            "examples": ["只出现一次的数", "Pow(x,n)", "多数元素"],
            "tags": ["技巧", "高频"],
        },
        # 后端
        {
            "category": "后端",
            "title": "数据库索引",
            "content": "索引原理：B+树（叶子节点链表）、Hash索引（等值查询）。聚簇索引vs非聚簇。覆盖索引、回表、最左前缀原则。",
            "concepts": ["B+树", "聚簇索引", "覆盖索引", "最左前缀", "索引下推"],
            "examples": ["索引失效场景", "分页查询优化", "联合索引设计"],
            "tags": ["数据库", "高频"],
        },
        {
            "category": "后端",
            "title": "事务与并发",
            "content": "ACID特性：原子性、一致性、隔离性、持久化。隔离级别：读未提交、读已提交、可重复读、串行化。并发问题：脏读、不可重复读、幻读。",
            "concepts": ["ACID", "隔离级别", "MVCC", "锁", "两阶段提交"],
            "examples": ["事务隔离级别选择", "死锁排查", "乐观锁vs悲观锁"],
            "tags": ["数据库", "高级"],
        },
        {
            "category": "后端",
            "title": "Redis数据结构与底层实现",
            "content": "SDS(简单动态字符串)、链表、压缩列表、哈希表、跳表、整数数组。Object编码：embstr vs raw。常用场景：缓存、分布式锁、计数器。",
            "concepts": ["SDS", "跳表", "过期策略", "淘汰策略", "Pipeline"],
            "examples": ["Redis实现分布式锁", "延迟队列", "附近的人"],
            "tags": ["缓存", "高频"],
        },
        {
            "category": "后端",
            "title": "消息队列",
            "content": "MQ作用：异步、解耦、削峰。常见MQ：RabbitMQ（交换机）、Kafka（高吞吐）、RocketMQ。消费模式：发布订阅、队列。",
            "concepts": ["消息顺序性", "消息可靠性", "幂等性", "延迟队列", "消息积压"],
            "examples": ["顺序消息处理", "消息重试", "事务消息"],
            "tags": ["中间件", "高频"],
        },
        {
            "category": "后端",
            "title": "微服务架构",
            "content": "微服务优势：独立部署、技术异构、容错。挑战：服务发现、负载均衡、熔断降级、分布式事务。网关：统一入口、路由、限流。",
            "concepts": ["服务注册发现", "API网关", "熔断器", "分布式事务", "Saga模式"],
            "examples": ["服务间调用链路追踪", "灰度发布", "蓝绿部署"],
            "tags": ["架构", "高级"],
        },
        {
            "category": "后端",
            "title": "操作系统与网络",
            "content": "进程vs线程、进程间通信、线程同步。TCP三次握手四次挥手、滑动窗口、拥塞控制。HTTP/HTTPS、TLS、WebSocket。",
            "concepts": ["进程与线程", "IO多路复用", "epoll", "TCP状态机", "HTTP/2"],
            "examples": ["epoll原理", "TCP连接建立", "HTTPS握手过程"],
            "tags": ["计算机基础", "高频"],
        },
        # AI工作流
        {
            "category": "AI工作流",
            "title": "LangChain核心概念",
            "content": "LangChain组件：Model I/O、Retrieval、Chains、Agents、Memory。PromptTemplate支持变量注入。Chain将组件串联。",
            "concepts": ["PromptTemplate", "Chain", "Agent", "Memory", "Callback"],
            "examples": ["RAG实现", "自定义Chain", "Tool调用"],
            "tags": ["框架", "工程"],
        },
        {
            "category": "AI工作流",
            "title": "LangGraph状态机",
            "content": "LangGraph基于有向图组织工作流。StateGraph定义状态和节点。条件边实现分支逻辑。支持checkpoint持久化。",
            "concepts": ["StateGraph", "节点", "边", "条件边", "Checkpoint"],
            "examples": ["多步骤推理", "自我修正", "循环检查"],
            "tags": ["框架", "高级"],
        },
        {
            "category": "AI工作流",
            "title": "RAG检索增强生成",
            "content": "RAG流程：文档分割→向量化→检索→生成。Embedding模型选择、向量数据库、分块策略影响效果。混合检索结合语义和关键词。",
            "concepts": ["Embedding", "向量检索", "混合检索", "重排序", "HyDE"],
            "examples": ["实现RAG pipeline", "多模态RAG", "查询改写"],
            "tags": ["AI应用", "工程"],
        },
        {
            "category": "AI工作流",
            "title": "Function Calling与工具调用",
            "content": "Function Calling让LLM调用外部工具。定义tool schema，LLM决定调用哪个函数。实现：天气查询、数据库查询、API调用。",
            "concepts": ["Tool", "Function Call", "Tool Choice", "Parallel Calling"],
            "examples": ["数据库问答", "多工具协作", "实时信息查询"],
            "tags": ["AI应用", "工程"],
        },
        # 提示词工程
        {
            "category": "提示词工程",
            "title": "CoT思维链",
            "content": "Chain of Thought通过让模型展示推理过程提高准确性。Zero-shot CoT用'Let\\'s think step by step'触发。Few-shot CoT提供示例。",
            "concepts": ["Zero-shot CoT", "Few-shot CoT", "自洽性", "思维骨架"],
            "examples": ["数学推理", "逻辑推导", "多步骤问题"],
            "tags": ["技巧", "高频"],
        },
        {
            "category": "提示词工程",
            "title": "角色与上下文注入",
            "content": "系统提示设定角色身份。上文注入示例演示期望输出格式。上下文窗口有限，需要选择性注入关键信息。",
            "concepts": ["System Prompt", "Few-shot", "上下文管理", "信息压缩"],
            "examples": ["面试官角色", "代码审查员", "翻译助手"],
            "tags": ["技巧", "基础"],
        },
        {
            "category": "提示词工程",
            "title": "结构化输出",
            "content": "让模型输出JSON/Markdown等结构化格式。使用Response Schema约束输出。Pydantic+LangChain简化解析。",
            "concepts": ["JSON Mode", "Response Schema", "Pydantic", "输出验证"],
            "examples": ["API响应解析", "数据抽取", "格式化报告"],
            "tags": ["技巧", "工程"],
        },
        {
            "category": "提示词工程",
            "title": "Prompt优化策略",
            "content": "迭代优化：明确任务→分解步骤→添加约束→测试评估。常用技巧：示例平衡、格式指定、避免偏见。",
            "concepts": ["迭代优化", "示例工程", "约束注入", "A/B测试"],
            "examples": ["Prompt版本管理", "自动化评估", "对抗性测试"],
            "tags": ["工程", "方法论"],
        },
        # 前沿知识
        {
            "category": "前沿知识",
            "title": "大模型架构演进",
            "content": "Transformer：Attention机制替代RNN。GPT单向语言模型，BERT双向理解。Llama用RMSNorm、SwiGLU提升效率。Mamba等状态空间模型探索RNN替代。",
            "concepts": ["Transformer", "Attention", "GPT", "BERT", "Llama", "Mamba"],
            "examples": ["Transformer源码解读", "注意力可视化", "模型选型"],
            "tags": ["LLM基础", "理论"],
        },
        {
            "category": "前沿知识",
            "title": "LLM训练流程",
            "content": "训练三阶段：预训练（大量语料）、SFT（有监督微调）、RLHF（人类反馈强化学习）。DPO简化RLHF。LoRA等参数高效微调降低算力需求。",
            "concepts": ["预训练", "SFT", "RLHF", "DPO", "LoRA", "QLoRA"],
            "examples": ["LoRA微调实战", "RLHF流程", "模型压缩"],
            "tags": ["LLM训练", "工程"],
        },
        {
            "category": "前沿知识",
            "title": "Agent智能体",
            "content": "Agent = LLM + Tools + Memory + Planning。ReAct结合推理与行动。Reflexion引入自我反思。AutoGPT探索自主Agent。",
            "concepts": ["ReAct", "Reflexion", "Tool Use", "Memory", "Planning"],
            "examples": ["自动化研究助手", "代码生成Agent", "多Agent协作"],
            "tags": ["AI应用", "前沿"],
        },
        {
            "category": "前沿知识",
            "title": "多模态大模型",
            "content": "多模态模型统一处理文本、图像、音频。CLIP连接视觉与语言。GPT-4V、Gemini支持视觉理解。视频理解是下一个前沿。",
            "concepts": ["CLIP", "视觉编码器", "跨模态对齐", "视频理解"],
            "examples": ["图文匹配", "视觉问答", "文档理解"],
            "tags": ["多模态", "前沿"],
        },
        {
            "category": "前沿知识",
            "title": "AI安全与对齐",
            "content": "对齐问题：幻觉、偏见、有害输出。缓解方法：RLHF、红队测试、 Constitutional AI。超级对齐研究AI控制问题。",
            "concepts": ["幻觉", "对齐", "RLHF", "红队", "Constitutional AI"],
            "examples": ["幻觉检测", "安全评估", "偏见消除"],
            "tags": ["安全", "重要"],
        },
    ]

    db = SessionLocal()
    try:
        for item in knowledge_items:
            existing = (
                db.query(KnowledgeItem)
                .filter(KnowledgeItem.title == item["title"])
                .first()
            )
            if existing:
                continue
            ki = KnowledgeItem(
                id=generate_uuid(),
                category=item["category"],
                title=item["title"],
                content=item["content"],
                concepts=item["concepts"],
                examples=item["examples"],
                tags=item["tags"],
                difficulty_min=1,
                difficulty_max=5,
            )
            db.add(ki)
        db.commit()
        print(f"Seeded {len(knowledge_items)} knowledge items")
    finally:
        db.close()


def seed_eight_part_templates():
    """八股题目模板种子数据"""
    templates = [
        # 自我介绍
        {
            "category": "自我介绍",
            "title": "1分钟自我介绍",
            "content": "用1分钟介绍你的背景、技术栈、项目经验和求职意向。",
            "answer_template": """【框架】
1. 基本信息：学校/专业/工作年限
2. 技术栈：擅长的技术领域
3. 项目亮点：最成功的1-2个项目，简述贡献和成果
4. 求职意向：为什么投这个岗位

【技巧】
- 用数据量化成果（如性能提升50%）
- 与岗位JD匹配的关键词
- 控制语速，避免背课文""",
            "difficulty": 1,
            "tips": ["提前准备", "突出亮点", "与岗位匹配"],
        },
        {
            "category": "自我介绍",
            "title": "3分钟详细自我介绍",
            "content": "用3分钟进行详细自我介绍，展示完整职业轨迹。",
            "answer_template": """【框架】
1. 求学经历（可选）
2. 工作经历：每段简述公司/项目/技术/成果
3. 技术专长：深入讲1-2个领域
4. 项目亮点：STAR法则描述
5. 职业规划：为什么适合这个岗位

【技巧】
- 准备多个版本（1min/3min/5min）
- 用具体数字证明能力
- 埋下伏笔引导后续问答""",
            "difficulty": 2,
            "tips": ["STAR法则", "数据量化", "引导提问"],
        },
        # 项目经历
        {
            "category": "项目经历",
            "title": "项目介绍框架",
            "content": "用STAR法则介绍项目：Situation-Task-Action-Result。",
            "answer_template": """【Situation 背景】
项目背景是什么？解决什么问题？

【Task 任务】
你的职责是什么？技术挑战在哪？

【Action 行动】
你具体做了什么？技术方案选择？

【Result 结果】
最终成果如何？数据指标？学到了什么？

【注意】
- 选择能体现技术深度的项目
- 突出你而非团队
- 准备细节追问""",
            "difficulty": 2,
            "tips": ["STAR法则", "突出个人贡献", "数据量化"],
        },
        {
            "category": "项目经历",
            "title": "最失败的项目",
            "content": "描述一个失败/挫折的项目经历，展示反思能力。",
            "answer_template": """【选择标准】
- 不是能力问题导致的失败
- 有反思和成长
- 最好有后续改进

【框架】
1. 背景：项目目标和约束
2. 失败点：具体哪里出了问题
3. 原因：分析根本原因
4. 反思：学到了什么
5. 改进：如果重来会怎么做

【注意】
- 不要甩锅给团队或外部因素
- 展示成长型思维""",
            "difficulty": 3,
            "tips": ["诚实反思", "成长思维", "改进方案"],
        },
        # 技术深度
        {
            "category": "技术深度",
            "title": "Redis为什么快",
            "content": "深入理解Redis高性能原理。",
            "answer_template": """【单线程优势】
1. 避免上下文切换
2. 避免锁竞争
3. 纯内存操作

【IO模型】
1. IO多路复用（epoll）
2. 非阻塞IO
3. 事件驱动

【数据结构】
1. 全局哈希表O(1)
2. 动态字符串SDS
3. 跳表实现有序集合

【持久化】
1. RDB：定期快照
2. AOF：命令日志

【再问】
可以追问：主从复制、集群、缓存穿透等""",
            "difficulty": 3,
            "tips": ["结构化回答", "深入细节", "引导追问"],
        },
        {
            "category": "技术深度",
            "title": "MySQL为什么用B+树",
            "content": "分析MySQL索引选择B+树的原因。",
            "answer_template": """【磁盘特性】
- 磁盘IO是瓶颈
- 局部性原理：预读
- 磁盘按页读取（4K/16K）

【B树vsB+树】
- B树：所有节点存数据，深度大，IO多
- B+树：数据在叶子，内部节点小，深度小
- 叶子链表：范围查询友好

【InnoDB优化】
- 聚簇索引：叶子存完整行数据
- 覆盖索引：不需要回表
- 自适应哈希：热点数据缓存

【追问方向】
- 索引失效场景
- 联合索引设计
- 索引下推""",
            "difficulty": 4,
            "tips": ["对比分析", "结合实践", "追问准备"],
        },
        {
            "category": "技术深度",
            "title": "分布式ID生成方案",
            "content": "设计一个分布式唯一ID生成系统。",
            "answer_template": """【需求分析】
- 全局唯一
- 趋势递增
- 高可用
- 可反解（时间、机器、序列）

【常见方案】

1. UUID
   - 优点：本地生成
   - 缺点：趋势无序、占用空间大

2. Snowflake
   - 64bit：符号(1) + 时间戳(41) + 机器(10) + 序列(12)
   - 优点：趋势递增、可反解
   - 缺点：依赖时钟

3. 雪花变种
   - 百度UidGenerator
   - 滴滴TinyId
   - 美团Leaf

【选型建议】
- 用户量小：UUID
- 中等业务：Snowflake
- 超大并发：Leaf+双Buffer""",
            "difficulty": 4,
            "tips": ["方案对比", "trade-off分析", "结合业务"],
        },
        # 系统设计
        {
            "category": "系统设计",
            "title": "设计短链系统",
            "content": "设计一个URL短链服务，支持长链转短链和短链跳转。",
            "answer_template": """【核心问题】
- 短码生成算法
- 存储选型
- 跳转302 vs 301

【短码生成】
1. 哈希后Base62（可能碰撞）
2. 分布式ID+Base62（推荐）
3. 预生成池

【存储设计】
- MySQL：id, url, short_code, expire_at
- Redis：缓存热点数据
- 布隆过滤器：判断是否已存在

【跳转优化】
- 302临时跳转（按需）
- 缓存跳转链接
- CDN加速

【追问方向】
- 并发量级？QPS多少？
- 数据量预估？
- 如何做容量规划？""",
            "difficulty": 4,
            "tips": ["需求拆解", "方案对比", "数据估算"],
        },
        {
            "category": "系统设计",
            "title": "设计feed流系统",
            "content": "设计一个信息流系统，如微博/朋友圈/小红书。",
            "answer_template": """【feed流模式】
- Pull模式：用户请求时拉取（延迟大）
- Push模式：推送给粉丝（存储大）
- 混合：大V用Pull，小V用Push

【核心表设计】
- 用户关系：who follow whom
- 内容表：微博/帖子内容
- Inbox：用户收件箱

【推拉结合】
1. 写入时：推送到粉丝Inbox
2. 大V粉丝多：写扩散转读扩散
3. 冷启动：优先拉取关注的人的feed

【性能优化】
- 缓存用户timeline
- 瀑布流分页
- 内容去重

【追问】
- 热帖处理？
- 分页不丢失/不重复？""",
            "difficulty": 5,
            "tips": ["模式选择", "权衡利弊", "细节追问"],
        },
        # 算法
        {
            "category": "算法",
            "title": "算法题解题框架",
            "content": "面试时高效解决算法题的框架。",
            "answer_template": """【5分钟理解题目】
1. 复述题目确认理解
2. 输入输出例子
3. 边界条件
4. 时间空间要求

【10分钟思考】
1. 类似问题？已知的解法？
2. 数据结构选择
3. 暴力解法（先跑通）
4. 优化：hash/双指针/滑动窗口/DP/递归

【15分钟写代码】
1. 先写函数签名
2. 边界处理
3. 核心逻辑
4. 返回结果

【5分钟验证】
1. 手动跑测试用例
2. 边界case
3. 代码风格

【禁忌】
- 不要死磕想最优解
- 不要不沟通直接写
- 不要写完不检查""",
            "difficulty": 2,
            "tips": ["沟通优先", "暴力法开刀", "边写边检查"],
        },
        {
            "category": "算法",
            "title": "高频算法模式",
            "content": "常见算法面试模式总结。",
            "answer_template": """【双指针】
- 两数之和（对撞指针）
- 滑动窗口（最长/最短子串）
- 快慢指针（环形链表）

【Hash】
- 计数（出现次数）
- 映射（字母异位词）
- 查找（两数之和）

【DP】
- 爬楼梯（最优子结构）
- 背包问题（选或不选）
- 编辑距离（状态转移）

【递归回溯】
- 全排列
- N皇后
- 组合总和

【二分查找】
- 有序数组查找
- 旋转数组
- 峰值元素

【图/树遍历】
- BFS层序遍历
- DFS前中后序
- 拓扑排序

【技巧】
- 大概率是变种
- 先想暴力解
- 用空间换时间""",
            "difficulty": 3,
            "tips": ["模式识别", "举一反三", "多练高频题"],
        },
        # HR问题
        {
            "category": "HR问题",
            "title": "离职原因",
            "content": "回答「为什么离职」这个问题。",
            "answer_template": """【原则】
- 正面表述，不抱怨
- 聚焦成长和发展
- 与钱无关或少谈钱

【好的回答】
1. 职业发展：现有公司无法满足成长需求
2. 技术挑战：寻求更大挑战
3. 方向契合：对新公司业务/技术感兴趣
4. 家庭原因：工作地点等（真实即可）

【避免的回答】
❌ 工资太低
❌ 领导傻X
❌ 同事内斗
❌ 加班太多
❌ 公司倒闭（实话说就行）

【话术模板】
"我在XXX工作X年了，主要负责XXX。虽然业务稳定，但我的技术成长遇到了瓶颈——主要是XXX方面的挑战。在关注贵司后，发现XXX方向正是我想深耕的，所以希望能加入。" """,
            "difficulty": 2,
            "tips": ["正面表述", "成长导向", "真诚不虚伪"],
        },
        {
            "category": "HR问题",
            "title": "职业规划",
            "content": "回答职业规划问题，展示长期价值。",
            "answer_template": """【时间维度】
- 1年：融入团队，掌握业务
- 3年：技术专家 or 管理路线
- 5年：影响业务/带团队

【回答框架】
1. 短期（1-2年）
   - 深入业务，熟悉系统
   - 提升技术深度
   - 独立承担项目

2. 中期（3年）
   - 技术领域专家
   - 或转向技术管理
   - 影响力扩展

3. 长期（5年）
   - 行业影响力
   - 或创业/转型

【注意】
- 不要说"想当领导"
- 不要说"几年后跳槽"
- 结合公司业务说""",
            "difficulty": 2,
            "tips": ["分时间维度", "与公司结合", "可信可行"],
        },
        # 反问环节
        {
            "category": "反问",
            "title": "反问面试官问题清单",
            "content": "面试最后反问环节的好问题。",
            "answer_template": """【问技术】
- 组内技术栈？
- 技术挑战？
- 代码规范？
- Tech Radar？

【问团队】
- 团队规模？
- 如何协作？
- Code Review？
- 团队氛围？

【问业务】
- 核心产品？
- 商业模式？
- 竞品优势？

【问成长】
- 培训机制？
- 技术成长路径？
- 晋升标准？

【问流程】
- 面试流程？
- 反馈时间？
- 下一轮？

【千万不问】
❌ 工资福利（HR轮再问）
❌ 加班情况（猎头问）
❌ 负面信息

【好问题示例】
"如果我有幸加入，初期最需要解决什么问题？"
"团队的技术愿景是什么？""",
            "difficulty": 1,
            "tips": ["不问禁忌", "问有价值的", "展示好奇心"],
        },
    ]

    db = SessionLocal()
    try:
        for t in templates:
            existing = (
                db.query(EightPartTemplate)
                .filter(EightPartTemplate.title == t["title"])
                .first()
            )
            if existing:
                continue
            et = EightPartTemplate(
                id=generate_uuid(),
                category=t["category"],
                title=t["title"],
                content=t["content"],
                answer_template=t["answer_template"],
                difficulty=t["difficulty"],
                tips=t["tips"],
            )
            db.add(et)
        db.commit()
        print(f"Seeded {len(templates)} eight-part templates")
    finally:
        db.close()


def run_seeds():
    """运行所有种子数据"""
    print("Seeding knowledge base...")
    seed_knowledge_base()
    print("Seeding eight-part templates...")
    seed_eight_part_templates()
    print("Done!")


if __name__ == "__main__":
    run_seeds()
