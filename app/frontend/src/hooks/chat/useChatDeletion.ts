import { useCallback, useEffect, useRef } from "react";
import { toast } from "sonner";
import { ChatService } from "@/services/chat.service";
import type { ChatListItem } from "@/types/chat";

const UNDO_DELAY_MS = 5000;

export function useChatDeletion({
  setChats,
  onCommitted,
}: {
  setChats: React.Dispatch<React.SetStateAction<ChatListItem[]>>;
  onCommitted?: (conversationId: string) => void;
}) {
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const onCommittedRef = useRef(onCommitted);
  onCommittedRef.current = onCommitted;

  const deleteChat = useCallback(
    (chat: ChatListItem, index: number) => {
      const id = chat.conversation_id;

      setChats((prev) => prev.filter((c) => c.conversation_id !== id));

      const restore = () =>
        setChats((prev) => {
          if (prev.some((c) => c.conversation_id === id)) return prev;
          const next = [...prev];
          next.splice(Math.min(index, next.length), 0, chat);
          return next;
        });

      const commit = () => {
        timers.current.delete(id);
        ChatService.deleteChat(id)
          .then(() => onCommittedRef.current?.(id))
          .catch(() => {
            restore();
            toast.error("Não foi possível apagar a conversa.");
          });
      };

      const timer = setTimeout(commit, UNDO_DELAY_MS);
      timers.current.set(id, timer);

      toast.success("Conversa apagada", {
        duration: UNDO_DELAY_MS,
        actionButtonStyle: {
          backgroundColor: "#ffffff",
          color: "#18181b",
        },
        action: {
          label: "Anular",
          onClick: () => {
            const t = timers.current.get(id);
            if (t) {
              clearTimeout(t);
              timers.current.delete(id);
            }
            restore();
          },
        },
      });
    },
    [setChats]
  );

  useEffect(() => {
    const pending = timers.current;
    return () => {
      pending.forEach((timer, id) => {
        clearTimeout(timer);
        void ChatService.deleteChat(id).catch(() => {});
      });
      pending.clear();
    };
  }, []);

  return { deleteChat };
}
