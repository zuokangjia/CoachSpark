"""
ProfileEvidence 向量数据校验与修复脚本

功能：
1. 检查所有现有记录的向量状态（缺失/维度异常/有效）
2. 清理维度异常的向量（标记为失效，下次自动补全）
3. 对缺失/失效的向量进行重新嵌入
4. 生成数据健康报告

用法：
  python scripts/verify_and_reembed_evidence.py        # 检查 + 修复
  python scripts/verify_and_reembed_evidence.py --dry   # 仅检查，不修改任何数据
  python scripts/verify_and_reembed_evidence.py --clean # 清理异常向量后退出（不重新嵌入）
"""

from __future__ import annotations

import argparse
import sys
import time

# 将项目根目录加入路径
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.db.models import ProfileEvidence
from app.services.rag_retrieval_service import (
    embed_evidence_texts,
    _validate_vector,
    _get_vector,
    VECTOR_DIMENSION,
)


def analyze_records(db) -> dict:
    """分析所有 ProfileEvidence 记录的向量状态，返回统计。"""
    records = db.query(ProfileEvidence).all()

    stats = {
        "total": len(records),
        "has_vector": 0,
        "missing_vector": 0,
        "invalid_dimension": 0,
        "empty_text": 0,
    }

    invalid_ids: list[str] = []

    for r in records:
        text = r.quote_text or ""
        if not text.strip():
            stats["empty_text"] += 1
            continue

        vec = _get_vector(r)
        if vec is None:
            stats["missing_vector"] += 1
        elif not _validate_vector(vec):
            stats["invalid_dimension"] += 1
            invalid_ids.append(r.id)
        else:
            stats["has_vector"] += 1

    return {"stats": stats, "invalid_ids": invalid_ids}


def print_report(stats: dict):
    """打印数据健康报告。"""
    print("\n" + "=" * 50)
    print("  ProfileEvidence Vector Data Health Report")
    print("=" * 50)
    print(f"  Total records:        {stats['total']}")
    print(f"  Valid vectors:        {stats['has_vector']}")
    print(f"  Missing vectors:      {stats['missing_vector']}")
    print(f"  Invalid dimension:    {stats['invalid_dimension']}")
    print(f"  Empty text (skipped): {stats['empty_text']}")
    print("-" * 50)

    if stats['invalid_dimension'] > 0:
        health = "WARNING - invalid data found, needs cleanup"
    elif stats['missing_vector'] > 0:
        health = "WARNING - partial missing vectors, recommend re-embed"
    elif stats['has_vector'] == stats['total']:
        health = "OK - all healthy"
    print(f"  Health status:        {health}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="ProfileEvidence Vector Verification & Repair")
    parser.add_argument("--dry", action="store_true", help="Check only, do not modify data")
    parser.add_argument("--clean", action="store_true", help="Clean invalid vectors only, do not re-embed")
    args = parser.parse_args()

    db = SessionLocal()

    print("\n[1] Analyzing ProfileEvidence vector data...")
    result = analyze_records(db)
    stats = result["stats"]
    invalid_ids = result["invalid_ids"]

    print_report(stats)

    if args.dry:
        print("[DRY MODE] No modifications made.")
        return

    # 清理异常维度向量
    if invalid_ids:
        print(f"\n[2] Cleaning {len(invalid_ids)} dimension-invalid vectors...")
        for record in db.query(ProfileEvidence).filter(ProfileEvidence.id.in_(invalid_ids)).all():
            from app.config import settings
            if settings.use_pgvector:
                record.vector = None
            else:
                metadata = dict(record.metadata_json or {})
                key = f"embedding_{record.id}"
                if key in metadata:
                    del metadata[key]
                    record.metadata_json = metadata
        db.commit()
        print(f"    Cleaned {len(invalid_ids)} invalid vectors (marked for re-embed)")

    if args.clean:
        print("[CLEAN MODE] Cleanup done, exiting.")
        return

    # 重新嵌入
    missing_or_invalid = stats["missing_vector"] + stats["invalid_dimension"]
    if missing_or_invalid > 0:
        print(f"\n[3] Re-embedding {missing_or_invalid} missing/invalid records...")
        start = time.time()
        count = embed_evidence_texts(db)
        elapsed = time.time() - start
        print(f"    Re-embedded {count} records in {elapsed:.1f}s")
    else:
        print("\n[3] No re-embedding needed, data is complete.")

    # 重新分析
    print("\n[4] Verifying final data state...")
    result2 = analyze_records(db)
    print_report(result2["stats"])


if __name__ == "__main__":
    main()
