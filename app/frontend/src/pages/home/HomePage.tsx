import { useHome } from "@/hooks/home/useHome";
import { PageState } from "@/components/ui/page-state";
import { ChatHistorySidebar } from "@/components/home/chat-history-sidebar";
import { NewChatComposer } from "@/components/home/new-chat-composer";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

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
      <SidebarProvider>
        <ChatHistorySidebar chats={chats} onSelectChat={openChat} />

        <SidebarInset>
          <main className="flex flex-1 items-center justify-center px-6">
            <div className="w-full max-w-2xl space-y-6">
              <div className="space-y-1 text-center">
                <h1 className="text-2xl font-semibold tracking-tight">
                  Começa uma nova conversa
                </h1>
                <p className="text-sm text-muted-foreground">
                  Escolhe a cadeira e escreve a tua primeira pergunta.
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
          </main>
        </SidebarInset>
      </SidebarProvider>
    </PageState>
  );
}
