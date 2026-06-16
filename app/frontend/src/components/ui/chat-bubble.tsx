import type { Message } from "@/types/message";
import { Copy, Check, Flag, BookOpen, Volume2, VolumeX } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ReportService } from "@/services/report.service";
import { toast } from "sonner";

interface ChatBubbleProps {
    message: Message;
}

export function ChatBubble({ message }: ChatBubbleProps) {
    const isUser = message.role === "user";
    const hasPersistedId = /^[a-f0-9]{24}$/i.test(message.id);
    const canReport = isUser && hasPersistedId;
    const [copied, setCopied] = useState(false);
    const [reported, setReported] = useState(message.is_reported || false);
    const [showSources, setShowSources] = useState(false);
    const [speaking, setSpeaking] = useState(false);
    const [isReporting, setIsReporting] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleSpeak = () => {
        if (speaking) {
            window.speechSynthesis.cancel();
            setSpeaking(false);
            return;
        }

        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(message.content);
        utterance.lang = "pt-PT";
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        utterance.onend = () => setSpeaking(false);
        utterance.onerror = () => setSpeaking(false);
        
        setSpeaking(true);
        window.speechSynthesis.speak(utterance);
    };

    const handleReport = async (id: string) => {
        if (isReporting) return;

        setIsReporting(true);
        try {
            if (reported) {
                const success = await ReportService.unreportMessage(id);
                if (success) {
                    setReported(false);
                }
            } else {
                const success = await ReportService.reportMessage(id);
                if (success) {
                    setReported(true);
                } else {
                    toast.error("Erro ao enviar o report. Certifica-te que a mensagem já tem uma resposta.");
                }
            }
        } catch (error: any) {
            console.error("Erro ao processar report:", error);
            const msg = error instanceof Error ? error.message : "Erro ao processar o pedido. Tenta novamente mais tarde.";
            toast.error(msg);
        } finally {
            setIsReporting(false);
        }
    };

    const formatTime = (isoString?: string) => {
        if (!isoString) return "";
        return new Intl.DateTimeFormat("pt-PT", {
            hour: "2-digit",
            minute: "2-digit",
        }).format(new Date(isoString));
    };

    return (
        <div className={`group flex w-full flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}>
            {/* Bubble */}
            <div
                className={`max-w-[85%] min-w-0 rounded-2xl border px-5 py-3 shadow-sm transition-all duration-300 ${
                    reported
                        ? "border-red-500/30 bg-gradient-to-br from-red-500/5 to-transparent shadow-red-500/10 text-foreground"
                        : isUser
                            ? "bg-primary text-primary-foreground border-primary/20"
                            : "bg-card shadow-sm"
                    } ${isUser ? "rounded-br-sm" : "rounded-bl-sm"}`}
            >
                <div className="text-sm leading-relaxed [overflow-wrap:anywhere]">
                    <ReactMarkdown
                        components={{
                            p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                            ul: ({ children }) => <ul className="mb-3 list-disc pl-4 space-y-1">{children}</ul>,
                            ol: ({ children }) => <ol className="mb-3 list-decimal pl-4 space-y-1">{children}</ol>,
                            li: ({ children }) => <li>{children}</li>,
                            strong: ({ children }) => <strong className="font-bold text-foreground/90">{children}</strong>,
                            code: ({ children }) => <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[13px]">{children}</code>,
                        }}
                    >
                        {message.content}
                    </ReactMarkdown>
                </div>

                {!isUser && !message.is_fallback && message.sources && message.sources.length > 0 && (
                    <div className="mt-3 border-t border-border/40 pt-2 text-[11px]">
                        <button
                            onClick={() => setShowSources(!showSources)}
                            className="flex items-center gap-1.5 font-semibold text-muted-foreground transition-colors hover:text-foreground"
                        >
                            <BookOpen className="h-3.5 w-3.5" />
                            {showSources ? "Ocultar Fontes" : `Ver ${message.sources.length} Fontes`}
                        </button>

                        {showSources && (
                            <div className="mt-2 flex flex-wrap gap-1.5 animate-in fade-in slide-in-from-top-1">
                                {message.sources.map((source, idx) => (
                                    <div
                                        key={idx}
                                        className="rounded bg-muted px-2 py-0.5 font-medium text-muted-foreground transition-colors hover:bg-muted/80"
                                    >
                                        {source.filename}
                                        {source.pages && source.pages.length > 0 && ` (p. ${source.pages.join(", ")})`}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className={`flex gap-1 opacity-0 transition-all duration-300 group-hover:opacity-100 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
                <button
                    onClick={handleCopy}
                    title="Copiar"
                    className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                    {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                </button>

                {!isUser && (
                    <button
                        onClick={handleSpeak}
                        title={speaking ? "Parar leitura" : "Ouvir"}
                        className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-xs transition-colors hover:bg-muted hover:text-foreground ${speaking ? "text-primary animate-pulse" : "text-muted-foreground"}`}
                    >
                        {speaking ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
                    </button>
                )}

                {canReport && (
                <button
                    onClick={() => handleReport(message.id)}
                    disabled={isReporting}
                    title={reported ? "Remover report" : "Reportar problema"}
                    className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-xs transition-colors hover:bg-red-500/10 hover:text-red-500 ${reported ? "text-red-500 bg-red-500/5" : "text-muted-foreground"} ${isReporting ? "opacity-50 cursor-wait" : ""}`}
                >
                    <Flag className={`h-3.5 w-3.5 ${reported ? "fill-current" : ""} ${isReporting ? "animate-pulse" : ""}`} />
                </button>
                )}
            </div>
        </div>
    );
}
