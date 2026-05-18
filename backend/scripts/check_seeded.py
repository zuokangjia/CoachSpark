"""Check what was seeded"""
from app.db.session import get_db
from app.db.models import KnowledgeDocument, KnowledgeChunk

db = next(get_db())
docs = db.query(KnowledgeDocument).all()
print(f"文档数: {len(docs)}")
for doc in docs:
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).all()
    has_vec = sum(1 for c in chunks if c.vector is not None)
    print(f"  [{doc.name}] chunks={len(chunks)}, has_vector={has_vec}, category={doc.category}")
    for c in chunks:
        v = "YES" if c.vector else "NO"
        print(f"    - [{c.title}] vector={v} content_len={len(c.content)}")
db.close()