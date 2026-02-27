"""
Module 7: Chat Engine (PTIT Edition)
Kết nối: Retrieval → Prompt → Gemini → Response

PTIT System Prompt được tối ưu để:
- Không hallucinate số liệu điểm chuẩn, học phí
- Phân biệt 2 cơ sở HN và HCM
- Hướng dẫn thủ tục nhập học rõ ràng
"""
import json
from typing import AsyncIterator, List, Optional

import google.generativeai as genai

from .hybrid_retriever import HybridRetriever


class PromptBuilder:
    """Xây dựng prompt từ query + RAG context + conversation history."""

    SYSTEM = """Bạn là chuyên viên tư vấn tuyển sinh của Học viện Công nghệ Bưu chính Viễn thông (PTIT).

QUY TẮC BẮT BUỘC:
1. CHỈ trả lời dựa trên THÔNG TIN TUYỂN SINH được cung cấp trong phần ngữ cảnh bên dưới.
2. KHÔNG bịa đặt số liệu. Nếu câu hỏi yêu cầu năm 2024 nhưng dữ liệu chỉ có 2023, hãy trả lời: "Hiện chưa có điểm chuẩn chính thức năm 2024, tuy nhiên bạn có thể tham khảo điểm chuẩn năm 2023 là...".
3. Nếu không tìm thấy bất kỳ thông tin liên quan nào, hãy trả lời: "Tôi chưa có thông tin về vấn đề này. Bạn có thể liên hệ trực tiếp phòng tuyển sinh PTIT tại tuyensinh@ptit.edu.vn hoặc hotline 024.3756.2186."
4. PHÂN BIỆT rõ ràng Hà Nội (BVH) và TP.HCM (BVS).
5. Ưu tiên trả lời bằng danh sách hoặc bảng nếu có nhiều số liệu."""

    def build(
        self,
        query: str,
        context_chunks: List[str],
        history: Optional[List[dict]] = None,
    ) -> str:
        if context_chunks:
            context = "\n\n---\n\n".join(
                f"[Nguồn {i+1}]\n{chunk}"
                for i, chunk in enumerate(context_chunks)
            )
        else:
            context = "Không tìm thấy thông tin liên quan trong cơ sở dữ liệu."

        history_str = ""
        if history:
            turns = history[-6:]  # sliding window 3 turns (6 messages)
            for turn in turns:
                role = "Người dùng" if turn["role"] == "user" else "Trợ lý"
                history_str += f"\n{role}: {turn['content']}"

        prompt = f"""{self.SYSTEM}

=== THÔNG TIN TUYỂN SINH (NGỮ CẢNH) ===
{context}
"""
        if history_str:
            prompt += f"\n=== LỊCH SỬ HỘI THOẠI ==={history_str}\n"

        prompt += f"\n=== CÂU HỎI ===\nNgười dùng: {query}\nTrợ lý:"
        return prompt


class ChatEngine:

    def __init__(
        self,
        retriever: HybridRetriever,
        api_key: str = "",
        provider: str = "gemini",
        model_name: str = "gemini-1.5-flash-latest",
    ):
        self.retriever = retriever
        self.prompt_builder = PromptBuilder()
        self.provider = provider.lower()
        self.model_name = model_name

        if self.provider == "gemini":
            if not api_key:
                print("  [WARN] GEMINI_API_KEY missing. ChatEngine will fail.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "max_output_tokens": 1024,
                },
            )
        elif self.provider == "ollama":
            import httpx
            self.ollama_client = httpx.Client(base_url="http://localhost:11434", timeout=60.0)
            print(f"  [INFO] ChatEngine using Ollama Local ({model_name})")

    def chat(
        self,
        query: str,
        history: Optional[List[dict]] = None,
        k: int = 5,
    ) -> dict:
        # 1. Retrieve
        results = self.retriever.retrieve(query, k=k)
        context_chunks = [chunk for chunk, _ in results]
        scores = [round(float(score), 4) for _, score in results]

        # 2. Build prompt
        prompt = self.prompt_builder.build(query, context_chunks, history)

        # 3. Generate
        if self.provider == "gemini":
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
        else:
            # Ollama API call
            resp = self.ollama_client.post("/api/generate", json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            })
            answer = resp.json().get("response", "").strip()

        return {
            "answer": answer,
            "sources": context_chunks[:3],
            "num_sources": len(context_chunks),
            "retrieval_scores": scores,
        }

    async def stream_chat(
        self,
        query: str,
        history: Optional[List[dict]] = None,
        k: int = 5,
        **kwargs,
    ) -> AsyncIterator[str]:
        import json
        # 0. Override config nếu có
        provider = kwargs.get("provider", self.provider).lower()
        api_key = kwargs.get("api_key", "")
        model_name = kwargs.get("model_name", self.model_name)

        results = self.retriever.retrieve(query, k=k)
        context_chunks = [chunk for chunk, _ in results]
        prompt = self.prompt_builder.build(query, context_chunks, history)

        # Trả về sources đầu tiên
        yield json.dumps({"sources": context_chunks[:3]}, ensure_ascii=False)

        if provider == "gemini":
            # Nếu có api_key mới, cấu hình lại
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
            else:
                model = self.model
            
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield json.dumps({"token": chunk.text}, ensure_ascii=False)
        else:
            # Ollama
            import httpx
            async with httpx.AsyncClient(base_url="http://localhost:11434", timeout=60.0) as client:
                async with client.stream("POST", "/api/generate", json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": 0.2}
                }) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield json.dumps({"token": token}, ensure_ascii=False)
