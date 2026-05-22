import { useNavigate } from "react-router";
import { LogOut, MessageSquarePlus, Shield } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatRelativeDate } from "@/lib/date";
import { authService } from "@/services/auth.service";
import { logout } from "@/api/auth";
import type { ChatListItem } from "@/types/chat";

interface ChatHistorySidebarProps {
  chats: ChatListItem[];
  onSelectChat: (conversationId: string) => void;
  onNewChat: () => void;
}

export function ChatHistorySidebar({
  chats,
  onSelectChat,
  onNewChat,
}: ChatHistorySidebarProps) {
  const navigate = useNavigate();
  const isAdmin = authService.getRole() === "admin";

  const handleLogout = async () => {
    const accessToken = authService.getAccessToken();
    if (accessToken) {
      await logout(accessToken).catch(() => {});
    }
    authService.clearTokens();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r bg-muted/30">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-sm font-semibold tracking-tight">Conversas</h2>
        <Button
          variant="ghost"
          size="icon-sm"
          title="Nova conversa"
          onClick={onNewChat}
        >
          <MessageSquarePlus className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        {chats.length === 0 ? (
          <p className="px-2 py-6 text-center text-xs text-muted-foreground">
            Ainda nao tens conversas.
          </p>
        ) : (
          <ul className="space-y-1">
            {chats.map((chat) => (
              <li key={chat.conversation_id}>
                <button
                  onClick={() => onSelectChat(chat.conversation_id)}
                  className="flex w-full flex-col gap-0.5 rounded-md px-2 py-2 text-left transition-colors hover:bg-muted"
                >
                  <span className="truncate text-sm font-medium">
                    {chat.course_name}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {formatRelativeDate(chat.updated_at)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex items-center justify-end gap-1 border-t px-2 py-2">
        {isAdmin && (
          <Button
            variant="ghost"
            size="icon-sm"
            title="Dashboard admin"
            onClick={() => navigate("/admin")}
          >
            <Shield className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon-sm"
          title="Terminar sessao"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </aside>
  );
}
