import { useEffect, useRef } from "react";
import { ArrowUp, Square } from "lucide-react";
import { ChatBubble } from "@/components/ui/chat-bubble";
import { TypingDots } from "@/components/ui/typing-dots";
import { useChat } from "@/hooks/chat/useChat";
import { PageState } from "@/components/ui/page-state";
import { UserMenu } from "@/components/account/user-menu";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ChatHistorySidebar } from "@/components/home/chat-history-sidebar";

export default function ChatPage() {
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
        chats,
        openChat,
        goHome,
        scrollRef,
        hasScrolled,
        handleScroll,
    } = useChat();

    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const MAX_CHARS = 1500;
    const canSend = input.trim().length > 0;
    const nearLimit = input.length >= MAX_CHARS * 0.9;

    useEffect(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }, [input]);

    return (
        <PageState loading={loading} error={error}>
            <SidebarProvider defaultOpen>
                <ChatHistorySidebar chats={chats} onSelectChat={openChat} onHome={goHome} />

                <SidebarInset>
                    <main className="flex h-screen flex-col overflow-hidden">
                        <header className="relative flex shrink-0 items-center justify-center py-4">
                            <div className="absolute left-4 top-0 bottom-0 my-auto flex items-center gap-2">
                                <SidebarTrigger />
                            </div>

                            <h1 className="text-xl font-semibold">{chat?.course_name}</h1>

                            <div className="absolute right-4 top-0 bottom-0 my-auto flex items-center">
                                <UserMenu compact />
                            </div>
                        </header>

                        <section
                            ref={scrollRef}
                            onScroll={handleScroll}
                            className={`flex-1 overflow-y-auto px-6 transition-[mask-image] duration-300 ${
                                hasScrolled
                                    ? "[mask-image:linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)]"
                                    : "[mask-image:linear-gradient(to_bottom,black,black_85%,transparent)]"
                            }`}
                        >
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

                        <form onSubmit={handleSubmit} className="shrink-0 px-4 pb-5 sm:px-6">
                            <div className="mx-auto w-full max-w-3xl">
                                <div className="flex items-end gap-2 rounded-[1.75rem] border border-border/70 bg-card/80 p-2 pl-4 shadow-lg backdrop-blur-sm transition-colors focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/20">
                                    <textarea
                                        ref={textareaRef}
                                        value={input}
                                        maxLength={MAX_CHARS}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter" && !e.shiftKey) {
                                                e.preventDefault();
                                                e.currentTarget.form?.requestSubmit();
                                            }
                                        }}
                                        placeholder="Pergunte alguma coisa"
                                        rows={1}
                                        className="max-h-[200px] min-h-[2.25rem] min-w-0 flex-1 resize-none self-center bg-transparent py-1.5 text-sm leading-relaxed outline-none placeholder:text-muted-foreground"
                                    />

                                    {isTyping ? (
                                        <button
                                            key="cancel-btn"
                                            type="button"
                                            onClick={handleCancel}
                                            aria-label="Parar geração"
                                            title="Parar geração"
                                            className="flex size-9 shrink-0 items-center justify-center rounded-full bg-foreground text-background transition-transform hover:scale-105 active:scale-95"
                                        >
                                            <Square className="size-4 fill-current" />
                                        </button>
                                    ) : (
                                        <button
                                            key="submit-btn"
                                            type="submit"
                                            disabled={!canSend}
                                            aria-label="Enviar mensagem"
                                            title="Enviar mensagem"
                                            className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all hover:bg-primary/90 hover:scale-105 active:scale-95 disabled:pointer-events-none disabled:opacity-40 disabled:hover:scale-100"
                                        >
                                            <ArrowUp className="size-5" />
                                        </button>
                                    )}
                                </div>

                                <div className="mt-1.5 flex items-center justify-center gap-2 px-2 text-[11px] text-muted-foreground/70">
                                    <span>O PoliTutor pode cometer erros. Por isso, lembre-se de conferir informações relevantes.</span>
                                    {nearLimit && (
                                        <span className="tabular-nums">
                                            {input.length}/{MAX_CHARS}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </form>
                    </main>
                </SidebarInset>
            </SidebarProvider>
        </PageState>
    );
}

