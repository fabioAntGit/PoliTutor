import { api } from "@/api/client";
import type { ProjectDescriptionRead, ProjectRead } from "@/types/project";

export async function getProjects(): Promise<ProjectRead[]> {
  const res = await api.get<ProjectRead[]>("/projects");
  return res.data;
}

export async function getProject(id: string): Promise<ProjectRead> {
  const res = await api.get<ProjectRead>(`/projects/${encodeURIComponent(id)}`);
  return res.data;
}

export async function getProjectDescription(id: string): Promise<ProjectDescriptionRead> {
  const res = await api.get<ProjectDescriptionRead>(
    `/projects/${encodeURIComponent(id)}/description`
  );
  return res.data;
}
