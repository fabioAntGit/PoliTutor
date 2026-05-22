import { useHome } from "@/hooks/home/useHome";
import { PageState } from "@/components/ui/page-state";
import { ChatHistorySidebar } from "@/components/home/chat-history-sidebar";
import { NewChatComposer } from "@/components/home/new-chat-composer";

export default function HomePage() {
  const {
    courses,
    chats,
    selectedCourse,
    setSelectedCourse,
    input,
    setInput,
    loading,
    error,
    submitting,
    submit,
    openChat,
  } = useHome();

  return (
    <PageState
      loading={loading}
      error={error}
      onRetry={() => window.location.reload()}
    >
      <main className="flex h-screen overflow-hidden">
        <ChatHistorySidebar
          chats={chats}
          onSelectChat={openChat}
          onNewChat={() => setInput("")}
        />

        <section className="flex flex-1 flex-col items-center justify-center px-6">
          <div className="w-full max-w-2xl space-y-6">
            <div className="space-y-1 text-center">
              <h1 className="text-2xl font-semibold tracking-tight">
                Comeca uma nova conversa
              </h1>
              <p className="text-sm text-muted-foreground">
                Escolhe o curso e escreve a tua primeira pergunta.
              </p>
            </div>

            <NewChatComposer
              courses={courses}
              selectedCourse={selectedCourse}
              onCourseChange={setSelectedCourse}
              input={input}
              onInputChange={setInput}
              onSubmit={submit}
              submitting={submitting}
            />
          </div>
        </section>
      </main>
    </PageState>
  );
}
