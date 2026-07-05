import axios from "axios";
import { ApiError } from "@/lib/errors";
import { tokenStore } from "@/lib/tokenStore";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
});

export function getApiErrorMessage(data: unknown, fallback: string) {
  if (data && typeof data === "object") {
    const { detail, message } = data as { detail?: unknown; message?: unknown };
    if (typeof message === "string" && message) return message;
    if (typeof detail === "string" && detail) return detail;
  }
  return fallback;
}

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status ?? 0;
      const url = error.config?.url ?? "";
      const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/logout");

      if (status === 401 && !isAuthEndpoint) {
        tokenStore.clear();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      const fallback = status === 422 ? "Pedido inválido." : error.message ?? "Erro de comunicação com o servidor.";
      const message = getApiErrorMessage(error.response?.data, fallback);
      return Promise.reject(new ApiError(status, message, error.response?.data));
    }

    return Promise.reject(error);
  }
);
