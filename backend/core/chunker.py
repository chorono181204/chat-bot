"""
Module 2: Chunking Engine
3 strategies để experiment & so sánh trong đồ án:
  1. FixedSizeChunker   — cắt đều theo token count
  2. SentenceWindowChunker — mỗi chunk xoay quanh 1 câu
  3. SemanticChunker    — cắt theo topic shift (nâng cao)
"""
from abc import ABC, abstractmethod
from typing import List

import numpy as np


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass

    def chunk_many(self, texts: List[str]) -> List[str]:
        result = []
        for t in texts:
            result.extend(self.chunk(t))
        return result


class FixedSizeChunker(BaseChunker):
    """
    Cắt text thành chunks có kích thước cố định (theo từ),
    với overlap để tránh mất context ở ranh giới chunk.
    
    VD: size=256, overlap=50
    └─ Chunk 1: words[0:256]
    └─ Chunk 2: words[206:462]  (overlap 50 từ)
    """

    def __init__(self, size: int = 256, overlap: int = 50):
        self.size = size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        step = self.size - self.overlap

        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.size]
            if len(chunk_words) < 20:  # Bỏ chunk quá ngắn
                continue
            chunks.append(" ".join(chunk_words))

        return chunks


class SentenceWindowChunker(BaseChunker):
    """
    Mỗi chunk = 1 câu chính + N câu xung quanh làm context.
    
    VD: window=2
    └─ Chunk cho câu[3] = câu[1] + câu[2] + câu[3] + câu[4] + câu[5]
    
    Ưu điểm: Không mất ngữ cảnh khi retrieve câu đơn lẻ.
    """

    def __init__(self, window: int = 2):
        self.window = window

    def chunk(self, text: str) -> List[str]:
        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks = []
        for i, _ in enumerate(sentences):
            start = max(0, i - self.window)
            end = min(len(sentences), i + self.window + 1)
            chunk = " ".join(sentences[start:end])
            if len(chunk.split()) >= 15:
                chunks.append(chunk)

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        import re
        # Split tại dấu câu tiếng Việt
        parts = re.split(r'(?<=[.!?])\s+', text)
        return [p.strip() for p in parts if p.strip()]


class SemanticChunker(BaseChunker):
    """
    Phát hiện topic shift bằng cosine similarity giữa các câu liên tiếp.
    Khi similarity giảm đột ngột → cắt chunk tại đó.
    
    Đây là kỹ thuật nâng cao, phù hợp để trình bày trong đồ án.
    Cần embedding model để chạy — inject từ ngoài vào.
    """

    def __init__(self, embedder, threshold: float = 0.5):
        self.embedder = embedder  # EmbeddingEngine instance
        self.threshold = threshold

    def chunk(self, text: str) -> List[str]:
        sentences = self._split_sentences(text)
        if len(sentences) < 3:
            return [text] if len(text.split()) >= 15 else []

        # Embed từng câu
        embeddings = self.embedder.encode(sentences)  # [N, dim]

        # Tính cosine similarity giữa câu liên tiếp
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_sim(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        # Tìm điểm cắt: nơi similarity < threshold
        chunks = []
        current = [sentences[0]]

        for i, sim in enumerate(similarities):
            if sim < self.threshold:
                # Topic shift detected → kết thúc chunk hiện tại
                chunk_text = " ".join(current)
                if len(chunk_text.split()) >= 15:
                    chunks.append(chunk_text)
                current = []
            current.append(sentences[i + 1])

        if current:
            chunk_text = " ".join(current)
            if len(chunk_text.split()) >= 15:
                chunks.append(chunk_text)

        return chunks

    def _cosine_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def _split_sentences(self, text: str) -> List[str]:
        import re
        parts = re.split(r'(?<=[.!?])\s+', text)
        return [p.strip() for p in parts if p.strip()]


# ─── Factory ───────────────────────────────────────────────
def get_chunker(strategy: str = "fixed", **kwargs) -> BaseChunker:
    """
    Factory function để dễ swap strategy trong experiments.
    
    Usage:
        chunker = get_chunker("fixed", size=256, overlap=50)
        chunker = get_chunker("sentence_window", window=2)
        chunker = get_chunker("semantic", embedder=emb, threshold=0.5)
    """
    strategies = {
        "fixed": FixedSizeChunker,
        "sentence_window": SentenceWindowChunker,
        "semantic": SemanticChunker,
    }
    if strategy not in strategies:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose: {list(strategies.keys())}")
    return strategies[strategy](**kwargs)
