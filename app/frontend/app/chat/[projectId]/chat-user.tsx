import { useRouter } from "next/navigation";
import type { Project } from "@/types/project";
import { useEffect, useRef, useState } from "react";
import type { Message } from "@/types/message";
import { sendMessage } from "@/app/chat/api/messages/messages";
import { ArrowUp } from "lucide-react";
import { ArrowLeft } from "lucide-react";
import { ChatBubble } from "@/components/ui/chat-bubble";
import { SubmitEvent } from "react";

interface ChatUserProps {
    project: Project;
}

export function ChatUser({ project }: ChatUserProps) {
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const bottomRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        const trimmed = input.trim();
        if (!trimmed) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: "user",
            content: trimmed,
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        await sendMessage(trimmed);
    };

    return (
        <main className="flex h-screen flex-col overflow-hidden">
            <header className="relative flex items-center justify-center shrink-0 border-b py-4">
                <button
                    onClick={() => router.push("/")}
                    className="absolute left-6 rounded-md p-2 hover:bg-muted transition-colors"
                >
                    <ArrowLeft className="h-5 w-5" />
                </button>
                <h1 className="text-xl font-semibold">{project.name}</h1>
            </header>

            <section className="flex-1 overflow-y-auto px-6 [mask-image:linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)]">
                <div className="mx-auto flex max-w-5xl flex-col space-y-4 py-8">
                    {messages.map((message) => (
                        <ChatBubble key={message.id} message={message} />
                    ))}
                    <div ref={bottomRef} />
                </div>
            </section>

            <form onSubmit={handleSubmit} className="shrink-0 px-6 pb-4">
                <div className="mx-auto flex max-w-4xl items-end gap-2 rounded-xl border px-4 py-3 shadow-lg bg-card">
                    <textarea
                        value={input}
                        maxLength={1500}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                e.currentTarget.form?.requestSubmit();
                            }
                        }}
                        placeholder="Escreve a tua mensagem..."
                        rows={6}
                        className="flex-1 min-w-0 resize-none overflow-y-auto bg-transparent text-xs outline-none"
                    />
                    <button
                        type="submit"
                        className="shrink-0 rounded-full p-2 transition-colors hover:bg-muted"
                    >
                        <ArrowUp className="h-5 w-5" />
                    </button>
                </div>
            </form>
        </main>
    );
}

