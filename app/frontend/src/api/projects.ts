import { api } from "@/api/client";
import type { ProjectRead } from "@/types/project";

export async function getProjects(): Promise<ProjectRead[]> {
  const res = await api.get<ProjectRead[]>("/projects");
  return res.data;
}

export async function getProject(id: string): Promise<ProjectRead> {
  const res = await api.get<ProjectRead>(`/projects/${encodeURIComponent(id)}`);
  return res.data;
}
