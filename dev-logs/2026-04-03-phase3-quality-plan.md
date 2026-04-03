# Phase 3 — 全链路质量优化

> 日期: 2026-04-03
> 目标: 拉长处理流程，提升每个环节的输出质量

---

## 优化总览

| 环节 | 当前问题 | 优化方向 | 优先级 |
|------|---------|---------|--------|
| 1. 输入引导 | 自由文本门槛高 | 结构化输入模板 | P1 |
| 2. 问题提取 | 单轮提取，遗漏多 | 两阶段提取 + 关键词识别 | P1 |
| 3. 评分 | 逐题调用，标准不一 | 批量评分 + 评分锚点 | P1 |
| 4. 洞察生成 | 上下文质量差 | 趋势分析 + 行动优先级 | P1 |
| 5. 备战计划 | 模板化，无递进 | 智能难度分级 + 时间预估 | P2 |
| 6. 画像更新 | 全表扫描，趋势粗糙 | 增量更新 + 趋势算法 | P2 |

---

## 详细优化方案

### 优化 1: 结构化输入模板

**目标**: 降低用户输入门槛，提高 AI 提取准确率

**实现**:
- 前端复盘页增加"结构化模式"开关
- 结构化模式: 动态表单，每轮面试一个区块
  - 问题文本 (必填)
  - 我的回答 (必填)
  - 面试官反应 (选填: 满意/追问/跳过/不满意)
  - 自我感觉 (选填: 好/一般/差)
- 自由模式: 保持现有 textarea
- 两种模式提交后统一转为 `raw_notes` 格式

**收益**: 提取准确率从 ~60% 提升到 ~90%

---

### 优化 2: 两阶段问题提取

**目标**: 提高问题识别覆盖率

**阶段 1: 关键词提取**
```python
def extract_tech_keywords(raw_notes: str) -> list[str]:
    """从笔记中提取所有技术关键词"""
    # 使用预定义技术词表 + LLM 补充
    return ["React diff", "性能优化", "TypeScript 泛型", ...]
```

**阶段 2: 问题-回答配对**
```python
def extract_qa_pairs(raw_notes: str, keywords: list[str]) -> list[dict]:
    """对每个关键词，尝试从笔记中提取具体问题和回答"""
    # 如果笔记不够详细，返回 {question: "关于 {keyword} 的问题", incomplete: true}
    return [...]
```

**收益**: 问题遗漏率从 ~30% 降低到 ~10%

---

### 优化 3: 批量评分 + 评分锚点

**目标**: 减少 API 调用 80%，评分标准统一

**实现**:
```python
# 一次调用批量评分所有问题
SCORING_RUBRIC = """
评分标准:
1-3 分: 完全不会或严重错误
4-6 分: 知道基本概念但说不清楚，缺乏深度
7-8 分: 能完整描述核心原理，有实际案例
9-10 分: 能深入讨论源码级细节，能对比多种方案

请严格按照以上标准评分。
"""

def batch_score_answers(questions: list[dict], jd_context: str) -> list[dict]:
    """一次调用批量评分所有问题"""
    prompt = f"{SCORING_RUBRIC}\n\nJD Context: {jd_context}\n\nQuestions:\n{json.dumps(questions)}"
    result = llm.invoke(prompt)
    return parse_scores(result)
```

**收益**: API 调用从 N 次降低到 1 次，评分一致性提升

---

### 优化 4: 洞察质量升级

**目标**: 让 AI 输出真正有洞察力的分析

**优化点**:
1. **薄弱点趋势判断**
   ```
   React diff 算法: 一面 3分 → 二面 5分 → 三面 7分 (趋势: ↑ 持续改善)
   系统设计: 一面 4分 → 二面 3分 (趋势: ↓ 退步，需要重点关注)
   ```

2. **下一轮预测具体化**
   ```
   基于:
   - 一面面试官追问了性能优化，说明这是团队当前痛点
   - 二面通常是架构面，会考察系统设计能力
   - 你的系统设计在退步

   预测二面重点:
   1. 系统设计方案题 (高概率)
   2. 性能优化实战场景 (中概率)
   ```

3. **行动优先级**
   ```
   接下来 5 天，只关注这 2 个:
   1. 系统设计 (紧急: 趋势退步 + 二面重点)
   2. React diff (重要: 虽然改善但还没到 8 分)
   ```

---

### 优化 5: 智能备战计划

**目标**: 计划不再是模板化的"阅读+练习+口述"

**优化点**:
1. **难度分级**
   - 薄弱点严重程度 → 每日任务量自动调整
   - 严重 (avg_score < 4): 每天 4h，重点练习
   - 中等 (4-6): 每天 3h，理解 + 练习
   - 轻微 (> 6): 每天 1.5h，复习巩固

2. **难度递进**
   ```
   Day 1-2: 理解概念 (阅读 + 笔记整理)
   Day 3-4: 实战练习 (编码 + 白板)
   Day 5:   模拟面试 (口述 + 自测)
   ```

3. **时间预估**
   ```json
   {
     "day": 1,
     "focus": "系统设计基础",
     "priority": "high",
     "tasks": [
       {"description": "阅读系统设计入门教程", "estimated_min": 45},
       {"description": "整理 URL 短链设计思路", "estimated_min": 30},
       {"description": "口述: 2 分钟讲清楚设计思路", "estimated_min": 15}
     ],
     "total_min": 90
   }
   ```

---

### 优化 6: 增量更新 + 趋势算法

**目标**: 画像更新更高效，趋势判断更准确

**实现**:
```python
def update_profile_incremental(db: Session, new_interview: Interview):
    """只基于新面试记录增量更新画像"""
    profile = get_or_create_profile(db)

    for wp in new_interview.ai_analysis.get("weak_points", []):
        if wp not in profile.weak_points:
            profile.weak_points[wp] = {
                "count": 1,
                "scores": [],
                "first_seen": str(new_interview.created_at),
                "last_seen": str(new_interview.created_at),
            }
        profile.weak_points[wp]["count"] += 1
        profile.weak_points[wp]["last_seen"] = str(new_interview.created_at)

        # 计算趋势
        scores = profile.weak_points[wp].get("scores", [])
        if len(scores) >= 2:
            recent_avg = sum(scores[-2:]) / 2
            older_avg = sum(scores[:-2]) / len(scores[:-2]) if scores[:-2] else recent_avg
            if recent_avg > older_avg + 1:
                profile.weak_points[wp]["trend"] = "improving"
            elif recent_avg < older_avg - 1:
                profile.weak_points[wp]["trend"] = "declining"
            else:
                profile.weak_points[wp]["trend"] = "stable"

    db.commit()
```

---

## 执行顺序

1. **优化 3: 批量评分** (最大收益，最小改动)
2. **优化 4: 洞察质量升级** (直接影响用户体验)
3. **优化 6: 增量更新 + 趋势算法** (支撑优化 4)
4. **优化 2: 两阶段提取** (提高数据质量)
5. **优化 5: 智能备战计划** (提升计划价值)
6. **优化 1: 结构化输入** (前端改动，最后做)
