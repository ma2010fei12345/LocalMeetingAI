import json
import math
import os
import sqlite3
from collections import Counter

from .config import CHROMA_DIR


class ProjectVectorStore:
    def __init__(self) -> None:
        self._chroma_client = None
        use_chroma = os.getenv("LOCALMEETINGAI_USE_CHROMA", "0") == "1"
        try:
            import chromadb

            if use_chroma:
                self._chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        except Exception:
            self._chroma_client = None

    def _collection_name(self, project_id: int) -> str:
        return f"project_{project_id}"

    def add_chunks(self, project_id: int, document_id: int, filename: str, chunks: list[str]) -> None:
        if not chunks:
            return
        if self._chroma_client:
            collection = self._chroma_client.get_or_create_collection(self._collection_name(project_id))
            ids = [f"{project_id}:{document_id}:{idx}" for idx in range(len(chunks))]
            metadatas = [
                {"project_id": project_id, "document_id": document_id, "filename": filename, "chunk_index": idx}
                for idx in range(len(chunks))
            ]
            collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
            return
        self._add_sqlite_chunks(project_id, document_id, filename, chunks)

    def search(self, project_id: int, query: str, limit: int = 5) -> list[dict]:
        if not query.strip():
            return []
        if self._chroma_client:
            collection = self._chroma_client.get_or_create_collection(self._collection_name(project_id))
            result = collection.query(query_texts=[query], n_results=limit)
            docs = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0] if result.get("distances") else []
            return [
                {
                    "text": doc,
                    "filename": meta.get("filename", ""),
                    "score": 1 / (1 + distances[idx]) if idx < len(distances) else 0,
                }
                for idx, (doc, meta) in enumerate(zip(docs, metadatas))
            ]
        return self._search_sqlite(project_id, query, limit)

    def _add_sqlite_chunks(self, project_id: int, document_id: int, filename: str, chunks: list[str]) -> None:
        from .db import DB_PATH

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                create table if not exists vector_chunks (
                    id text primary key,
                    project_id integer not null,
                    document_id integer not null,
                    filename text not null,
                    text text not null,
                    tokens text not null
                )
                """
            )
            for idx, chunk in enumerate(chunks):
                row_id = f"{project_id}:{document_id}:{idx}"
                conn.execute(
                    "insert or replace into vector_chunks(id, project_id, document_id, filename, text, tokens) values (?, ?, ?, ?, ?, ?)",
                    (row_id, project_id, document_id, filename, chunk, json.dumps(_tokens(chunk), ensure_ascii=False)),
                )

    def _search_sqlite(self, project_id: int, query: str, limit: int) -> list[dict]:
        from .db import DB_PATH

        query_tokens = _tokens(query)
        if not query_tokens:
            return []
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "select filename, text, tokens from vector_chunks where project_id = ?",
                (project_id,),
            ).fetchall()
        scored = []
        for row in rows:
            score = _cosine(query_tokens, Counter(json.loads(row["tokens"])))
            if score > 0:
                scored.append({"filename": row["filename"], "text": row["text"], "score": score})
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]


def _tokens(text: str) -> Counter:
    chars = [ch.lower() for ch in text if ch.isalnum() or "\u4e00" <= ch <= "\u9fff"]
    grams = chars + ["".join(chars[i : i + 2]) for i in range(max(0, len(chars) - 1))]
    return Counter(grams)


def _cosine(a: Counter, b: Counter) -> float:
    common = set(a) & set(b)
    numerator = sum(a[key] * b[key] for key in common)
    if numerator == 0:
        return 0.0
    left = math.sqrt(sum(value * value for value in a.values()))
    right = math.sqrt(sum(value * value for value in b.values()))
    return numerator / (left * right)
