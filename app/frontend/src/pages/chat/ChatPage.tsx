import { useNavigate } from "react-router";
import { ArrowLeft, ArrowUp, Square } from "lucide-react";
import { ChatBubble } from "@/components/ui/chat-bubble";
import { TypingDots } from "@/components/ui/typing-dots";
import { useChat } from "@/hooks/chat/useChat";
import { PageState } from "@/components/ui/page-state";

export default function ChatPage() {
    const navigate = useNavigate();
    const {
        chat,
        loading,
        error,
        messages,
        input,
        setInput,
        isTyping,
        bottomRef,
        handleSubmit,
        handleCancel,
    } = useChat();

    return (
        <PageState loading={loading} error={error}>
            <main className="flex h-screen flex-col overflow-hidden">
            <header className="relative flex shrink-0 items-center justify-center border-b py-4">
                <button
                    onClick={() => navigate("/")}
                    className="absolute left-6 rounded-md p-2 transition-colors hover:bg-muted"
                >
                    <ArrowLeft className="h-5 w-5" />
                </button>

                <h1 className="text-xl font-semibold">{chat?.project_name}</h1>
            </header>

            <section className="flex-1 overflow-y-auto px-6 [mask-image:linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)]">
                <div className="mx-auto flex max-w-5xl flex-col space-y-4 py-8">
                    {messages.map((message) => (
                        <ChatBubble key={message.id} message={message} />
                    ))}
                    {isTyping && (
                        <div className="flex w-full flex-col items-start gap-1 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="rounded-2xl border bg-card px-4 py-1 shadow-sm rounded-bl-sm">
                                <TypingDots />
                            </div>
                        </div>
                    )}
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
                        className="min-w-0 flex-1 resize-none overflow-y-auto bg-transparent text-sm outline-none transition-opacity"
                    />

                    {isTyping ? (
                        <button
                            key="cancel-btn"
                            type="button"
                            onClick={handleCancel}
                            className="shrink-0 rounded-full p-2 transition-colors hover:bg-muted"
                        >
                            <Square className="h-4 w-4 fill-foreground" />
                        </button>
                    ) : (
                        <button
                            key="submit-btn"
                            type="submit"
                            className="shrink-0 rounded-full p-2 transition-colors hover:bg-muted"
                        >
                            <ArrowUp className="h-5 w-5" />
                        </button>
                    )}
                </div>
            </form>
        </main>
    </PageState>
  );
}

