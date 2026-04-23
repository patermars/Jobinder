import chromadb
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, CHROMA_COLLECTION


class RAGEngine:
    def __init__(self):
        self._model = None
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )

    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        return self._model

    def index_jobs(self, jobs: list[dict]):
        docs, ids, metas = [], [], []
        for job in jobs:
            doc = f"{job['title']} at {job['company']}. {job['description']}. Requirements: {', '.join(job.get('requirements', []))}"
            docs.append(doc)
            ids.append(job.get("id", f"job_{len(ids)}"))
            metas.append({
                "title": job.get("title") or "",
                "company": job.get("company") or "",
                "location": job.get("location") or "",
                "salary_range": job.get("salary_range") or "",
                "job_type": job.get("job_type") or "Full-time",
                "category": job.get("category") or "",
                "source": job.get("source") or "",
                "url": job.get("url") or "",
            })
        if docs:
            embeddings = self.model.encode(docs).tolist()
            existing = set(self._collection.get()["ids"])
            new_docs, new_ids, new_metas, new_embs = [], [], [], []
            for d, i, m, e in zip(docs, ids, metas, embeddings):
                if i not in existing:
                    new_docs.append(d)
                    new_ids.append(i)
                    new_metas.append(m)
                    new_embs.append(e)
            if new_docs:
                self._collection.add(documents=new_docs, ids=new_ids, metadatas=new_metas, embeddings=new_embs)

    def search(self, query: str, top_k: int = 5, filters: dict = None) -> list[dict]:
        embedding = self.model.encode(query).tolist()
        where = filters if filters else None
        results = self._collection.query(query_embeddings=[embedding], n_results=top_k, where=where)
        matches = []
        for i in range(len(results["ids"][0])):
            matches.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0
            })
        return matches

    def get_job_by_id(self, job_id: str) -> dict | None:
        result = self._collection.get(ids=[job_id])
        if result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0]
            }
        return None

    def get_all_jobs(self) -> list[dict]:
        result = self._collection.get()
        jobs = []
        for i in range(len(result["ids"])):
            jobs.append({
                "id": result["ids"][i],
                "document": result["documents"][i],
                "metadata": result["metadatas"][i]
            })
        return jobs

    def delete_job(self, job_id: str):
        self._collection.delete(ids=[job_id])

    def get_stats(self) -> dict:
        return {"total_jobs": self._collection.count()}
