import type { Message } from "@/types/message";
import { Copy, Check, Flag } from "lucide-react";
import { useState } from "react";

interface ChatBubbleProps {
    message: Message;
}

export function ChatBubble({ message }: ChatBubbleProps) {
    const isUser = message.role === "user";
    const [copied, setCopied] = useState(false);
    const [reported, setReported] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleReport = (id: string, text: string) => {
        // report da mensagem
        setReported((prev) => !prev);
    };

    return (
        <div className={`group flex w-full flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
            <div
                className={`max-w-[80%] min-w-0 rounded-2xl border px-5 py-3 shadow-sm transition-all duration-300 ${reported ? "border-red-500/30 bg-gradient-to-br from-red-500/10 to-transparent shadow-red-500/10" : "bg-card"
                    } ${isUser ? "rounded-br-sm" : "rounded-bl-sm"
                    }`}
            >
                <p className="whitespace-pre-wrap break-words text-sm leading-relaxed [overflow-wrap:anywhere]">
                    {message.content}
                </p>
            </div>

            <div className="invisible flex gap-1 opacity-0 transition-all duration-300 group-hover:visible group-hover:opacity-100 group-hover:delay-500">
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                    {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </button>

                <button
                    onClick={() => handleReport(message.id, message.content)}
                    className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-xs transition-colors hover:bg-red-500/10 hover:text-red-500 ${reported ? "text-red-500" : "text-muted-foreground"
                        }`}
                >
                    <Flag className={`h-3.5 w-3.5 ${reported ? "fill-red-500 text-red-500" : "text-red-500"}`} />
                </button>
            </div>
        </div>
    );
}
