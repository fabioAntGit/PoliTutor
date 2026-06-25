import { Plus, Trash2 } from "lucide-react";
import { AppShellSidebar } from "@/components/layout/app-shell-sidebar";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { formatRelativeDate } from "@/lib/date";
import type { ChatListItem } from "@/types/chat";

interface ChatHistorySidebarProps {
  chats: ChatListItem[];
  onSelectChat: (conversationId: string) => void;
  onDeleteChat: (chat: ChatListItem, index: number) => void;
  onHome?: () => void;
}

export function ChatHistorySidebar({
  chats,
  onSelectChat,
  onDeleteChat,
  onHome,
}: ChatHistorySidebarProps) {
  return (
    <AppShellSidebar>
      {onHome && (
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <button
                  onClick={onHome}
                  className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm font-medium transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                >
                  <Plus className="h-4 w-4" />
                  <span>Novo chat</span>
                </button>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      )}

      <SidebarGroup>
        <SidebarGroupLabel>Conversas</SidebarGroupLabel>

        <SidebarGroupContent>
          {chats.length === 0 ? (
            <p className="px-2 py-6 text-center text-xs text-muted-foreground">
              Ainda não tem conversas.
            </p>
          ) : (
            <SidebarMenu>
              {chats.map((chat, index) => (
                <SidebarMenuItem key={chat.conversation_id}>
                  <div className="group/chat relative">
                    <button
                      onClick={() => onSelectChat(chat.conversation_id)}
                      className="flex w-full flex-col gap-0.5 rounded-md px-2 py-2 pr-9 text-left transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                    >
                      <span className="truncate text-sm font-medium">
                        {chat.course_name}
                      </span>
                      <span className="text-[11px] text-muted-foreground">
                        {formatRelativeDate(chat.updated_at)}
                      </span>
                    </button>

                    <button
                      type="button"
                      aria-label="Apagar conversa"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteChat(chat, index);
                      }}
                      className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground opacity-0 transition-opacity hover:text-destructive focus-visible:opacity-100 group-hover/chat:opacity-100"
                    >
                      <Trash2 className="size-3.5" strokeWidth={1.5} />
                    </button>
                  </div>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          )}
        </SidebarGroupContent>
      </SidebarGroup>
    </AppShellSidebar>
  );
}
