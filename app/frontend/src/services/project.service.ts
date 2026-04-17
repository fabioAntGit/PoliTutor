import * as projectsApi from "@/api/projects";
import type { Project } from "@/types/project";

export const ProjectService = {
  /**
   * Retrieves the list of all available projects.
   */
  async getAllProjects(): Promise<Project[]> {
    return await projectsApi.getProjects();
  },

  /**
   * Retrieves the details of a specific project by its ID.
   */
  async getProjectById(id: string): Promise<Project | undefined> {
    return await projectsApi.getProject(id);
  }
};
