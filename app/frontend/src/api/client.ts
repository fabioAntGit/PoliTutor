import axios from "axios";
import { ApiError } from "@/lib/errors";
import { tokenStore } from "@/lib/tokenStore";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
});

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

      const message =
        error.response?.data?.detail ??
        error.response?.data?.message ??
        error.message ??
        "Erro de comunicação com o servidor.";
      return Promise.reject(new ApiError(status, message, error.response?.data));
    }

    return Promise.reject(error);
  }
);
