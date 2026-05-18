"""
Knowledge Indexer Service
知识库索引服务 - Markdown 文档解析、分块、嵌入、向量检索

参考 TechSpar 的文件结构:
  data/knowledge/{user_id}/{topic}/{filename}.md

但数据库模型使用 CoachSpark 的 SQLAlchemy 模式:
  KnowledgeDocument -> KnowledgeChunk (一对多)

处理流程:
  1. 解析 Markdown 文件为层级结构 (Document > Sections > Chunks)
  2. 对每个 Chunk 生成 embedding 向量
  3. 存储到 KnowledgeChunk.vector 列
  4. 提供语义搜索接口 retrieve_knowledge_chunks()
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.llm import get_embedder
from app.config import settings
from app.db.models import KnowledgeDocument, KnowledgeChunk

logger = logging.getLogger(__name__)

# Markdown 解析配置
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
# 细粒度分割：一级和二级标题都作为 chunk 边界
CHUNK_SPLIT_LEVELS = {1, 2}

# 嵌入配置
EMBED_BATCH_SIZE = 16
EMBED_RETRY_TIMES = 3
EMBED_RETRY_DELAY = 1.0
MIN_CHUNK_LENGTH = 40  # 最小 chunk 长度，过短则合并到相邻块


@dataclass
class MarkdownSection:
    """Markdown 解析后的一个章节"""
    level: int  # 标题级别 1-6
    title: str  # 标题文本
    content: str  # 该标题下的完整文本（含子标题内容）
    children: list["MarkdownSection"]  # 子章节
    order_index: int  # 全局顺序


@dataclass
class ParsedChunk:
    """解析后的知识块，待嵌入"""
    title: str
    content: str
    order_index: int
    concepts: list[str] = None  # 从标题提取的关键概念

    def __post_init__(self):
        if self.concepts is None:
            self.concepts = []


# ============================================================================
# Markdown 解析
# ============================================================================

def parse_markdown_sections(text: str) -> list[MarkdownSection]:
    """
    将 Markdown 文本解析为层级章节结构。
    算法：扫描所有标题行，维护一个栈来追踪当前层级关系。
    """
    lines = text.split("\n")
    sections: list[MarkdownSection] = []
    stack: list[MarkdownSection] = []  # 维护当前路径的栈
    order_counter = 0

    # 将内容行分配到最近的一个标题下
    pending_content: list[str] = []

    def flush_pending(parent_section: MarkdownSection | None):
        """将 pending_content 写入当前栈顶章节的内容中"""
        nonlocal pending_content
        if pending_content and parent_section is not None:
            parent_section.content += "\n".join(pending_content) + "\n"
        pending_content = []

    for line in lines:
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            order_counter += 1

            new_section = MarkdownSection(
                level=level,
                title=title,
                content="",
                children=[],
                order_index=order_counter,
            )

            # 先 flush pending 到当前栈顶（弹出前）
            if pending_content and stack:
                stack[-1].content += "\n".join(pending_content) + "\n"
            pending_content = []

            # 弹出栈中级别 >= 当前级别的节点
            while stack and stack[-1].level >= level:
                stack.pop()

            if stack:
                stack[-1].children.append(new_section)
            else:
                sections.append(new_section)

            stack.append(new_section)
        else:
            pending_content.append(line)

    # 处理末尾剩余内容
    if pending_content and stack:
        stack[-1].content += "\n".join(pending_content) + "\n"
    pending_content = []

    return sections


def _flatten_sections_for_chunks(
    sections: list[MarkdownSection],
    chunks: list[ParsedChunk] | None = None,
    parent_titles: list[str] | None = None,
) -> list[ParsedChunk]:
    """
    将层级章节展平为适合作为知识块的列表。
    算法（先序遍历）：
      - 遇到 split-level 节点：收集"自身内容 + 非 split 子节点内容"为 1 个 chunk，
        然后递归处理其 split-level 子节点创建独立 chunk。
      - 遇到非 split-level 节点：内容合并到上一个 chunk，若无则独立创建。
    后处理：对内容过短的相邻同级 chunk 执行合并（仅合并 < MIN_CHUNK_LENGTH 且属于同一父级）。
    """
    if chunks is None:
        chunks = []
    if parent_titles is None:
        parent_titles = []

    for section in sections:
        current_titles = parent_titles + [section.title]

        if section.level in CHUNK_SPLIT_LEVELS:
            parts: list[str] = []
            if section.content.strip():
                parts.append(section.content.strip())
            _collect_non_split_content(section, parts)
            content = "\n\n".join(p for p in parts if p.strip())

            if content:
                chunks.append(ParsedChunk(
                    title=section.title,
                    content=content,
                    order_index=section.order_index,
                    concepts=_extract_concepts_from_title(section.title),
                ))

            child_splits = [
                c for c in (section.children or [])
                if c.level in CHUNK_SPLIT_LEVELS
            ]
            if child_splits:
                _flatten_sections_for_chunks(child_splits, chunks, current_titles)
        else:
            content = section.content.strip()
            if not content:
                if section.children:
                    _flatten_sections_for_chunks(section.children, chunks, current_titles)
                continue

            if chunks:
                chunks[-1].content += "\n\n" + content
            else:
                chunks.append(ParsedChunk(
                    title=section.title or "概述",
                    content=content,
                    order_index=section.order_index,
                    concepts=_extract_concepts_from_title(section.title),
                ))

            if section.children:
                _flatten_sections_for_chunks(section.children, chunks, current_titles)

    # 后处理：仅合并相邻且过小的 chunk（保留一定颗粒度）
    chunks = _merge_small_chunks(chunks)
    return chunks


def _merge_small_chunks(chunks: list[ParsedChunk]) -> list[ParsedChunk]:
    """
    合并内容过短的 chunk（阈值 MIN_CHUNK_LENGTH）。
    策略：将短 chunk 合并到下一个 chunk，形成合理的知识块。
    只在内容确实很薄时合并，避免损失太多语义区分度。
    """
    if len(chunks) <= 1:
        return chunks

    result: list[ParsedChunk] = []
    i = 0
    while i < len(chunks):
        current = chunks[i]
        # 如果当前 chunk 过短且不是最后一个，尝试与下一个合并
        if len(current.content) < MIN_CHUNK_LENGTH and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            next_chunk.content = current.content + "\n\n" + next_chunk.content
            next_chunk.order_index = current.order_index
            # 合并标题
            if current.title and current.title != next_chunk.title:
                next_chunk.title = current.title + " / " + next_chunk.title
            # 合并 concepts
            for c in (current.concepts or []):
                if c not in next_chunk.concepts:
                    next_chunk.concepts.append(c)
            # 跳过 current，i+1 会在下一轮处理
            i += 1
            continue
        result.append(current)
        i += 1

    return result if result else chunks


def _collect_non_split_content(section: MarkdownSection, parts: list[str]) -> None:
    """递归收集 section 中所有非 split-level 子节点的 content。"""
    for child in section.children or []:
        if child.level not in CHUNK_SPLIT_LEVELS:
            content = child.content.strip()
            if content:
                parts.append(content)
            # 继续向下（跳过 split-level 节点）
            _collect_non_split_content(child, parts)


def _extract_concepts_from_title(title: str) -> list[str]:
    """从标题中提取关键概念（简单实现：基于分隔符拆分）"""
    concepts = []
    # 移除 Markdown 格式标记
    title = re.sub(r"[*_`~\[\]]", "", title)
    # 按常见分隔符拆分
    parts = re.split(r"[、,，;；/、\s]+", title)
    for part in parts:
        part = part.strip()
        if len(part) >= 2 and len(part) <= 20:
            concepts.append(part)
    return concepts


# ============================================================================
# 向量化 & 存储
# ============================================================================

def _embed_with_retry(texts: list[str], embedder) -> list[list[float] | None]:
    """批量嵌入，带重试逻辑"""
    for attempt in range(EMBED_RETRY_TIMES):
        try:
            return embedder.embed_documents(texts)
        except Exception as e:
            logger.warning(f"批量嵌入失败（第 {attempt + 1}/{EMBED_RETRY_TIMES} 次）: {e}")
            if attempt < EMBED_RETRY_TIMES - 1:
                import time
                time.sleep(EMBED_RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"批量嵌入最终失败，已达最大重试次数")
                return [None] * len(texts)
    return [None] * len(texts)


def index_markdown_document(
    db: Session,
    *,
    user_id: str,
    name: str,
    category: str,
    markdown_text: str,
    source: str = "markdown",
    tags: list[str] | None = None,
    file_path: str | None = None,
) -> KnowledgeDocument:
    """
    完整的知识文档索引流程：
    1. 解析 Markdown
    2. 创建 KnowledgeDocument 记录
    3. 创建 KnowledgeChunk 记录
    4. 批量生成嵌入向量
    5. 保存到数据库
    """
    if tags is None:
        tags = []

    # 1. 解析 Markdown
    sections = parse_markdown_sections(markdown_text)
    chunks_data = _flatten_sections_for_chunks(sections)

    if not chunks_data:
        # 如果没有分割出 chunk，至少创建一个包含全部内容的 chunk
        chunks_data = [
            ParsedChunk(
                title=name,
                content=markdown_text.strip(),
                order_index=1,
            )
        ]

    logger.info(f"Markdown 解析完成: {len(chunks_data)} 个知识块")

    # 2. 创建 Document 记录
    doc = KnowledgeDocument(
        user_id=user_id,
        name=name,
        category=category,
        source=source,
        tags=tags,
        file_path=file_path,
    )
    db.add(doc)
    db.flush()  # 获取 doc.id

    # 3. 创建 Chunk 记录
    embed_texts: list[str] = []
    chunk_records: list[KnowledgeChunk] = []

    for idx, chunk_data in enumerate(chunks_data):
        chunk = KnowledgeChunk(
            document_id=doc.id,
            title=chunk_data.title,
            content=chunk_data.content,
            order_index=chunk_data.order_index,
            concepts=chunk_data.concepts,
            tags=tags,
        )
        db.add(chunk)
        chunk_records.append(chunk)

        # 准备嵌入文本：标题 + 内容
        embed_text = chunk_data.title + "\n" + chunk_data.content
        embed_texts.append(embed_text)

    db.flush()

    # 4. 批量嵌入
    if embed_texts:
        embedder = get_embedder()
        vectors = _embed_with_retry(embed_texts, embedder)

        for chunk, vec in zip(chunk_records, vectors):
            if vec is not None and len(vec) > 0:
                chunk.vector = vec
            else:
                logger.warning(f"Chunk {chunk.id} 嵌入失败，跳过向量化")

    db.commit()
    logger.info(f"文档 '{name}' 索引完成: {len(chunk_records)} 个知识块")

    return doc


# ============================================================================
# 语义搜索
# ============================================================================

def _title_boost_score(query_text: str, title: str, concepts: list[str]) -> float:
    """
    标题/概念匹配加成：当查询文本直接命中标题或关键概念时给予额外加权。
    这解决"查询精确匹配标题但向量相似度低"的问题。
    """
    if not title:
        return 0.0

    # 标题中关键词在查询中的占比
    title_words = set(re.findall(r"\w+", title.lower()))
    query_words = set(re.findall(r"\w+", query_text.lower()))

    if not query_words:
        return 0.0

    overlap = len(title_words & query_words)
    if overlap == 0:
        # 检查概念
        for concept in concepts:
            concept_words = set(re.findall(r"\w+", concept.lower()))
            if concept_words & query_words:
                return 0.15
        return 0.0

    ratio = overlap / len(query_words)
    # 标题完全覆盖查询词给最高加成
    return 0.25 * min(ratio * 2, 1.0)


def _apply_title_boost(score: float, boost: float) -> float:
    """
    将标题加成融合到原始余弦相似度中。
    公式: final = cosine_weight * score + title_weight * boost
    保证最终分数仍在 [0, 1] 范围内。
    """
    cosine_weight = 0.75
    title_weight = 0.25
    return cosine_weight * score + title_weight * boost


def retrieve_knowledge_chunks(
    db: Session,
    *,
    query_text: str,
    user_id: str = "default-user",
    top_k: int = 10,
    min_score: float = 0.2,
    category: str | None = None,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    知识库语义搜索（带标题加权）

    Args:
        query_text: 查询文本
        user_id: 用户ID
        top_k: 返回结果数量
        min_score: 最低综合分数阈值
        category: 按分类过滤
        document_id: 按文档ID过滤

    Returns:
        按综合分数排序的结果列表
    """
    embedder = get_embedder()

    # 生成查询向量
    query_vec = None
    for attempt in range(3):
        try:
            query_vec = embedder.embed_query(query_text)
            break
        except Exception as e:
            logger.warning(f"查询向量生成失败（第 {attempt + 1} 次）: {e}")
            if attempt < 2:
                import time
                time.sleep(1.0 * (attempt + 1))

    if query_vec is None:
        logger.error("查询向量生成失败，返回空结果")
        return []

    # 构建查询
    query = (
        db.query(KnowledgeChunk)
        .join(KnowledgeDocument)
        .filter(KnowledgeDocument.user_id == user_id)
    )

    if category:
        query = query.filter(KnowledgeDocument.category == category)

    if document_id:
        query = query.filter(KnowledgeChunk.document_id == document_id)

    chunks = query.all()

    if not chunks:
        return []

    # 计算综合分数 = 0.75 * 余弦相似度 + 0.25 * 标题加成
    candidates: list[tuple[float, KnowledgeChunk]] = []

    for chunk in chunks:
        if chunk.vector is None:
            # 无向量的 chunk 使用文本启发式匹配
            sim_score = _text_similarity(query_text, chunk.content)
        else:
            sim_score = _cosine_similarity(query_vec, chunk.vector)

        # 标题加成
        boost = _title_boost_score(query_text, chunk.title, chunk.concepts or [])
        final_score = _apply_title_boost(sim_score, boost)

        if sim_score >= min_score or boost > 0.1:
            candidates.append((final_score, chunk))

    # 按综合分数降序排序
    candidates.sort(key=lambda x: x[0], reverse=True)

    # 返回 top_k
    results = []
    for score, chunk in candidates[:top_k]:
        results.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_name": chunk.document.name,
            "title": chunk.title,
            "content": chunk.content,
            "concepts": chunk.concepts,
            "category": chunk.document.category,
            "similarity_score": round(score, 4),
        })

    return results


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    if len(a) != len(b):
        logger.warning(f"向量维度不匹配: {len(a)} vs {len(b)}")
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def _text_similarity(query: str, text: str) -> float:
    """
    文本关键词重叠度（降级用，当向量不可用时）
    """
    if not query or not text:
        return 0.0

    # 简单的分词：按标点和空格分割
    q_words = set(re.findall(r"\w+", query.lower()))
    t_words = set(re.findall(r"\w+", text.lower()))

    if not q_words:
        return 0.0

    overlap = len(q_words & t_words)
    return overlap / len(q_words)


