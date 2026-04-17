import { api } from "@/api/client";

export async function sendMessage(body: {
  conversation_id: string;
  question: string;
  iaedu_endpoint: string;
  iaedu_api_key: string;
  iaedu_channel_id: string;
}) {
  try {
    const response = await api.post("/ask", body);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail ?? "Erro ao enviar mensagem.");
  }
}

export async function getMessages(body: { conversation_id: string }) {
  try {
    const response = await api.get("/messages", { data: body });
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail ?? "Erro ao obter mensagens.");
  }
}
