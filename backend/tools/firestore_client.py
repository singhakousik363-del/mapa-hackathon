import uuid
from typing import Any

_store: dict = {}

class FirestoreClient:
    def __init__(self, collection: str):
        self.col = collection
        _store.setdefault(collection, {})

    async def create(self, data: dict[str, Any]) -> str:
        doc_id = str(uuid.uuid4())[:8]
        _store[self.col][doc_id] = {"id": doc_id, **data}
        return doc_id

    async def get(self, doc_id: str) -> dict | None:
        return _store[self.col].get(doc_id)

    async def update(self, doc_id: str, data: dict[str, Any]) -> None:
        if doc_id in _store[self.col]:
            _store[self.col][doc_id].update(data)

    async def delete(self, doc_id: str) -> None:
        _store[self.col].pop(doc_id, None)

    async def list_by_session(self, session_id: str, limit: int = 50) -> list[dict]:
        return [v for v in _store[self.col].values()
                if v.get("session_id") == session_id][:limit]
