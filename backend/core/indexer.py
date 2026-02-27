"""
Indexer — hỗ trợ cả full build và incremental (thêm 1 file).
"""
import sys
from pathlib import Path

# Đảm bảo import đúng dù chạy từ bất kỳ thư mục nào
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.core.bm25_retriever import BM25Retriever
from backend.core.chunker import get_chunker
from backend.core.embedder import EmbeddingEngine
from backend.core.parser import DocumentParser
from backend.core.vector_store import VectorStore


DATA_DIR = Path(__file__).parent.parent / "data" / "raw"


def build_index(
    data_dir: str = str(DATA_DIR),
    chunking_strategy: str = "fixed",
    chunk_size: int = 256,
    chunk_overlap: int = 50,
):
    """
    Full offline indexing pipeline. Chạy 1 lần khi có dữ liệu mới.

    Args:
        data_dir: Thư mục chứa tài liệu tuyển sinh
        chunking_strategy: 'fixed' | 'sentence_window' | 'semantic'
    """
    print("=" * 55)
    print("PTIT CHATBOT - INDEXING PIPELINE")
    print("=" * 55)

    # Step 1: Parse
    print(f"\n[1/4] Parsing documents tu: {data_dir}")
    parser = DocumentParser()
    raw_texts = parser.parse_directory(data_dir)

    if not raw_texts:
        print("\n[WARN] Khong co du lieu. Hay bo file vao thu muc data/raw/")
        return None, None, None

    # Step 2: Chunk
    print(f"\n[2/4] Chunking (strategy: {chunking_strategy})")
    if chunking_strategy == "semantic":
        _embedder = EmbeddingEngine()
        chunker = get_chunker("semantic", embedder=_embedder)
    elif chunking_strategy == "sentence_window":
        chunker = get_chunker("sentence_window", window=2)
    else:
        chunker = get_chunker("fixed", size=chunk_size, overlap=chunk_overlap)

    chunks = chunker.chunk_many(raw_texts)
    chunks = list(dict.fromkeys(chunks))  # Deduplicate
    print(f"    -> {len(chunks)} chunks sau khi deduplicate")

    if not chunks:
        print("[WARN] Khong tao duoc chunk nao.")
        return None, None, None

    # Step 3: Embed
    print(f"\n[3/4] Embedding (model: vietnamese-sbert, chay local)...")
    embedder = EmbeddingEngine()
    embeddings = embedder.encode(chunks)
    embedder.save_embeddings(embeddings, "corpus")
    print(f"    -> Embeddings shape: {embeddings.shape}  (dim={embedder.dim})")

    # Step 4: Build indexes
    print("\n[4/4] Building FAISS + BM25 indexes...")
    vs = VectorStore(dim=embedder.dim)
    vs.add(embeddings, chunks)
    vs.save()

    bm25 = BM25Retriever()
    bm25.build(chunks)
    bm25.save()

    print("\n" + "=" * 55)
    print(f"[OK] Done! {len(chunks)} chunks duoc index thanh cong.")
    print(f"[INFO] Index luu tai: backend/data/processed/")
    print("[INFO] Chay server: uvicorn backend.main:app --reload")
    print("=" * 55)

    return vs, bm25, embedder


async def build_index_incremental(file_path: str, engine=None):
    """Thêm 1 file mới vào index hiện có mà không cần rebuild toàn bộ."""
    from backend.core.hybrid_retriever import HybridRetriever

    print(f"  [>>] Incremental index: {file_path}")
    parser = DocumentParser()
    raw_texts = parser.parse(file_path)

    chunker = get_chunker("fixed", size=256, overlap=50)
    new_chunks = chunker.chunk_many(raw_texts)

    # Load existing indexer và thêm vào
    embedder = EmbeddingEngine()
    new_embeddings = embedder.encode(new_chunks)

    vs = VectorStore(dim=embedder.dim)
    bm25 = BM25Retriever()

    processed = Path(__file__).parent.parent / "data" / "processed"
    if (processed / "faiss.index").exists():
        vs.load()
        bm25.load()

    vs.add(new_embeddings, new_chunks)
    bm25.build(vs.chunks)  # Rebuild BM25 với toàn bộ chunks

    vs.save()
    bm25.save()

    retriever = HybridRetriever(vs, bm25, embedder)
    print(f"  [OK] Added {len(new_chunks)} new chunks")
    return retriever


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PTIT Chatbot Indexer")
    parser.add_argument("--strategy", default="fixed",
                        choices=["fixed", "sentence_window", "semantic"],
                        help="Chunking strategy")
    parser.add_argument("--size", type=int, default=256, help="Chunk size")
    parser.add_argument("--overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Data directory")

    args = parser.parse_args()
    build_index(args.data_dir, args.strategy, args.size, args.overlap)
