import os
import uuid
import logging
from typing import Any

logger = logging.getLogger(__name__)

_db = None

def _get_db():
    global _db
    if _db is None:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path and os.path.exists(cred_path):
                firebase_admin.initialize_app(credentials.Certificate(cred_path))
            else:
                firebase_admin.initialize_app()
        _db = firestore.client()
        logger.info("Firestore connected")
    return _db

class FirestoreClient:
    def __init__(self, collection: str):
        self.col = collection

    async def create(self, data: dict[str, Any]) -> str:
        doc_id = str(uuid.uuid4())[:8]
        doc = {"id": doc_id, **data}
        _get_db().collection(self.col).document(doc_id).set(doc)
        return doc_id

    async def get(self, doc_id: str) -> dict | None:
        doc = _get_db().collection(self.col).document(doc_id).get()
        return doc.to_dict() if doc.exists else None

    async def update(self, doc_id: str, data: dict[str, Any]) -> None:
        _get_db().collection(self.col).document(doc_id).update(data)

    async def delete(self, doc_id: str) -> None:
        _get_db().collection(self.col).document(doc_id).delete()

    async def list_by_session(self, session_id: str, limit: int = 50) -> list[dict]:
        docs = _get_db().collection(self.col)\
            .where("session_id", "==", session_id)\
            .limit(limit).stream()
        return [d.to_dict() for d in docs]
