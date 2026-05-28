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
}

export function ChatHistorySidebar({
  chats,
  onSelectChat,
}: ChatHistorySidebarProps) {
  return (
    <AppShellSidebar homeTo="/">
      <SidebarGroup>
        <SidebarGroupLabel>Conversas</SidebarGroupLabel>

        <SidebarGroupContent>
          {chats.length === 0 ? (
            <p className="px-2 py-6 text-center text-xs text-muted-foreground group-data-[collapsible=icon]:hidden">
              Ainda não tens conversas.
            </p>
          ) : (
            <SidebarMenu>
              {chats.map((chat) => (
                <SidebarMenuItem key={chat.conversation_id}>
                  <button
                    onClick={() => onSelectChat(chat.conversation_id)}
                    className="flex w-full flex-col gap-0.5 rounded-md px-2 py-2 text-left transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground group-data-[collapsible=icon]:hidden"
                  >
                    <span className="truncate text-sm font-medium">
                      {chat.course_name}
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {formatRelativeDate(chat.updated_at)}
                    </span>
                  </button>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          )}
        </SidebarGroupContent>
      </SidebarGroup>
    </AppShellSidebar>
  );
}
