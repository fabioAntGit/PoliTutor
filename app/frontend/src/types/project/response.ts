export type ProjectConfigType = "iaedu" | "none";
export type ProjectGuardrailSource = "Dynamic" | null;

export interface ProjectRead {
  id: string;
  name: string;
  description: string;
  institution: string;
  configType: ProjectConfigType;
  source?: ProjectGuardrailSource;
}

export interface ProjectDescriptionRead {
  project_id: string;
  description: string;
}
