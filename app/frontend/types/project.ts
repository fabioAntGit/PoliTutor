export type ProjectConfigType = "iaedu" | "none";

export interface Project {
  id: string;
  name: string;
  description: string;
  institution: string;
  configType: ProjectConfigType;
}