import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router";
import type { Message } from "@/types/message";
import { MessageService } from "@/services/message.service";
import { sessionService } from "@/services/session.service";
import { useProject } from "@/hooks/shared/useProject";
import type { SubmitEvent } from "react";

export function useChat() {
  const navigate = useNavigate();
  const { projectId, project, loading, error } = useProject();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!loading && project) {
      const config = sessionService.loadConfig();
      if (!config) {
        navigate(`/setup/${project.id}`);
      }
    }
  }, [loading, project, navigate]);

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
    if (!config) {
      navigate(`/setup/${projectId}`);
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
      const response = await MessageService.sendMessage({
        question: trimmed,
        conversation_id: "demo",
        iaedu_api_key: config.apiKey,
        iaedu_endpoint: config.endpoint,
        iaedu_channel_id: config.channelId
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
    project,
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
