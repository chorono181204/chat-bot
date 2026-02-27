"use client";

import { useState, useRef, useEffect } from "react";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatMessage, ChatInput } from "@/components/chat/ChatMessages";
import { SettingsModal, ChatSettings } from "@/components/settings/SettingsModal";
import { useChat } from "@/hooks/useChat";
import { Menu, Plus } from "lucide-react";

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");

  const { messages, sendMessage, isLoading, clearChat, conversationId, loadChatHistory } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cuộn xuống cuối mỗi khi có tin nhắn mới
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    sendMessage(inputValue);
    setInputValue("");
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar - Desktop */}
      <ChatSidebar
        onNewChat={clearChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onSelectChat={loadChatHistory}
        currentChatId={conversationId}
        className={isSidebarOpen ? "flex" : "hidden"}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full relative">
        {/* Mobile Header */}
        <header className="md:hidden flex items-center justify-between p-4 bg-white border-b">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 hover:bg-slate-100 rounded-lg">
            <Menu size={20} className="text-slate-600" />
          </button>
          <h2 className="font-bold text-slate-800">PTIT Chatbot</h2>
          <button onClick={clearChat} className="p-2 hover:bg-slate-100 rounded-lg">
            <Plus size={20} className="text-slate-600" />
          </button>
        </header>

        {/* Message Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-6">
              <div className="w-20 h-20 bg-[#C41E22]/10 rounded-3xl flex items-center justify-center text-[#C41E22]">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-10 h-10 stroke-[1.5]">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold text-slate-800 italic">Học viện Công nghệ Bưu chính Viễn thông</h3>
                <p className="text-slate-500 max-w-sm mx-auto">
                  Chào bạn! Mình là Trợ lý Ảo hỗ trợ thông tin tuyển sinh.
                  Hãy thử hỏi mình về ngành học hoặc điểm chuẩn nhé!
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-xl pt-8">
                {[
                  "Điểm chuẩn ngành CNTT năm 2024?",
                  "Học phí hệ đại trà bao nhiêu?",
                  "Các phương thức xét tuyển?",
                  "Học bổng tân sinh viên như thế nào?"
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="p-4 bg-white border border-slate-200 rounded-2xl text-sm text-slate-600 hover:border-[#C41E22] hover:bg-[#C41E22]/5 transition-all text-left font-medium shadow-sm hover:shadow-md"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((m, i) => (
                <ChatMessage key={i} message={m} />
              ))}
              <div ref={messagesEndRef} className="h-4" />
            </>
          )}
        </div>

        {/* Input Area */}
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSend}
          isLoading={isLoading}
        />
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSave={(settings) => {
          console.log("Settings saved:", settings);
        }}
      />

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #E2E8F0;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #CBD5E1;
        }
      `}</style>
    </div>
  );
}
