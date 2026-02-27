"use client";

import ReactMarkdown from "react-markdown";
import { User, GraduationCap, Copy, Share2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Message } from "@/hooks/useChat";

export function ChatMessage({ message }: { message: Message }) {
    const isBot = message.role === "assistant";

    return (
        <div className={cn("py-8 flex gap-4 px-4 md:px-8", isBot ? "bg-[#FFF1F2]" : "bg-white")}>
            <div className="flex-shrink-0">
                <div
                    className={cn(
                        "w-9 h-9 rounded-xl flex items-center justify-center shadow-sm",
                        isBot ? "bg-[#C41E22] text-white" : "bg-slate-100 text-slate-600"
                    )}
                >
                    {isBot ? <img src="/logo-ptit-1.svg" alt="Bot" className="w-5 h-5 brightness-0 invert" /> : <User size={20} />}
                </div>
            </div>

            <div className="flex-1 space-y-4 max-w-3xl">
                <div className="font-semibold text-sm text-slate-800 flex items-center gap-2">
                    {isBot ? "PTIT Advisor" : "Bạn"}
                    {isBot && <span className="text-[10px] bg-[#C41E22]/10 text-[#C41E22] px-1.5 py-0.5 rounded uppercase font-bold tracking-tight">Cố vấn Ảo</span>}
                </div>

                <div className="prose prose-slate prose-p:leading-relaxed prose-pre:bg-slate-900 prose-pre:text-white prose-sm max-w-none text-slate-700">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>

                {isBot && message.sources && message.sources.length > 0 && (
                    <div className="pt-4 border-t border-[#C41E22]/5">
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                            📚 Nguồn tham khảo
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {message.sources.map((source, i) => (
                                <div
                                    key={i}
                                    className="text-[11px] px-2 py-1 bg-white border border-slate-200 rounded-md text-slate-500 hover:border-[#C41E22] hover:text-[#C41E22] transition-all cursor-default flex items-center gap-1.5"
                                >
                                    <div className="w-1 h-1 bg-slate-300 rounded-full" />
                                    {source.length > 100 ? source.substring(0, 100) + "..." : source}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {isBot && (
                    <div className="flex items-center gap-3 pt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="text-slate-400 hover:text-slate-600 transition-colors">
                            <Copy size={14} />
                        </button>
                        <button className="text-slate-400 hover:text-slate-600 transition-colors">
                            <Share2 size={14} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

// --- ChatInput ---
export function ChatInput({
    value,
    onChange,
    onSubmit,
    isLoading
}: {
    value: string;
    onChange: (v: string) => void;
    onSubmit: () => void;
    isLoading: boolean;
}) {
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSubmit();
        }
    };

    return (
        <div className="p-4 border-t bg-white/80 backdrop-blur-md">
            <div className="max-w-3xl mx-auto relative group">
                <textarea
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Hỏi mình về điểm chuẩn, học phí, thủ tục nhập học..."
                    disabled={isLoading}
                    rows={1}
                    className="w-full p-4 pr-14 rounded-2xl border border-slate-200 focus:border-[#C41E22] focus:ring-4 focus:ring-[#C41E22]/5 outline-none transition-all resize-none shadow-sm min-h-[56px] text-slate-700 bg-white"
                />
                <button
                    onClick={onSubmit}
                    disabled={!value.trim() || isLoading}
                    className={cn(
                        "absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl transition-all",
                        value.trim() && !isLoading
                            ? "bg-[#C41E22] text-white shadow-lg shadow-[#C41E22]/30 scale-100"
                            : "bg-slate-100 text-slate-400 scale-90"
                    )}
                >
                    {isLoading ? (
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-5 h-5 stroke-[2.5px]">
                            <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                    )}
                </button>
            </div>
            <div className="text-[11px] text-center text-slate-400 mt-2">
                AI có thể có sai sót. Hãy kiểm tra lại thông tin quan trọng.
            </div>
        </div>
    );
}