# ============================================================================
# 批量索引 & 管理
# ============================================================================

def reindex_document(
    db: Session,
    *,
    document_id: str,
    user_id: str = "default-user",
) -> int:
    """
    重新索引一个文档的所有 chunks
    Returns: 成功重新嵌入的 chunk 数量
    """
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.user_id == user_id,
    ).first()

    if doc is None:
        raise ValueError(f"文档 {document_id} 不存在或不属于用户 {user_id}")

    chunks = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.document_id == document_id
    ).all()

    if not chunks:
        return 0

    embedder = get_embedder()
    texts = [chunk.title + "\n" + chunk.content for chunk in chunks]

    vectors = _embed_with_retry(texts, embedder)
    count = 0

    for chunk, vec in zip(chunks, vectors):
        if vec is not None and len(vec) > 0:
            chunk.vector = vec
            count += 1

    if count > 0:
        db.commit()
        logger.info(f"文档 {document_id} 重新索引完成: {count}/{len(chunks)} 个 chunks")

    return count


def get_document_stats(db: Session, *, user_id: str = "default-user") -> dict[str, Any]:
    """
    获取知识库统计信息
    """
    total_docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.user_id == user_id
    ).count()

    total_chunks = db.query(KnowledgeChunk).join(
        KnowledgeDocument
    ).filter(KnowledgeDocument.user_id == user_id).count()

    indexed_chunks = db.query(func.count(KnowledgeChunk.id)).join(
        KnowledgeDocument
    ).filter(
        KnowledgeDocument.user_id == user_id,
        KnowledgeChunk.vector.isnot(None),
    ).scalar()

    categories = db.query(
        KnowledgeDocument.category,
        func.count(KnowledgeDocument.id),
    ).filter(
        KnowledgeDocument.user_id == user_id
    ).group_by(KnowledgeDocument.category).all()

    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "indexed_chunks": indexed_chunks,
        "index_rate": round(indexed_chunks / total_chunks, 2) if total_chunks > 0 else 0,
        "categories": {cat: count for cat, count in categories},
    }