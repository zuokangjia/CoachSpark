"""
RAG Pipeline Integration Test
完整的知识库 RAG 流程测试
"""

import asyncio
import json
import os
import sys

# Force UTF-8 output for Windows terminals
if os.name == 'nt':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

from app.db.session import get_db
from app.services.knowledge_indexer import (
    index_markdown_document,
    retrieve_knowledge_chunks,
    get_document_stats,
    parse_markdown_sections,
    _flatten_sections_for_chunks,
)
from app.services.practice_service import generate_topic_drill_questions
from app.db.models import generate_uuid


def test_1_parse_markdown():
    """测试1: Markdown解析能力"""
    print("=" * 60)
    print("TEST 1: Markdown 解析")
    print("=" * 60)

    md = """# Java并发编程

## 线程基础

线程是操作系统调度的最小单位。

## synchronized关键字

synchronized是Java内置的互斥锁，支持可重入。

## volatile关键字

volatile保证变量的可见性和有序性。

## 线程池

核心参数：corePoolSize, maximumPoolSize。
"""
    sections = parse_markdown_sections(md)
    chunks = _flatten_sections_for_chunks(sections)

    print(f"解析出 {len(sections)} 个章节, {len(chunks)} 个知识块\n")
    for i, chunk in enumerate(chunks):
        print(f"  [{i}] {chunk.title}")
        print(f"      内容: {chunk.content[:60]}...")
        print(f"      概念: {chunk.concepts}")
        print()

    expected = len(chunks) >= 4
    print(f"结果: {'PASS' if expected else 'FAIL'} (期望>=4个chunk, 实际={len(chunks)})")
    return expected


def test_2_index_document():
    """测试2: 文档索引和嵌入"""
    print("\n" + "=" * 60)
    print("TEST 2: 文档索引")
    print("=" * 60)

    db = next(get_db())

    doc = index_markdown_document(
        db,
        user_id="default-user",
        name="Java并发编程详解",
        category="Java",
        tags=["并发", "多线程", "JVM", "面试"],
        markdown_text="""# Java并发编程

## 线程基础

Java中创建线程有3种方式：继承Thread类、实现Runnable接口、实现Callable接口。
推荐使用线程池来管理线程生命周期，避免频繁创建销毁线程的开销。

## synchronized关键字

synchronized是Java内置的互斥锁，支持可重入。每个对象都有一个内置锁（monitor）。
修饰方法时锁住的是对象实例（this），修饰静态方法时锁住的是Class对象。

## volatile关键字

volatile保证变量的可见性和有序性，但不保证原子性。
适用于状态标记变量、单次安全发布等场景。

## JUC并发工具

### CountDownLatch
允许一个或多个线程等待其他线程完成操作。

### CyclicBarrier
让一组线程互相等待到达一个屏障点。

### Semaphore
控制同时访问特定资源的线程数量，常用于限流。

## 线程池

### ThreadPoolExecutor
核心参数：corePoolSize, maximumPoolSize, keepAliveTime, workQueue, handler。
拒绝策略包括AbortPolicy, CallerRunsPolicy, DiscardPolicy, DiscardOldestPolicy。

## 死锁与排查

死锁产生的4个必要条件：互斥、持有并等待、不可剥夺、循环等待。
使用jstack可以导出线程栈信息来排查死锁。
""",
    )

    print(f"文档ID: {doc.id}")
    print(f"文档名称: {doc.name}")
    print(f"包含 {len(doc.chunks)} 个知识块\n")

    for chunk in doc.chunks:
        vlen = len(chunk.vector) if chunk.vector else 0
        print(f"  - [{chunk.title}] vector={'OK' if chunk.vector else 'MISSING'} dim={vlen}")

    success = len(doc.chunks) >= 4
    print(f"\n结果: {'PASS' if success else 'FAIL'} (期望>=4个chunk, 实际={len(doc.chunks)})")

    doc_id = doc.id
    db.close()
    return doc_id, success


