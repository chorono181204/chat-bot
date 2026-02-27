"""
Module 5: BM25 Retriever
Keyword-based retrieval dùng BM25Okapi algorithm.

BM25 vs TF-IDF:
- TF-IDF: tần suất term × log(N/df)
- BM25:   cải tiến TF-IDF với saturation (term freq không tăng vô hạn)
          và document length normalization

Công thức BM25:
  score(D, Q) = Σ IDF(qi) × [tf(qi,D)×(k1+1)] / [tf(qi,D) + k1×(1-b+b×|D|/avgdl)]
  
BM25 giỏi ở: tìm keyword chính xác (mã ngành, năm, tên trường cụ thể)
Dense embedding giỏi ở: hiểu ngữ nghĩa ("học phí" ≈ "chi phí học tập")

→ Hybrid = kết hợp cả 2 
"""
import pickle
from pathlib import Path
from typing import List, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

try:
    from underthesea import word_tokenize
    _HAS_UNDERTHESEA = True
except ImportError:
    _HAS_UNDERTHESEA = False
    print("  [Warning] underthesea not found. Using whitespace tokenizer.")


def tokenize_vi(text: str) -> List[str]:
    """Tokenize tiếng Việt — underthesea nếu có, fallback whitespace."""
    if _HAS_UNDERTHESEA:
        return word_tokenize(text, format="text").split()
    return text.lower().split()


class BM25Retriever:

    SAVE_PATH = Path(__file__).parent.parent / "data" / "processed" / "bm25.pkl"

    def __init__(self):
        self.bm25: BM25Okapi | None = None
        self.chunks: List[str] = []

    def build(self, chunks: List[str]) -> None:
        """Build BM25 index từ danh sách chunks."""
        self.chunks = chunks
        tokenized = [tokenize_vi(c) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)
        print(f"  BM25 index built. ({len(chunks)} docs)")

    def search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Tìm k chunks có BM25 score cao nhất với query.
        
        Returns:
            [(chunk_text, bm25_score), ...]  — sorted by score desc
        """
        if self.bm25 is None or not self.chunks:
            return []

        query_tokens = tokenize_vi(query)
        scores = self.bm25.get_scores(query_tokens)

        top_k_idx = np.argsort(scores)[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top_k_idx if scores[i] > 0]

    def save(self) -> None:
        self.SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.SAVE_PATH, "wb") as f:
            pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)
        print("  BM25 index saved.")

    def load(self) -> None:
        with open(self.SAVE_PATH, "rb") as f:
            data = pickle.load(f)
        self.bm25 = data["bm25"]
        self.chunks = data["chunks"]
        print(f"  BM25 loaded. ({len(self.chunks)} docs)")
