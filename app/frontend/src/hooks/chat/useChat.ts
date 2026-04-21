import { useState, useRef, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import type { Message } from "@/types/message";
import { MessageService } from "@/services/message.service";
import { sessionService } from "@/services/session.service";
import type { SubmitEvent } from "react";
import { ChatService } from "@/services/chat.service";
import type { ChatRead } from "@/types/chat";

export function useChat() {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const [chat, setChat] = useState<ChatRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!conversationId) {
      setError("Chat nao encontrado.");
      setLoading(false);
      return;
    }

    ChatService.getChat(conversationId)
      .then((chatResponse) => {
        setChat(chatResponse);
        setMessages(chatResponse.messages);

        const config = sessionService.loadConfig();
        if (!config) {
          navigate(`/setup/${chatResponse.project_id}`, { replace: true });
        }
      })
      .catch(() => {
        setError("Erro ao carregar os dados do chat.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [conversationId, navigate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleCancel = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (isTyping) return;

    const trimmed = input.trim();
    if (!trimmed) return;

    const config = sessionService.loadConfig();
    if (!config || !conversationId || !chat) {
      if (chat) {
        navigate(`/setup/${chat.project_id}`, { replace: true });
      } else {
        navigate("/");
      }
      return;
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await MessageService.sendMessage(conversationId, {
        question: trimmed,
      }, {
        apiKey: config.apiKey,
        endpoint: config.endpoint,
        channelId: config.channelId
      }, controller.signal);

      const assistantMsg: Message = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        isFallback: response.is_fallback,
        createdAt: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error: any) {
      if (error.name === "CanceledError" || error.name === "AbortError" || error.message === "canceled") {
        return;
      }

      const assistantMsg: Message = {
        id: `${Date.now()}-assistant-error`,
        role: "assistant",
        content: error instanceof Error ? error.message : "Erro ao obter resposta.",
        createdAt: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  };

  return {
    conversationId,
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
  };
}
