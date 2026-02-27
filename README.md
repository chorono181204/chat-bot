# 🎓 PTIT Chatbot - Hệ thống Tư vấn Tuyển sinh Thông minh (RAG)

Một ứng dụng Chatbot AI hiện đại được thiết kế riêng cho **Học viện Công nghệ Bưu chính Viễn thông (PTIT)**, sử dụng kiến trúc **RAG (Retrieval-Augmented Generation)** để cung cấp thông tin tuyển sinh chính xác, minh bạch và có trích dẫn nguồn.

---

## 🏗️ Kiến trúc Hệ thống (System Architecture)

Dự án được xây dựng theo mô hình **Decoupled Architecture** (tách biệt hoàn toàn Backend và Frontend) với quy trình xử lý dữ liệu RAG tùy chỉnh (Custom RAG Pipeline) không phụ thuộc vào các framework nặng nề như LangChain để tối ưu hóa tốc độ và khả năng kiểm soát.

### 1. Quy trình RAG Pipeline
1.  **Ingestion & Parsing**: Hệ thống hỗ trợ đa định dạng (PDF, Excel, Word, TXT). Đặc biệt có bộ Parser chuyên dụng cho Excel điểm chuẩn PTIT để chuyển đổi dữ liệu bảng thành câu văn tự nhiên.
2.  **Hybrid Search (Core)**: Kết hợp 2 phương pháp tìm kiếm:
    *   **Semantic Search**: Sử dụng Vector Database (FAISS) và mô hình Embedding `vietnamese-sbert` để hiểu ngữ nghĩa câu hỏi.
    *   **Keyword Search (BM25)**: Đảm bảo độ chính xác tuyệt đối khi người dùng tra cứu các từ khóa đặc thù như mã ngành, tên môn học.
3.  **Context Re-ranking**: Lọc và sắp xếp các đoạn văn bản phù hợp nhất trước khi đưa vào LLM.
4.  **Generation**: Sử dụng Gemini 1.5 Flash hoặc Ollama để tạo câu trả lời dựa trên ngữ cảnh đã tìm được.

---

## 💻 Công nghệ sử dụng (Tech Stack)

### Frontend (Modern UI/UX)
*   **Framework**: Next.js 15 (App Router).
*   **Styling**: Tailwind CSS với thiết kế tối giản, hiện đại (ChatGPT-style).
*   **Animation**: Framer Motion cho các hiệu ứng chuyển cảnh và streaming text mượt mà.
*   **Icons**: Lucide React.
*   **State Management**: React Hooks & Custom Hooks (`useChat`).

### Backend (AI Engine)
*   **Language**: Python 3.12.
*   **Web Framework**: FastAPI (Asynchronous, High Performance).
*   **Vector Database**: Facebook AI Similarity Search (FAISS).
*   **Database**: SQLite với SQLAlchemy (Lưu lịch sử hội thoại).
*   **AI Models**:
    *   **Embedding**: `keepitreal/vietnamese-sbert` (Chạy local, tối ưu cho tiếng Việt).
    *   **LLM**: Google Gemini API (Cloud) hoặc Ollama (Local/Self-hosted).
*   **Dự phòng**: Hỗ trợ streaming SSE (Server-Sent Events) giúp phản hồi tức thì.

---

## ✨ Tính năng nổi bật

*   🔴 **PTIT Branding**: Giao diện mang đậm bản sắc PTIT với tông màu Đỏ-Trắng và Logo đặc trưng.
*   📚 **Citations (Trích dẫn)**: Mỗi câu trả lời đều đi kèm nguồn tham khảo cụ thể từ file tài liệu gốc.
*   💬 **Conversation History**: Ghi nhớ ngữ cảnh hội thoại và quản lý danh sách lịch sử chat ở Sidebar.
*   ⚙️ **Dual-Mode LLM**: Cho phép chuyển đổi linh hoạt giữa AI trên mây (Gemini) và AI chạy tại máy (Ollama).
*   🚀 **Excel-to-Text**: Tự động hiểu các bảng điểm chuẩn phức tạp và diễn giải thành văn bản dễ hiểu.

---

## 🛠️ Hướng dẫn cài đặt & Chạy dự án

### 1. Cấu hình Backend
1. Cài đặt Python 3.10+.
2. Di chuyển vào thư mục `backend`:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Tạo file `.env` từ `.env.example` và điền `GEMINI_API_KEY`.
4. Index dữ liệu lần đầu:
   ```bash
   python -m backend.core.indexer
   ```
5. Chạy server:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

### 2. Cấu hình Frontend
1. Di chuyển vào thư mục `frontend`:
   ```bash
   cd frontend
   npm install
   ```
2. Chạy ứng dụng:
   ```bash
   npm run dev
   ```

---

## 📂 Cấu trúc thư mục

```text
chat-bot/
├── backend/
│   ├── api/          # Endpoints và Routes (FastAPI)
│   ├── core/         # RAG Engine (Indexer, Parser, Retriever)
│   ├── data/
│   │   ├── raw/      # Nơi bỏ tài liệu đầu vào (.pdf, .xlsx)
│   │   └── processed/# File index FAISS và BM25
│   └── main.py       # Entry point Backend
├── frontend/
│   ├── src/
│   │   ├── components/ # UI Components (Sidebar, Chat, Modal)
│   │   ├── hooks/      # Logic xử lý (useChat)
│   │   └── app/        # Next.js Pages
│   └── tailwind.config.ts
└── README.md
```

---

*Phát triển bởi Đội ngũ kỹ thuật với mục tiêu nâng tầm trải nghiệm tư vấn tuyển sinh số tại PTIT.* 🚀
