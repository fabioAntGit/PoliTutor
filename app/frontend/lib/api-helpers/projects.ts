import "server-only";

import type { Project } from "@/types/project";
import { getApiUrl } from "@/lib/api-helpers/api-config";

export async function getProjects(): Promise<Project[]> {
  const res = await fetch(getApiUrl("/projects"), { cache: "no-store" });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function getProject(id: string): Promise<Project | undefined> {
  const res = await fetch(getApiUrl(`/projects/${encodeURIComponent(id)}`), {
    cache: "no-store",
  });
  if (!res.ok) {
    return undefined;
  }
  return res.json();
}
