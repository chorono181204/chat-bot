"use client";

import { X, Sparkles, Cpu, Key } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

export interface ChatSettings {
    provider: "gemini" | "ollama";
    api_key: string;
    model: string;
}

export function SettingsModal({
    isOpen,
    onClose,
    onSave
}: {
    isOpen: boolean;
    onClose: () => void;
    onSave: (s: ChatSettings) => void;
}) {
    const [tempSettings, setTempSettings] = useState<ChatSettings>({
        provider: "gemini",
        api_key: "",
        model: "gemini-2.5-flash"
    });

    useEffect(() => {
        const saved = localStorage.getItem("chatbot-settings");
        if (saved) setTempSettings(JSON.parse(saved));
    }, [isOpen]);

    const handleSave = () => {
        localStorage.setItem("chatbot-settings", JSON.stringify(tempSettings));
        onSave(tempSettings);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={onClose} />

            <div className="relative bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-slate-100 flex flex-col">
                {/* Header */}
                <div className="p-6 border-b flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-[#C41E22]/10 rounded-lg text-[#C41E22]">
                            <Sparkles size={18} />
                        </div>
                        <h2 className="text-xl font-bold text-slate-800">Cấu hình AI</h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                        <X size={20} className="text-slate-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Provider Selection */}
                    <div className="space-y-3">
                        <label className="text-sm font-semibold text-slate-700 block">LLM Provider</label>
                        <div className="grid grid-cols-2 gap-3">
                            {[
                                { id: "gemini", label: "Google Gemini", sub: "Fast Cloud" },
                                { id: "ollama", label: "Ollama", sub: "Private Local" }
                            ].map((p) => (
                                <button
                                    key={p.id}
                                    onClick={() => setTempSettings({ ...tempSettings, provider: p.id as any })}
                                    className={cn(
                                        "flex flex-col text-left p-4 rounded-2xl border-2 transition-all",
                                        tempSettings.provider === p.id
                                            ? "border-[#C41E22] bg-[#C41E22]/5"
                                            : "border-slate-100 hover:border-slate-200"
                                    )}
                                >
                                    <span className="font-bold text-sm text-slate-800">{p.label}</span>
                                    <span className="text-[10px] text-slate-400 uppercase tracking-wide font-medium">{p.sub}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Model Name */}
                    <div className="space-y-3">
                        <label className="text-sm font-semibold text-slate-700 block flex items-center gap-2">
                            <Cpu size={16} /> Model Name
                        </label>
                        <input
                            type="text"
                            value={tempSettings.model}
                            onChange={(e) => setTempSettings({ ...tempSettings, model: e.target.value })}
                            className="w-full p-4 rounded-xl border border-slate-100 bg-slate-50 focus:bg-white focus:border-[#C41E22] outline-none transition-all text-sm"
                            placeholder={tempSettings.provider === "gemini" ? "gemini-1.5-flash-latest" : "qwen2.5:7b"}
                        />
                    </div>

                    {/* API Key (Only show if gemini) */}
                    {tempSettings.provider === "gemini" && (
                        <div className="space-y-3">
                            <label className="text-sm font-semibold text-slate-700 block flex items-center gap-2">
                                <Key size={16} /> Gemini API Key
                            </label>
                            <input
                                type="password"
                                value={tempSettings.api_key}
                                onChange={(e) => setTempSettings({ ...tempSettings, api_key: e.target.value })}
                                className="w-full p-4 rounded-xl border border-slate-100 bg-slate-50 focus:bg-white focus:border-[#C41E22] outline-none transition-all text-sm"
                                placeholder="Nhập API Key của bạn..."
                            />
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 bg-slate-50 flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 p-4 rounded-2xl font-semibold text-slate-500 hover:bg-slate-100 transition-all"
                    >
                        Hủy
                    </button>
                    <button
                        onClick={handleSave}
                        className="flex-[2] p-4 rounded-2xl bg-[#C41E22] text-white font-bold hover:bg-[#B31518] shadow-lg shadow-[#C41E22]/30 transition-all active:scale-95"
                    >
                        Lưu cấu hình
                    </button>
                </div>
            </div>
        </div>
    );
}
