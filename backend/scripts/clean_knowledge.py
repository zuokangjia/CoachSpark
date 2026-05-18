"""Clean knowledge base test data"""
from app.db.session import get_db
from app.db.models import KnowledgeDocument, KnowledgeChunk, GeneratedQuestion, Drill, DrillSession

db = next(get_db())
db.query(DrillSession).delete()
db.query(Drill).delete()
db.query(GeneratedQuestion).delete()
db.query(KnowledgeChunk).delete()
db.query(KnowledgeDocument).delete()
db.commit()
db.close()
print("Cleaned")