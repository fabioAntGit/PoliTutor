import { useHome } from "@/hooks/home/useHome";
import { PageState } from "@/components/ui/page-state";
import { ChatHistorySidebar } from "@/components/home/chat-history-sidebar";
import { NewChatComposer } from "@/components/home/new-chat-composer";
import { UserMenu } from "@/components/account/user-menu";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";

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
      <SidebarProvider defaultOpen={false}>
        <ChatHistorySidebar chats={chats} onSelectChat={openChat} onHome={() => window.location.reload()} />

        <SidebarInset>
          <div className="absolute left-4 top-4 z-30 flex items-center gap-2">
            <SidebarTrigger />
            <span className="text-base font-semibold">PoliTutor</span>
          </div>
          <div className="fixed right-4 top-2.5 z-30">
            <UserMenu compact />
          </div>
          <main className="relative flex flex-1 items-center justify-center overflow-hidden px-6">
            <div className="relative z-10 w-full max-w-2xl space-y-6">
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

            <img
              src="/poli_tutor_chat.png"
              alt=""
              aria-hidden="true"
              className="pointer-events-none absolute -bottom-[4.4rem] left-[50%] hidden w-[30rem] select-none duration-700 animate-in fade-in slide-in-from-bottom-4 xl:block xl:w-[39rem] xl:left-[calc(50%+2rem)] 2xl:w-[47rem] 2xl:left-[calc(50%+4rem)]"
            />
          </main>
        </SidebarInset>
      </SidebarProvider>
    </PageState>
  );
}
