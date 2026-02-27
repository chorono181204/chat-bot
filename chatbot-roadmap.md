# 🎓 Chatbot Tư Vấn Tuyển Sinh — Roadmap Đồ Án

## Goal
Xây dựng chatbot RAG (Retrieval-Augmented Generation) tư vấn tuyển sinh với pipeline AI tự implement,
không phụ thuộc framework hộp đen (LangChain). Có thể thuyết minh từng bước với giám khảo.

---

## 🏗️ Kiến Trúc Tổng Quan

```
[PDF/Excel Tuyển Sinh]
        ↓
[Document Parser]   ← PyMuPDF + pandas
        ↓
[Chunking Engine]   ← 3 strategies: fixed / sentence-window / semantic
        ↓
[Embedding Engine]  ← SentenceTransformers (vietnamese-sbert, LOCAL)
        ↓
    ┌───┴───┐
[FAISS]   [BM25]   ← Dense + Sparse retriever
    └───┬───┘
        ↓
[Hybrid Retriever]  ← Reciprocal Rank Fusion
        ↓
[LLM Generation]    ← Gemini 1.5 Flash API
        ↓
[FastAPI Backend]   ← REST API
        ↓
[Next.js Frontend]  ← Chat UI với streaming
```

---

## 📦 Tech Stack

| Layer | Công nghệ | Lý do |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Async, tự động OpenAPI docs |
| Parsing | PyMuPDF + pandas + docx2txt | Đọc PDF/Excel/Word |
| Embedding | sentence-transformers (local) | Miễn phí, hiểu internals |
| Vector DB | FAISS | Meta AI, chuẩn ngành |
| Keyword | rank-bm25 + underthesea | BM25 + tokenizer tiếng Việt |
| LLM | Gemini 1.5 Flash (free tier) | 1M tokens/tháng miễn phí |
| DB | SQLite + SQLAlchemy | Lưu conversation history |
| Frontend | Next.js 14 + TypeScript | App Router, streaming |
| Styling | Tailwind CSS | Rapid UI |
| Testing | pytest | Unit test từng module |

---

## 🗓️ PHASE 1: Data & Core AI Pipeline (Tuần 1–2)

### Task 1.1 — Cài đặt môi trường
- [ ] Tạo virtual environment Python: `python -m venv .venv`
- [ ] Cài dependencies: `pip install -r requirements.txt`
- [ ] Kiểm tra: `python -c "from sentence_transformers import SentenceTransformer; print('OK')"`
- Verify: Model load thành công, không lỗi CUDA/CPU

### Task 1.2 — Thu thập & chuẩn bị dữ liệu tuyển sinh
- [ ] Tải/tổng hợp dữ liệu: đề án tuyển sinh PDF, bảng điểm chuẩn Excel, FAQ
- [ ] Đặt vào `backend/data/raw/`
- [ ] Mục tiêu: ít nhất 50 trang tài liệu để RAG có đủ context
- Verify: Files tồn tại trong thư mục raw/

### Task 1.3 — Document Parser (`backend/core/parser.py`)
- [ ] Viết `PDFParser.parse(path)` → List[str] (theo từng trang)
- [ ] Viết `ExcelParser.parse(path)` → List[str] (mỗi row → câu tự nhiên)
- [ ] Xử lý encoding tiếng Việt (UTF-8)
- [ ] Unit test: parse 1 file mẫu → in ra text
- Verify: `pytest tests/test_parser.py` pass

### Task 1.4 — Chunking Engine (`backend/core/chunker.py`)
- [ ] Implement `FixedSizeChunker(size=256, overlap=50)`
- [ ] Implement `SentenceWindowChunker(window=3)`
- [ ] Implement `SemanticChunker(threshold=0.5)` (nâng cao — dùng cosine để detect topic shift)
- [ ] Unit test mỗi strategy
- Verify: Output chunks có độ dài hợp lý, overlap đúng

### Task 1.5 — Embedding Engine (`backend/core/embedder.py`)
- [ ] Load model `keepitreal/vietnamese-sbert`
- [ ] Viết `EmbeddingEngine.encode(texts)` → np.ndarray
- [ ] Cache embeddings ra file `.npy` để không re-embed mỗi lần chạy
- Verify: 2 câu cùng nghĩa → cosine similarity > 0.8

---

## 🗓️ PHASE 2: Retrieval System (Tuần 3)

### Task 2.1 — FAISS Vector Store (`backend/core/vector_store.py`)
- [ ] Viết `VectorStore.add(embeddings, chunks)`
- [ ] Viết `VectorStore.search(query_embedding, k=5)` → [(chunk, score)]
- [ ] Persist index: `faiss.write_index()` / `faiss.read_index()`
- Verify: Query "ngành CNTT" → trả về chunks liên quan đến CNTT

### Task 2.2 — BM25 Retriever (`backend/core/bm25_retriever.py`)
- [ ] Tokenize corpus bằng `underthesea.word_tokenize`
- [ ] Khởi tạo `BM25Okapi` từ `rank_bm25`
- [ ] Viết `BM25Retriever.search(query, k=5)` → [(chunk, score)]
- Verify: Query "điểm chuẩn" → chunks chứa từ "điểm chuẩn" nằm top

