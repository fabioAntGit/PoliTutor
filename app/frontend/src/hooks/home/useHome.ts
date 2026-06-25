import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { ChatService } from "@/services/chat.service";
import { CourseService } from "@/services/course.service";
import { AuthService } from "@/services/auth.service";
import type { ChatListItem } from "@/types/chat";
import type { CourseResponse } from "@/types/course";
import { ApiError } from "@/lib/errors";
import { toast } from "sonner";
import { useChatDeletion } from "@/hooks/chat/useChatDeletion";

export function useHome() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<CourseResponse[]>([]);
  const [chats, setChats] = useState<ChatListItem[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([CourseService.listMyCourses(AuthService.getCourses()), ChatService.listChats()])
      .then(([mine, chatsData]) => {
        setCourses(mine);
        setChats(chatsData);
        if (mine.length > 0) {
          setSelectedCourse(mine[0].code);
        }
      })
      .catch(() => {
        setError("Nao foi possivel carregar os dados. Tente novamente mais tarde.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const submit = async () => {
    if (submitting) return;

    const trimmed = input.trim();
    if (!trimmed) {
      toast.error("Escreve uma mensagem para iniciar a conversa.");
      return;
    }
    if (!selectedCourse) {
      toast.error("Seleciona uma cadeira.");
      return;
    }

    setSubmitting(true);
    try {
      const chat = await ChatService.createChat({ course_code: selectedCourse });
      navigate(`/chat/${chat.conversation_id}`, {
        state: { initialMessage: trimmed },
      });
    } catch (err) {
      let message = "Erro ao iniciar a conversa.";
      if (err instanceof ApiError) {
        message = err.message;
      }
      console.error("Erro ao criar chat:", err);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const openChat = (conversationId: string) => {
    navigate(`/chat/${conversationId}`);
  };

  const { deleteChat } = useChatDeletion({ setChats });

  return {
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
    deleteChat,
  };
}
