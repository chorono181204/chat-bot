"""
Module 3: Embedding Engine
Dùng SentenceTransformers chạy HOÀN TOÀN LOCAL — không gọi API.

Model được chọn: keepitreal/vietnamese-sbert
└─ BERT-based model fine-tune trên corpus tiếng Việt
└─ Output: vector 768 chiều
└─ Cosine similarity: câu cùng nghĩa → similarity > 0.8

Kiến thức AI cần nắm để trình bày với giám khảo:
- BERT encoder: biến text → [CLS] token embedding → vector
- Mean pooling qua all tokens (sentence-transformers)
- Normalize embeddings để dùng dot product thay cosine
"""
from pathlib import Path
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingEngine:

    DEFAULT_MODEL = "keepitreal/vietnamese-sbert"
    CACHE_DIR = Path(__file__).parent.parent / "data" / "processed"

    def __init__(self, model_name: str = DEFAULT_MODEL):
        print(f"  Loading embedding model: {model_name}")
        # Model download 1 lần, cache tại ~/.cache/huggingface
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        print(f"  Embedding dim: {self.dim}")

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Chuyển text(s) thành vector(s).
        
        Args:
            texts: 1 chuỗi hoặc list chuỗi
            normalize: True → normalize L2, dùng dot product = cosine similarity
        
        Returns:
            np.ndarray shape [N, dim] hoặc [dim] nếu input là string
        """
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=len(texts) > 100,
        )

        return embeddings[0] if single else embeddings

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity giữa 2 vectors đã normalize."""
        return float(np.dot(a, b))

    def save_embeddings(self, embeddings: np.ndarray, name: str) -> Path:
        """Cache embeddings ra disk để không re-compute mỗi lần."""
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = self.CACHE_DIR / f"{name}.npy"
        np.save(path, embeddings)
        print(f"  Embeddings saved: {path}")
        return path

    def load_embeddings(self, name: str) -> np.ndarray:
        path = self.CACHE_DIR / f"{name}.npy"
        if not path.exists():
            raise FileNotFoundError(f"No cached embeddings for '{name}'")
        return np.load(path)
