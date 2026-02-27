"""
Module 4: FAISS Vector Store
Lưu và tìm kiếm embeddings bằng approximate nearest neighbor search.

Kiến thức AI cần nắm:
- FAISS (Facebook AI Similarity Search) dùng IndexFlatIP
- IP = Inner Product, với normalized vectors → = cosine similarity
- search() trả về top-k vectors gần nhất trong O(log N) trung bình
"""
import json
import pickle
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np


class VectorStore:

    INDEX_PATH = Path(__file__).parent.parent / "data" / "processed" / "faiss.index"
    CHUNKS_PATH = Path(__file__).parent.parent / "data" / "processed" / "chunks.pkl"

    def __init__(self, dim: int = 768):
        self.dim = dim
        # IndexFlatIP: brute-force với inner product (chính xác 100%)
        # Dùng IndexIVFFlat nếu corpus > 100k docs (nhanh hơn, gần đúng)
        self.index = faiss.IndexFlatIP(dim)
        self.chunks: List[str] = []

    def add(self, embeddings: np.ndarray, chunks: List[str]) -> None:
        """Thêm embeddings và chunks tương ứng vào index."""
        assert len(embeddings) == len(chunks), "embeddings và chunks phải cùng số lượng"
        self.index.add(embeddings.astype("float32"))
        self.chunks.extend(chunks)
        print(f"  Added {len(chunks)} chunks. Total: {self.index.ntotal}")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """
        Tìm k chunks gần nhất với query embedding.
        
        Returns:
            [(chunk_text, similarity_score), ...]  — sorted by score desc
        """
        if self.index.ntotal == 0:
            return []

        q = query_embedding.reshape(1, -1).astype("float32")
        scores, indices = self.index.search(q, min(k, self.index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # -1 = không tìm được
                results.append((self.chunks[idx], float(scores[0][i])))
        return results

    def save(self) -> None:
        """Persist index + chunks ra disk."""
        self.INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.INDEX_PATH))
        with open(self.CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)
        print(f"  VectorStore saved. ({self.index.ntotal} vectors)")

    def load(self) -> None:
        """Load index từ disk."""
        self.index = faiss.read_index(str(self.INDEX_PATH))
        with open(self.CHUNKS_PATH, "rb") as f:
            self.chunks = pickle.load(f)
        print(f"  VectorStore loaded. ({self.index.ntotal} vectors)")

    @property
    def is_empty(self) -> bool:
        return self.index.ntotal == 0
