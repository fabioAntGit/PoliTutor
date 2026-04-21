import { api } from "@/api/client";
import type { ProjectRead } from "@/types/project";

export async function getProjects(): Promise<ProjectRead[]> {
  try {
    const res = await api.get<ProjectRead[]>("/projects");
    return res.data;
  } catch (error) {
    return [];
  }
}

export async function getProject(id: string): Promise<ProjectRead | undefined> {
  try {
    const res = await api.get<ProjectRead>(`/projects/${encodeURIComponent(id)}`);
    return res.data;
  } catch (error) {
    return undefined;
  }
}
