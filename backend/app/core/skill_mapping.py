"""
知识点命名对齐映射表
用于统一 weak_points（复盘输出）和 knowledge_points（题库标签）的命名
"""

# 标准名 -> 可能的变体/别名
SKILL_SYNONYMS = {
    # Python 基础与进阶
    "python_async": ["Python异步编程", "asyncio", "协程", "coroutine", "异步IO", "async/await"],
    "python_gil": ["GIL", "全局解释器锁", "Global Interpreter Lock", "Python并发限制"],
    "python_memory": ["Python内存管理", "垃圾回收", "GC", "内存泄漏", "引用计数"],
    "python_metaclass": ["元类", "metaclass", "类创建", "动态类"],
    "python_decorator": ["装饰器", "decorator", "@语法", "AOP"],
    "python_context_manager": ["上下文管理器", "with语句", "context manager", "资源管理"],
    
    # 后端架构
    "microservices": ["微服务", "microservices", "服务拆分", "SOA", "分布式架构"],
    "api_design": ["API设计", "RESTful", "GraphQL", "接口规范", "API版本控制"],
    "load_balancing": ["负载均衡", "Load Balancing", "Nginx", "HAProxy", "流量分发"],
    "circuit_breaker": ["熔断", "Circuit Breaker", "故障隔离", "Hystrix", "服务降级"],
    "rate_limiting": ["限流", "Rate Limiting", "流量控制", "令牌桶", "漏桶算法"],
    "service_discovery": ["服务发现", "Service Discovery", "Consul", "Eureka", "Nacos"],
    "api_gateway": ["API网关", "API Gateway", "Kong", "Zuul", "统一入口"],
    
    # 数据库
    "db_index": ["数据库索引", "B+树", "索引优化", "Index", "查询优化"],
    "db_transaction": ["事务", "Transaction", "ACID", "隔离级别", "并发控制"],
    "db_sharding": ["分库分表", "Sharding", "水平拆分", "垂直拆分", "分区"],
    "db_replication": ["主从复制", "Replication", "读写分离", "binlog", "数据同步"],
    "redis": ["Redis", "缓存", "Cache", "内存数据库", "NoSQL"],
    "redis_cluster": ["Redis集群", "Cluster", "哨兵", "Sentinel", "数据分片"],
    "sql_optimization": ["SQL优化", "慢查询", "执行计划", "Explain", "索引命中"],
    
    # 消息队列
    "message_queue": ["消息队列", "MQ", "Message Queue", "异步消息"],
    "kafka": ["Kafka", "消息中间件", "日志收集", "流处理", "高吞吐"],
    "rabbitmq": ["RabbitMQ", "AMQP", "消息路由", "死信队列"],
    "event_driven": ["事件驱动", "Event Driven", "EDA", "消息订阅", "发布订阅"],
    
    # AI 应用开发
    "llm_prompt": ["Prompt工程", "提示词设计", "Prompt Engineering", "上下文工程"],
    "llm_rag": ["RAG", "检索增强生成", "向量检索", "Embedding", "知识库"],
    "llm_agent": ["Agent", "智能体", "多Agent协作", "AutoGPT", "ReAct"],
    "llm_fine_tuning": ["模型微调", "Fine-tuning", "LoRA", "PEFT", "参数高效微调"],
    "llm_evaluation": ["模型评估", "LLM评测", "Benchmark", "幻觉检测"],
    "embedding": ["Embedding", "向量嵌入", "语义表示", "BGE", "text2vec"],
    "vector_db": ["向量数据库", "Vector DB", "Milvus", "Pinecone", "Qdrant"],
    "langchain": ["LangChain", "LLM框架", "Chain", "工具调用"],
    "llm_security": ["AI安全", "Prompt注入", "越狱攻击", "内容审核", "对齐"],
    
    # DevOps & 容器
    "docker": ["Docker", "容器化", "Container", "镜像", "容器编排"],
    "kubernetes": ["Kubernetes", "K8s", "容器编排", "Pod", "Service", "Deployment"],
    "ci_cd": ["CI/CD", "持续集成", "持续部署", "Jenkins", "GitLab CI", "DevOps"],
    "infrastructure_as_code": ["IaC", "Terraform", "基础设施即代码", "配置管理"],
    "monitoring": ["监控", "Monitoring", "Prometheus", "Grafana", "可观测性"],
    "logging": ["日志", "Logging", "ELK", "Logstash", "结构化日志"],
    
    # 系统与性能
    "concurrency": ["并发编程", "Concurrency", "多线程", "锁", "线程安全"],
    "performance": ["性能优化", "Performance", "压测", "QPS", "Latency", "P99"],
    "caching": ["缓存策略", "Caching", "Cache Aside", "Write Through", "缓存穿透"],
    "distributed_system": ["分布式系统", "Distributed System", "CAP定理", "一致性"],
    "consistency": ["数据一致性", "Consistency", "强一致性", "最终一致性", "分布式事务"],
}


def normalize_skill_name(name: str) -> str:
    """
    将任意技能名称变体映射到标准名
    
    Args:
        name: 输入的技能名称（可能是复盘输出的 weak_point）
    
    Returns:
        标准化的技能名称（对应题库 knowledge_points）
    
    Example:
        >>> normalize_skill_name("asyncio")
        'python_async'
        >>> normalize_skill_name("Python异步编程")
        'python_async'
    """
    if not name:
        return ""
    
    name_lower = name.lower().strip()
    
    for canonical, aliases in SKILL_SYNONYMS.items():
        # 检查是否匹配标准名本身
        if name_lower == canonical.lower():
            return canonical
        # 检查是否匹配任何别名
        if name_lower in [a.lower() for a in aliases]:
            return canonical
    
    # 未找到映射，返回原值（小写化）
    return name_lower


def get_skill_aliases(canonical_name: str) -> list[str]:
    """
    获取标准名的所有别名
    
    Args:
        canonical_name: 标准技能名
    
    Returns:
        该技能的所有别名列表
    """
    return SKILL_SYNONYMS.get(canonical_name, [])


def find_matching_skills(query: str, top_k: int = 5) -> list[tuple[str, float]]:
    """
    模糊匹配技能名称
    
    Args:
        query: 查询字符串
        top_k: 返回最多几个结果
    
    Returns:
        [(标准名, 匹配分数), ...]
    """
    query_lower = query.lower()
    matches = []
    
    for canonical, aliases in SKILL_SYNONYMS.items():
        all_names = [canonical] + aliases
        for name in all_names:
            # 完全匹配
            if query_lower == name.lower():
                matches.append((canonical, 1.0))
                break
            # 包含匹配
            elif query_lower in name.lower() or name.lower() in query_lower:
                score = len(query_lower) / len(name) if len(name) > 0 else 0
                matches.append((canonical, score))
                break
    
    # 去重并排序
    seen = set()
    unique_matches = []
    for canonical, score in sorted(matches, key=lambda x: x[1], reverse=True):
        if canonical not in seen:
            seen.add(canonical)
            unique_matches.append((canonical, score))
    
    return unique_matches[:top_k]


def expand_weak_points(weak_points: list[str]) -> list[str]:
    """
    扩展薄弱点列表：将每个 weak_point 映射到标准名，并包含相关别名
    用于提高题库匹配成功率
    
    Args:
        weak_points: 复盘输出的薄弱点列表
    
    Returns:
        扩展后的标准名列表（去重）
    """
    expanded = set()
    for wp in weak_points:
        canonical = normalize_skill_name(wp)
        if canonical:
            expanded.add(canonical)
    
    return list(expanded)
