import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { ProjectService } from "@/services/project.service";
import type { SubmitEvent } from "react";

import type { Project } from "@/types/project";
import type { Message } from "@/types/message";
import { MessageService } from "@/services/message.service";

import { ArrowLeft, ArrowUp, Loader2 } from "lucide-react";
import { ChatBubble } from "@/components/ui/chat-bubble";

export default function ChatPage() {
    const navigate = useNavigate();
    const { projectId } = useParams();
    const [project, setProject] = useState<Project | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!projectId) {
            setLoading(false);
            return;
        }

        ProjectService.getProjectById(projectId).then((res) => {
            if (res) {
                setProject(res);
            }
            setLoading(false);
        });
    }, [projectId]);

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

        // TODO: Pass proper credentials from sessionStorage to MessageService
        await MessageService.sendMessage({
            question: trimmed,
            conversation_id: "demo",
            iaedu_api_key: "demo",
            iaedu_endpoint: "demo",
            iaedu_channel_id: "demo"
        });
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center p-6">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <main className="flex h-screen flex-col overflow-hidden">
            <header className="relative flex shrink-0 items-center justify-center border-b py-4">
                <button
                    onClick={() => navigate("/")}
                    className="absolute left-6 rounded-md p-2 transition-colors hover:bg-muted"
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
                <div className="mx-auto flex max-w-4xl items-end gap-2 rounded-xl border bg-card px-4 py-3 shadow-lg">
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
                        className="min-w-0 flex-1 resize-none overflow-y-auto bg-transparent text-xs outline-none"
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
