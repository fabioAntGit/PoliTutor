const DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1";

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

export function getApiUrl(path = ""): string {
  const configuredUrl =
    process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;

  const normalizedBase = stripTrailingSlash(configuredUrl);
  const baseUrl = normalizedBase.endsWith("/api/v1")
    ? normalizedBase
    : `${normalizedBase}/api/v1`;
  const normalizedPath = path ? (path.startsWith("/") ? path : `/${path}`) : "";

  return `${baseUrl}${normalizedPath}`;
}
