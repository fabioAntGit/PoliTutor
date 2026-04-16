export async function sendMessage(body: {
  conversation_id: string;
  question: string;
  iaedu_endpoint: string;
  iaedu_api_key: string;
  iaedu_channel_id: string;
}) {
  const response = await fetch("/chat/api/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.detail ?? "Erro ao enviar mensagem.");
  }

  return data;
}

export async function getMessages(body: {
  conversation_id: string;
}) {
  const response = await fetch("/chat/api/messages", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.detail ?? "Erro ao enviar mensagem.");
  }

  return data;
}

