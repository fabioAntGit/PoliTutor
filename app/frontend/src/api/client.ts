import axios from "axios";
import { ApiError } from "@/lib/errors";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  withCredentials: true,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status ?? 0;
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