"""
复盘流程速度测试脚本

功能：
1. 模拟完整的面试复盘流程
2. 测量各阶段的耗时（AI 分析、向量嵌入、画像重建）
3. 生成性能报告

用法：
  python scripts\test_review_speed.py              # 运行单次测试（需要 API）
  python scripts\test_review_speed.py --mock       # 使用模拟数据测试（不需要 API）
  python scripts\test_review_speed.py --runs 5     # 运行 5 次取平均值
  python scripts\test_review_speed.py --company-id <id>  # 指定公司 ID
"""

from __future__ import annotations

import argparse
import sys
import time
import statistics
import asyncio
from datetime import datetime

# 将项目根目录加入路径
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.services.review_service import analyze_review, save_review_and_update_profile
from app.core.logging import logger


# 测试用的面试笔记样本
SAMPLE_NOTES = """
面试官问了以下几个问题：

问题1：请解释 React 的 Virtual DOM 和 Diff 算法是如何工作的？
我的回答：React 通过虚拟 DOM 来减少真实 DOM 操作。Diff 算法会比较新旧虚拟 DOM 树的差异，然后只更新变化的部分。
面试官反应：点头，但追问了 key 的作用和列表渲染优化
自我感觉：回答得比较表面，没有深入到 Fiber 架构

问题2：在高并发场景下，如何设计一个限流系统？
我的回答：可以使用令牌桶算法或者漏桶算法。Redis 可以实现分布式限流。
面试官反应：继续问具体实现细节，比如如何处理突发流量
自我感觉：知道概念但缺乏实战经验，答得不够深入

问题3：介绍一下你最近做的项目中遇到的技术难点和解决方案
我的回答：做了一个电商后台管理系统，遇到了大数据量表格渲染性能问题，后来用了虚拟滚动解决
面试官反应：比较满意，追问了虚拟滚动的实现原理
自我感觉：这个问题回答得还不错，有具体案例支撑

问题4：MySQL 索引失效的场景有哪些？
我的回答：模糊查询 like '%xxx'、函数计算、类型转换等情况会导致索引失效
面试官反应：继续问最左前缀原则和覆盖索引
自我感觉：基础概念知道，但深度不够

总体感受：
- 面试官比较温和，会引导式提问
- 技术问题覆盖面广，从前端到后端都有涉及
- 感觉自己基础知识还可以，但深度和实战经验不足
- 有些问题紧张导致表达不够清晰
"""


# 模拟的 AI 分析结果（用于 mock 模式）
MOCK_AI_RESULT = {
    "questions": [
        {
            "question": "React Virtual DOM 和 Diff 算法",
            "your_answer_summary": "了解基本概念，但未深入 Fiber 架构",
            "score": 5,
            "assessment": "能够描述基本原理，但缺乏深度",
            "improvement": "阅读 React Fiber 源码，练习口述完整流程"
        },
        {
            "question": "高并发限流系统设计",
            "your_answer_summary": "知道令牌桶和漏桶算法，但缺乏实战经验",
            "score": 4,
            "assessment": "理论了解，但无法深入实现细节",
            "improvement": "研究 Redis + Lua 脚本实现分布式限流"
        },
        {
            "question": "项目技术难点和解决方案",
            "your_answer_summary": "使用虚拟滚动解决大数据量表格性能问题",
            "score": 7,
            "assessment": "有实际案例，能清晰表达解决方案",
            "improvement": "进一步优化，考虑添加缓存策略"
        },
        {
            "question": "MySQL 索引失效场景",
            "your_answer_summary": "列举了几种常见场景",
            "score": 6,
            "assessment": "基础概念正确，但深度不足",
            "improvement": "深入学习最左前缀原则和覆盖索引优化"
        }
    ],
    "weak_points": ["React Fiber 架构", "分布式限流实现", "MySQL 索引优化"],
    "strong_points": ["项目经验总结", "虚拟滚动实践"],
    "next_round_prediction": [
        "React 性能优化进阶",
        "分布式系统一致性",
        "数据库事务隔离级别"
    ],
    "interviewer_signals": [
        "对基础概念满意，但持续追问深度",
        "对项目经验感兴趣",
        "引导式提问，态度温和"
    ]
}


