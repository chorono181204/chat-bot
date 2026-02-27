"use client";

import { useState, useCallback } from "react";

export type Message = {
    role: "user" | "assistant";
    content: string;
    sources?: string[];
};

export function useChat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);

    const sendMessage = useCallback(async (query: string) => {
        if (!query.trim()) return;

        // 1. Thêm tin nhắn của user vào UI
        const userMsg: Message = { role: "user", content: query };
        setMessages((prev) => [...prev, userMsg]);
        setIsLoading(true);

        try {
            // 2. Lấy cấu hình từ Settings
            const savedSettings = localStorage.getItem("chatbot-settings");
            const config = savedSettings ? JSON.parse(savedSettings) : {};

            // 3. Gọi API Streaming
            const response = await fetch("http://localhost:8000/api/chat/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query,
                    conversation_id: conversationId,
                    // Gửi thêm cấu hình LLM nếu API backend hỗ trợ override
                    llm_config: {
                        provider: config.provider || "gemini",
                        api_key: config.api_key || "",
                        model: config.model || "gemini-1.5-flash"
                    }
                }),
            });

            if (!response.ok) throw new Error("Network response was not ok");

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            // Thêm một tin nhắn assistant trống để bắt đầu stream
            setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

            let fullContent = "";

            while (true) {
                const { done, value } = await reader!.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n\n");

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const dataStr = line.replace("data: ", "");
                        if (dataStr === "[DONE]") continue;

                        try {
                            const data = JSON.parse(dataStr);
                            if (data.sources) {
                                setMessages((prev) => {
                                    const newMsgs = [...prev];
                                    newMsgs[newMsgs.length - 1].sources = data.sources;
                                    return newMsgs;
                                });
                            }
                            if (data.token) {
                                fullContent += data.token;
                                // Cập nhật tin nhắn assistant cuối cùng
                                setMessages((prev) => {
                                    const newMsgs = [...prev];
                                    newMsgs[newMsgs.length - 1].content = fullContent;
                                    return newMsgs;
                                });
                            }
                            if (data.conversation_id && !conversationId) {
                                setConversationId(data.conversation_id);
                            }
                        } catch (e) {
                            // Có thể là text thuần hoặc JSON không đầy đủ, bỏ qua nếu lỗi parse
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Chat error:", error);
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "⚠️ Đã có lỗi xảy ra. Hãy kiểm tra lại Backend hoặc API Key." },
            ]);
        } finally {
            setIsLoading(false);
        }
    }, [conversationId]);

    const loadChatHistory = useCallback(async (id: string) => {
        setIsLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/conversations/${id}/messages`);
            if (response.ok) {
                const data = await response.json();
                setMessages(data.messages);
                setConversationId(id);
            }
        } catch (error) {
            console.error("Failed to load history:", error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const clearChat = () => {
        setMessages([]);
        setConversationId(null);
    };

    return {
        messages,
        sendMessage,
        isLoading,
        clearChat,
        conversationId,
        setConversationId,
        loadChatHistory
    };
}