def test_3_semantic_search():
    """测试3: 语义搜索"""
    print("\n" + "=" * 60)
    print("TEST 3: 语义搜索")
    print("=" * 60)

    db = next(get_db())

    queries = [
        ("线程池满了会怎样", "线程池拒绝策略"),
        ("synchronized和ReentrantLock区别", "锁机制对比"),
        ("volatile有什么用", "volatile语义"),
        ("死锁怎么排查", "死锁问题"),
    ]

    all_pass = True
    for query, desc in queries:
        print(f"\n  查询: '{query}' ({desc})")
        print("  " + "-" * 40)
        results = retrieve_knowledge_chunks(
            db,
            query_text=query,
            user_id="default-user",
            top_k=3,
            min_score=0.0,
        )
        if results:
            for r in results:
                print(f"    [{r['similarity_score']:.4f}] {r['title']}")
        else:
            print("    无结果")
            all_pass = False

    # 不相干查询应该得到低分
    results_cook = retrieve_knowledge_chunks(
        db, query_text="怎么做红烧肉",
        user_id="default-user", top_k=1, min_score=0.0
    )
    if results_cook and results_cook[0]['similarity_score'] < 0.3:
        print(f"\n  不相干查询相似度 {results_cook[0]['similarity_score']:.4f} < 0.3: OK")
    else:
        score = results_cook[0]['similarity_score'] if results_cook else 'N/A'
        print(f"\n  不相干查询相似度 {score}")

    db.close()
    return all_pass


def test_4_stats():
    """测试4: 统计"""
    print("\n" + "=" * 60)
    print("TEST 4: 知识库统计")
    print("=" * 60)

    db = next(get_db())
    stats = get_document_stats(db, user_id="default-user")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    success = stats['total_documents'] > 0 and stats['total_chunks'] > 0
    print(f"\n结果: {'PASS' if success else 'FAIL'}")
    db.close()
    return success


async def test_5_rag_generate_questions():
    """测试5: RAG驱动的题目生成"""
    print("\n" + "=" * 60)
    print("TEST 5: RAG驱动专项练习生成")
    print("=" * 60)

    db = next(get_db())

    # 确保有技能状态
    from app.db.models import UserSkillState
    existing = db.query(UserSkillState).filter(
        UserSkillState.user_id == "default-user",
        UserSkillState.dimension == "Java"
    ).first()
    if not existing:
        state = UserSkillState(
            id=generate_uuid(),
            user_id="default-user",
            dimension="Java",
            level=2,
            confidence=60,
        )
        db.add(state)
        db.commit()
        print("  已创建 Java 技能状态 (level=2)")

    try:
        result = await generate_topic_drill_questions(
            db, topic="Java", user_id="default-user", num_questions=2
        )
        print(f"  专题: {result['topic']}")
        print(f"  用户等级: {result['user_level']}")
        print(f"  生成题目数: {result['generated_count']}")
        print(f"  练习ID: {result['drill_id']}")
        for q in result['questions']:
            print(f"    - [{q['difficulty']}星] {q['title']}")
        success = True
    except Exception as e:
        print(f"  生成失败: {e}")
        import traceback
        traceback.print_exc()
        success = False

    db.close()
    return success


def test_6_api_endpoints():
    """测试6: API端点连通性"""
    print("\n" + "=" * 60)
    print("TEST 6: API端点连通性")
    print("=" * 60)

    db = next(get_db())

    # 测试 categories endpoint
    from app.api.v2.knowledge import router
    categories = [r for r in router.routes if hasattr(r, 'endpoint')]
    print(f"  已注册路由数: {len(categories)}")
    for r in router.routes:
        if hasattr(r, 'methods') and hasattr(r, 'path'):
            print(f"    {list(r.methods)} {r.path}")

    success = len(categories) > 0
    print(f"\n结果: {'PASS' if success else 'FAIL'}")
    db.close()
    return success


if __name__ == "__main__":

    tests = [
        ("1. Markdown解析", test_1_parse_markdown, False),
        ("2. 文档索引", test_2_index_document, False),
        ("3. 语义搜索", test_3_semantic_search, False),
        ("4. 知识库统计", test_4_stats, False),
        ("5. RAG题目生成", test_5_rag_generate_questions, True),
        ("6. API路由", test_6_api_endpoints, False),
    ]

    if len(sys.argv) > 1:
        test_num = sys.argv[1]
        for name, fn, is_async in tests:
            if test_num in name:
                print(f"\n运行: {name}\n")
                result = fn()
                if is_async:
                    result = asyncio.run(result)
                exit(0 if result else 1)
    else:
        results = {}
        for name, fn, is_async in tests:
            print(f"\n运行: {name}\n")
            try:
                result = fn()
                if is_async:
                    result = asyncio.run(result)
                results[name] = result
                status = "PASS" if result else "FAIL"
                print(f"状态: {status}")
            except Exception as e:
                print(f"异常: {e}")
                import traceback
                traceback.print_exc()
                results[name] = False

        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        for name, ok in results.items():
            sign = "PASS" if ok else "FAIL"
            print(f"  [{sign}] {name}")
        passed = sum(1 for v in results.values() if v)
        print(f"\n总计: {passed}/{len(results)} 项通过")