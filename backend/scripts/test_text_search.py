"""Test text-based fallback search"""
import sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

from app.db.session import get_db
from app.services.knowledge_indexer import retrieve_knowledge_chunks

db = next(get_db())

queries = [
    "线程池满了会怎样",
    "synchronized和ReentrantLock有什么区别",
    "volatile有什么用",
    "死锁怎么排查",
    "怎么排查死锁问题",
    "Spring IoC原理",
    "事务隔离级别",
    "索引优化",
]

print("=== 文本降级匹配（无向量）===\n")
for q in queries:
    results = retrieve_knowledge_chunks(
        db, query_text=q, user_id="default-user",
        top_k=3, min_score=0.0
    )
    print("查询: '%s'" % q)
    if results:
        for r in results:
            print("  [%.4f] %s / %s" % (r['similarity_score'], r['document_name'], r['title']))
    else:
        print("  无结果")
    print()

db.close()