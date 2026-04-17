import { api } from "@/api/client";
import type { Project } from "@/types/project";

export async function getProjects(): Promise<Project[]> {
  try {
    const res = await api.get("/projects");
    return res.data;
  } catch (error) {
    return [];
  }
}

export async function getProject(id: string): Promise<Project | undefined> {
  try {
    const res = await api.get(`/projects/${encodeURIComponent(id)}`);
    return res.data;
  } catch (error) {
    return undefined;
  }
}
