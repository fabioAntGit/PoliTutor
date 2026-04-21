export type ProjectConfigType = "iaedu" | "none";

export interface ProjectRead {
  id: string;
  name: string;
  description: string;
  institution: string;
  configType: ProjectConfigType;
}
