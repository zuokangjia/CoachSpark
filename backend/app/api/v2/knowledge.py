"""
Knowledge Base API
知识库管理接口 - 文档导入、语义检索、管理
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import KnowledgeDocument, KnowledgeChunk
from app.services.knowledge_indexer import (
    index_markdown_document,
    retrieve_knowledge_chunks,
    get_document_stats,
    reindex_document,
)
from app.core.logging import logger


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class DocumentResponse(BaseModel):
    id: str
    name: str
    category: str
    source: str
    tags: list[str]
    file_path: str | None
    chunk_count: int
    indexed_count: int
    created_at: str

    model_config = {"from_attributes": True}


class CreateDocumentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="未分类", max_length=100)
    tags: list[str] = Field(default_factory=list)


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    document_name: str
    title: str
    content: str
    concepts: list[str]
    tags: list[str]
    similarity_score: float | None
    category: str

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.2, ge=0.0, le=1.0)
    category: str | None = None


# ============== 文档管理 ==============


@router.get("/documents", response_model=dict[str, Any])
def list_documents(
    category: str | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取知识文档列表"""
    query = db.query(KnowledgeDocument)

    if category:
        query = query.filter(KnowledgeDocument.category == category)

    if search:
        query = query.filter(
            KnowledgeDocument.name.ilike(f"%{search}%")
            | KnowledgeDocument.tags.contains([search])
        )

    total = query.count()
    docs = query.order_by(KnowledgeDocument.created_at.desc()).offset(offset).limit(limit).all()

    def _count_chunks(doc):
        indexed = db.query(KnowledgeChunk.id).filter(
            KnowledgeChunk.document_id == doc.id,
            KnowledgeChunk.vector.isnot(None)
        ).count()
        total_chunks = db.query(KnowledgeChunk.id).filter(
            KnowledgeChunk.document_id == doc.id
        ).count()
        return indexed, total_chunks

    items = []
    for doc in docs:
        indexed, total_chunks = _count_chunks(doc)
        items.append({
            "id": doc.id,
            "name": doc.name,
            "category": doc.category,
            "source": doc.source,
            "tags": doc.tags or [],
            "file_path": doc.file_path,
            "chunk_count": total_chunks,
            "indexed_count": indexed,
            "created_at": doc.created_at.isoformat() if doc.created_at else "",
        })

    return {
        "items": items,
        "total": total,
    }


@router.post("/documents", response_model=dict[str, Any])
def create_document(
    name: str = Form(...),
    category: str = Form(default="未分类"),
    tags: list[str] = Form(default_factory=list),
    file: UploadFile | None = File(None),
    content: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    创建知识文档
    支持两种方式：
    1. 上传 Markdown 文件 (file)
    2. 直接传入 Markdown 内容 (content)
    """
    if file and file.filename:
        # 从上传文件读取内容
        raw_content = file.file.read()
        try:
            text_content = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            text_content = raw_content.decode("gbk", errors="replace")
        file_path = file.filename
    elif content:
        text_content = content
        file_path = None
    else:
        raise HTTPException(status_code=400, detail="必须提供文件或内容")

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="文档内容为空")

    try:
        doc = index_markdown_document(
            db,
            user_id="default-user",
            name=name,
            category=category,
            markdown_text=text_content,
            source="markdown",
            tags=tags,
            file_path=file_path,
        )

        stats = get_document_stats(db, user_id="default-user")

        return {
            "id": doc.id,
            "name": doc.name,
            "category": doc.category,
            "chunk_count": len(doc.chunks),
            "indexed_count": sum(1 for c in doc.chunks if c.vector is not None),
            "message": "文档导入并索引成功",
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"文档导入失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档导入失败: {str(e)}")


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """删除知识文档及其所有 chunks"""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 级联删除由 relationship cascade 处理
    db.delete(doc)
    db.commit()

    return {"message": "文档已删除", "id": document_id}


@router.post("/documents/{document_id}/reindex")
def reindex_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    """重新索引文档"""
    try:
        count = reindex_document(db, document_id=document_id, user_id="default-user")
        return {"message": f"重新索引完成", "document_id": document_id, "reindexed_chunks": count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新索引失败: {str(e)}")


# ============== 语义搜索 ==============


@router.post("/search", response_model=dict[str, Any])
def search_knowledge(request: SearchRequest, db: Session = Depends(get_db)):
    """
    知识库语义搜索

    基于向量相似度检索相关文档片段。
    """
    results = retrieve_knowledge_chunks(
        db,
        query_text=request.query,
        user_id="default-user",
        top_k=request.top_k,
        min_score=request.min_score,
        category=request.category,
    )

    return {
        "query": request.query,
        "result_count": len(results),
        "results": results,
    }


@router.get("/categories", response_model=dict[str, Any])
def list_categories(db: Session = Depends(get_db)):
    """获取文档分类统计"""
    categories = (
        db.query(
            KnowledgeDocument.category,
            func.count(KnowledgeDocument.id).label("count"),
            func.count(KnowledgeChunk.id.distinct()).label("chunk_count"),
        )
        .outerjoin(KnowledgeChunk)
        .group_by(KnowledgeDocument.category)
        .all()
    )

    return {
        "categories": [
            {
                "name": cat,
                "documents": count,
                "chunks": chunk_count,
            }
            for cat, count, chunk_count in categories
        ]
    }


# ============== 文档统计 ==============


@router.get("/stats", response_model=dict[str, Any])
def knowledge_stats(db: Session = Depends(get_db)):
    """获取知识库统计概览"""
    stats = get_document_stats(db, user_id="default-user")
    return stats