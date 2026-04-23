import { useState, useRef, useEffect } from "react";
import { ApiError } from "@/lib/errors";
import { useParams } from "react-router";
import type { Message } from "@/types/message";
import { MessageService } from "@/services/message.service";
import type { SubmitEvent } from "react";
import { ChatService } from "@/services/chat.service";
import type { ChatRead } from "@/types/chat";

export function useChat() {
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
      })
      .catch((err) => {
        if (err instanceof ApiError && err.isNotFound) {
          setError("Chat não encontrado.");
        } else {
          setError("Erro ao carregar os dados do chat.");
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [conversationId]);

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

    if (!conversationId || !chat) return;

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
      const response = await MessageService.sendMessage(
        conversationId,
        { question: trimmed },
        controller.signal
      );

      const assistantMsg: Message = {
        id: response.assistant_message_id,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        isFallback: response.is_fallback,
        createdAt: new Date().toISOString(),
      };

      setMessages((prev) => {
        const updated = prev.map((m) =>
          m.id === userMsg.id ? { ...m, id: response.user_message_id } : m
        );
        return [...updated, assistantMsg];
      });
    } catch (err: any) {
      if (err.name === "CanceledError" || err.name === "AbortError" || err.message === "canceled") {
        return;
      }

      let errorMessage = "Erro ao obter resposta.";
      if (err instanceof ApiError) {
        if (err.isValidationError) {
          errorMessage = "Credenciais inválidas. Verifica o Endpoint, API Key e Channel ID nas definições.";
        } else if (err.message) {
          errorMessage = err.message;
        }
      }

      const assistantMsg: Message = {
        id: `${Date.now()}-assistant-error`,
        role: "assistant",
        content: errorMessage,
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