async def measure_review_once(
    company_id: str = "",
    round_num: int = 1,
    notes: str = SAMPLE_NOTES,
    use_mock: bool = False,
) -> dict:
    """
    测量单次复盘流程的耗时
    
    Returns:
        dict with timing information for each stage
    """
    db = SessionLocal()
    timings = {}
    
    try:
        # Stage 1: AI 分析
        print("\n[Stage 1] AI 分析中...")
        start_ai = time.perf_counter()
        
        if use_mock:
            # 模拟延迟
            await asyncio.sleep(0.5)
            result = MOCK_AI_RESULT.copy()
        else:
            result = await analyze_review(
                db=db,
                raw_notes=notes,
                company_name="测试公司",
                position="前端工程师",
                round_num=round_num,
                jd_key_points=["React", "系统设计", "数据库优化"],
                company_id=company_id,
            )
        
        end_ai = time.perf_counter()
        ai_duration = (end_ai - start_ai) * 1000  # ms
        timings['ai_analysis_ms'] = ai_duration
        
        mode_str = "(Mock)" if use_mock else ""
        print(f"✅ AI 分析完成{mode_str}: {ai_duration:.1f}ms")
        print(f"   - 提取问题数: {len(result.get('questions', []))}")
        print(f"   - 薄弱点: {len(result.get('weak_points', []))}")
        print(f"   - 优势点: {len(result.get('strong_points', []))}")
        
        # Stage 2: 保存记录并更新画像
        if company_id:
            print("\n[Stage 2] 保存记录并更新画像...")
            start_save = time.perf_counter()
            
            interview_data = save_review_and_update_profile(
                db=db,
                company_id=company_id,
                result=result,
                round_num=round_num,
                raw_notes=notes,
                interview_date=datetime.now().strftime("%Y-%m-%d"),
                interview_format="video",
                interviewer="技术面试官",
            )
            
            end_save = time.perf_counter()
            save_duration = (end_save - start_save) * 1000  # ms
            timings['save_and_persona_ms'] = save_duration
            
            print(f"✅ 保存和画像更新完成: {save_duration:.1f}ms")
            if isinstance(interview_data, dict):
                print(f"   - 面试记录 ID: {interview_data.get('interview_id')}")
                dim_changes = interview_data.get('dimension_changes', [])
                print(f"   - 维度变化: {len(dim_changes)} 个")
        
        # 总耗时
        total_duration = sum(timings.values())
        timings['total_ms'] = total_duration
        
        return timings
        
    except Exception as e:
        logger.error(f"复盘测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
    finally:
        db.close()


def print_report(all_timings: list[dict]):
    """打印性能报告"""
    print("\n" + "=" * 70)
    print("  📊 复盘流程性能测试报告")
    print("=" * 70)
    
    if not all_timings:
        print("❌ 没有有效的测试数据")
        return
    
    # 过滤掉失败的测试
    valid_timings = [t for t in all_timings if 'error' not in t]
    failed_count = len(all_timings) - len(valid_timings)
    
    if not valid_timings:
        print("❌ 所有测试都失败了")
        return
    
    runs = len(valid_timings)
    
    def calc_stats(key: str):
        values = [t[key] for t in valid_timings if key in t]
        if not values:
            return None
        return {
            'min': min(values),
            'max': max(values),
            'avg': statistics.mean(values),
            'median': statistics.median(values),
            'p95': sorted(values)[max(0, int(len(values) * 0.95) - 1)],
        }
    
    # AI 分析统计
    ai_stats = calc_stats('ai_analysis_ms')
    if ai_stats:
        print(f"\n🤖 AI 分析阶段 ({runs} 次测试)")
        print(f"   最小值: {ai_stats['min']:8.1f}ms  ({ai_stats['min']/1000:.2f}s)")
        print(f"   最大值: {ai_stats['max']:8.1f}ms  ({ai_stats['max']/1000:.2f}s)")
        print(f"   平均值: {ai_stats['avg']:8.1f}ms  ({ai_stats['avg']/1000:.2f}s)")
        print(f"   中位数: {ai_stats['median']:8.1f}ms  ({ai_stats['median']/1000:.2f}s)")
        print(f"   P95:    {ai_stats['p95']:8.1f}ms  ({ai_stats['p95']/1000:.2f}s)")
    
    # 保存和画像更新统计
    save_stats = calc_stats('save_and_persona_ms')
    if save_stats:
        print(f"\n💾 保存和画像更新阶段")
        print(f"   最小值: {save_stats['min']:8.1f}ms  ({save_stats['min']/1000:.2f}s)")
        print(f"   最大值: {save_stats['max']:8.1f}ms  ({save_stats['max']/1000:.2f}s)")
        print(f"   平均值: {save_stats['avg']:8.1f}ms  ({save_stats['avg']/1000:.2f}s)")
        print(f"   中位数: {save_stats['median']:8.1f}ms  ({save_stats['median']/1000:.2f}s)")
        print(f"   P95:    {save_stats['p95']:8.1f}ms  ({save_stats['p95']/1000:.2f}s)")
    
    # 总耗时统计
    total_stats = calc_stats('total_ms')
    if total_stats:
        print(f"\n⏱️  总耗时")
        print(f"   最小值: {total_stats['min']:8.1f}ms  ({total_stats['min']/1000:.2f}s)")
        print(f"   最大值: {total_stats['max']:8.1f}ms  ({total_stats['max']/1000:.2f}s)")
        print(f"   平均值: {total_stats['avg']:8.1f}ms  ({total_stats['avg']/1000:.2f}s)")
        print(f"   中位数: {total_stats['median']:8.1f}ms  ({total_stats['median']/1000:.2f}s)")
        print(f"   P95:    {total_stats['p95']:8.1f}ms  ({total_stats['p95']/1000:.2f}s)")
    
    # 性能评估
    print(f"\n{'=' * 70}")
    avg_total_s = total_stats['avg'] / 1000 if total_stats else 0
    
    if avg_total_s < 20:
        print("🎉 性能优秀！平均响应时间 < 20s")
    elif avg_total_s < 35:
        print("✨ 性能良好，平均响应时间在可接受范围内")
    elif avg_total_s < 60:
        print("⚠️  性能一般，建议优化 AI 调用或考虑异步处理")
    else:
        print("❌ 性能较差，强烈建议优化（异步化、缓存等）")
    
    if failed_count > 0:
        print(f"\n⚠️  注意: {failed_count} 次测试失败")
    
    print("=" * 70)


async def main():
    parser = argparse.ArgumentParser(description="复盘流程速度测试")
    parser.add_argument("--runs", type=int, default=1, help="测试次数（默认 1）")
    parser.add_argument("--company-id", default="", help="公司 ID（可选）")
    parser.add_argument("--round", type=int, default=1, help="面试轮次（默认 1）")
    parser.add_argument("--notes-file", default="", help="从文件读取面试笔记")
    parser.add_argument("--mock", action="store_true", help="使用模拟数据（不需要 API）")
    args = parser.parse_args()
    
    # 加载测试笔记
    notes = SAMPLE_NOTES
    if args.notes_file:
        try:
            with open(args.notes_file, 'r', encoding='utf-8') as f:
                notes = f.read()
            print(f"📄 从文件加载笔记: {args.notes_file} ({len(notes)} 字符)")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}，使用默认笔记")
    
    mode_str = "Mock 模式" if args.mock else "真实 API 模式"
    print("=" * 70)
    print(f"  🚀 复盘流程速度测试 ({mode_str})")
    print("=" * 70)
    print(f"\n配置:")
    print(f"  测试次数: {args.runs}")
    print(f"  公司 ID: {args.company_id or '(无)'}")
    print(f"  面试轮次: {args.round}")
    print(f"  笔记长度: {len(notes)} 字符")
    if args.mock:
        print(f"  ⚠️  注意: 使用模拟数据，AI 分析时间不准确")
    
    all_timings = []
    
    for i in range(1, args.runs + 1):
        print(f"\n{'=' * 70}")
        print(f"  测试 {i}/{args.runs}")
        print('=' * 70)
        
        timings = await measure_review_once(
            company_id=args.company_id,
            round_num=args.round,
            notes=notes,
            use_mock=args.mock,
        )
        
        all_timings.append(timings)
        
        if 'error' in timings:
            print(f"\n❌ 测试 {i} 失败: {timings['error']}")
        
        # 两次测试之间等待一下，避免速率限制
        if i < args.runs:
            wait_time = 2 if not args.mock else 0.5
            print(f"\n⏳ 等待 {wait_time} 秒后继续下一次测试...")
            await asyncio.sleep(wait_time)
    
    # 打印报告
    print_report(all_timings)


if __name__ == "__main__":
    asyncio.run(main())
