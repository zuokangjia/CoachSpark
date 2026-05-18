"""Debug markdown parser"""
import sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

from app.services.knowledge_indexer import parse_markdown_sections, _flatten_sections_for_chunks

md = """# Java并发编程

## 线程基础

Java中创建线程有3种方式。

## synchronized关键字

synchronized是Java内置的互斥锁。

## volatile关键字

volatile保证变量的可见性。

## JUC并发工具

### CountDownLatch
允许线程等待。

### CyclicBarrier
让线程互相等待。

## 线程池

核心参数：corePoolSize。

## 死锁与排查

死锁产生的必要条件。
"""

print("=== Raw sections ===")
sections = parse_markdown_sections(md)
for s in sections:
    print(f"  Level {s.level}: '{s.title}' content_len={len(s.content)} children={len(s.children)}")
    for c in s.children:
        print(f"    Level {c.level}: '{c.title}' content_len={len(c.content)} children={len(c.children)}")
        for cc in c.children:
            print(f"      Level {cc.level}: '{cc.title}' content_len={len(cc.content)}")

print("\n=== Flattened chunks ===")
chunks = _flatten_sections_for_chunks(sections)
print(f"Total chunks: {len(chunks)}")
for i, c in enumerate(chunks):
    print(f"  [{i}] '{c.title}' content_len={len(c.content)} concepts={c.concepts}")
    print(f"      content: {c.content[:80]}...")