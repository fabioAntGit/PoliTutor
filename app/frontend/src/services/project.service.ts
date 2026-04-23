import * as projectsApi from "@/api/projects";
import type { ProjectRead } from "@/types/project";

export const ProjectService = {
  /**
   * Retrieves the list of all available projects.
   */
  async getAllProjects(): Promise<ProjectRead[]> {
    return await projectsApi.getProjects();
  },

  /**
   * Retrieves the details of a specific project by its ID.
   */
  async getProjectById(id: string): Promise<ProjectRead> {
    return await projectsApi.getProject(id);
  }
};