### Task 2.3 — Hybrid Retriever (`backend/core/hybrid_retriever.py`)
- [ ] Implement `reciprocal_rank_fusion(*result_lists, k=60)` → merged ranking
- [ ] Viết `HybridRetriever.retrieve(query, k=5)` gọi cả FAISS + BM25
- Verify: So sánh 3 retriever bằng tay với 10 câu hỏi mẫu

---

## 🗓️ PHASE 3: LLM Integration & API (Tuần 4)

### Task 3.1 — Chat Engine (`backend/core/chat_engine.py`)
- [ ] Viết `PromptBuilder.build(query, context_chunks, history)` → str
- [ ] Implement conversation memory (lưu 5 turns gần nhất)
- [ ] Kết nối Gemini API: `google-generativeai` package
- [ ] Streaming response support
- Verify: Gửi câu hỏi → nhận câu trả lời có context từ tài liệu

### Task 3.2 — FastAPI Backend (`backend/api/routes.py`)
- [ ] `POST /chat` — nhận query, trả lời + sources
- [ ] `POST /ingest` — nhận file upload, tự động index
- [ ] `GET /health` — kiểm tra server
- [ ] `GET /conversations/{id}` — lấy lịch sử chat
- [ ] CORS config cho frontend
- Verify: Test với Swagger UI tại `localhost:8000/docs`

### Task 3.3 — Database (SQLite)
- [ ] Schema: `conversations(id, created_at)`, `messages(id, conv_id, role, content, sources)`
- [ ] CRUD operations với SQLAlchemy
- Verify: Sau chat, query SQLite → thấy messages được lưu

---

## 🗓️ PHASE 4: Frontend (Tuần 5)

### Task 4.1 — Setup Next.js
- [ ] `npx create-next-app@latest frontend --typescript --tailwind --app`
- [ ] Cài thêm: `npm i ai @ai-sdk/google lucide-react`
- Verify: `npm run dev` → trang mặc định hiển thị

### Task 4.2 — Chat UI Component
- [ ] Trang chat: message list, input box, send button
- [ ] Streaming messages (dùng `useChat` hook hoặc tự fetch stream)
- [ ] Hiển thị "Sources" — các đoạn tài liệu được dùng để trả lời
- [ ] Loading indicator khi đang generate
- Verify: Chat thực tế với backend → response stream đúng

### Task 4.3 — UI Polish
- [ ] Dark mode
- [ ] Responsive (mobile-friendly)
- [ ] Avatar bot vs user
- [ ] Timestamp messages
- Verify: Chạy trên điện thoại không bị vỡ layout

---

## 🗓️ PHASE 5: Experiments & Evaluation (Tuần 6)

### Task 5.1 — Tạo Test Dataset
- [ ] Viết 30 cặp (câu hỏi, câu trả lời đúng) về tuyển sinh
- [ ] Lưu vào `notebooks/eval_dataset.json`

### Task 5.2 — Đo Metrics (`notebooks/experiments.ipynb`)
- [ ] Đo **Recall@5**: trong top 5 results, có đoạn đúng không?
- [ ] Đo **MRR@10**: Mean Reciprocal Rank
- [ ] So sánh 3 retriever: BM25-only vs FAISS-only vs Hybrid
- [ ] So sánh 3 chunking strategy

### Task 5.3 — Vẽ Biểu Đồ
- [ ] Bar chart: Recall@5 của 3 retriever
- [ ] Bar chart: Chunking strategy performance
- [ ] Lưu figures vào `docs/figures/`
- Verify: Có ít nhất 4 biểu đồ cho báo cáo

---

## 🗓️ PHASE 6: Báo Cáo & Demo (Tuần 7–8)

### Task 6.1 — Viết Báo Cáo
- [ ] Chương 1: Giới thiệu, bài toán, mục tiêu
- [ ] Chương 2: Cơ sở lý thuyết (RAG, BERT, BM25, FAISS, Hybrid Search)
- [ ] Chương 3: Thiết kế hệ thống (kiến trúc, phân tích từng module)
- [ ] Chương 4: Thực nghiệm & đánh giá (bảng + biểu đồ)
- [ ] Chương 5: Kết luận

### Task 6.2 — Chuẩn Bị Demo
- [ ] Docker Compose để chạy 1 lệnh: `docker compose up`
- [ ] README với hướng dẫn cài đặt
- [ ] Slide 15-20 trang cho bảo vệ

---

## ✅ Done When
- [ ] Chatbot trả lời được câu hỏi tuyển sinh từ dữ liệu thực
- [ ] Có thể giải thích từng module với giám khảo
- [ ] Recall@5 ≥ 0.75 trên test dataset
- [ ] Hybrid search tốt hơn từng retriever riêng lẻ (có số liệu)
- [ ] Báo cáo đầy đủ, demo chạy được

---

## 📌 Mốc Quan Trọng

| Tuần | Milestone |
|---|---|
| Tuần 2 | Parser + Chunker + Embedder chạy được, index xong dữ liệu |
| Tuần 3 | Hybrid retrieval hoạt động, test thủ công OK |
| Tuần 4 | Backend API đầy đủ, Swagger docs hoạt động |
| Tuần 5 | Frontend chat UI hoàn chỉnh, end-to-end demo |
| Tuần 6 | Có số liệu thực nghiệm, biểu đồ |
| Tuần 8 | Submit báo cáo + demo |
