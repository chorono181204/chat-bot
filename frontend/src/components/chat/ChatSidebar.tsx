"use client";

import { useState, useEffect } from "react";
import { Plus, Settings, History } from "lucide-react";
import { cn } from "@/lib/utils";

interface Conversation {
    id: string;
    title: string;
    created_at: string;
}

interface SidebarProps {
    onNewChat: () => void;
    onOpenSettings: () => void;
    onSelectChat: (id: string) => void;
    currentChatId: string | null;
    className?: string;
}

export function ChatSidebar({ onNewChat, onOpenSettings, onSelectChat, currentChatId, className }: SidebarProps) {
    const [conversations, setConversations] = useState<Conversation[]>([]);

    useEffect(() => {
        fetchConversations();
    }, [currentChatId]); // Refresh when current chat changes

    const fetchConversations = async () => {
        try {
            const resp = await fetch("http://localhost:8000/api/conversations");
            if (resp.ok) {
                const data = await resp.json();
                setConversations(data);
            }
        } catch (e) {
            console.error("Failed to fetch conversations:", e);
        }
    };

    return (
        <div className={cn("flex flex-col h-full bg-white text-slate-800 w-64 border-r border-slate-200", className)}>
            {/* Header / Logo */}
            <div className="p-5 flex flex-col gap-4 border-b border-slate-100 mb-2">
                <div className="w-fit">
                    <img src="/logo-ptit-1.svg" alt="PTIT Logo" className="h-10 w-auto" />
                </div>
                <div>
                    <h1 className="font-bold text-lg leading-tight tracking-tight text-slate-900">PTIT Chatbot</h1>
                    <p className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">Tư vấn tuyển sinh</p>
                </div>
            </div>

            {/* New Chat Button */}
            <div className="px-3 mb-4 pt-2">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center justify-center gap-2 bg-[#C41E22] hover:bg-[#A3161A] text-white transition-all p-3 rounded-xl font-bold text-sm shadow-lg shadow-red-200"
                >
                    <Plus size={18} />
                    Cuộc trò chuyện mới
                </button>
            </div>

            {/* Chat History List */}
            <div className="flex-1 overflow-y-auto px-3 space-y-1">
                <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-2 ml-1">Lịch sử trò chuyện</div>
                {conversations.length === 0 ? (
                    <div className="text-xs text-slate-400 ml-1 italic">Chưa có hội thoại</div>
                ) : (
                    conversations.map((conv) => (
                        <button
                            key={conv.id}
                            onClick={() => onSelectChat(conv.id)}
                            className={cn(
                                "w-full text-left flex items-center gap-2 p-3 rounded-lg text-sm transition-all group",
                                currentChatId === conv.id
                                    ? "bg-red-50 text-[#C41E22] font-medium"
                                    : "hover:bg-slate-50 text-slate-600 hover:text-[#C41E22]"
                            )}
                        >
                            <History size={14} className={cn(
                                "shrink-0",
                                currentChatId === conv.id ? "text-[#C41E22]" : "text-slate-400 group-hover:text-[#C41E22]"
                            )} />
                            <span className="truncate">{conv.title}</span>
                        </button>
                    ))
                )}
            </div>

            {/* Footer / Settings */}
            <div className="p-3 border-t border-slate-100">
                <button
                    onClick={onOpenSettings}
                    className="w-full flex items-center gap-2 p-3 rounded-lg hover:bg-slate-100 text-sm text-slate-600 hover:text-slate-900 transition-all"
                >
                    <Settings size={18} className="text-slate-400" />
                    Cài đặt AI
                </button>
            </div>
        </div>
    );
}
