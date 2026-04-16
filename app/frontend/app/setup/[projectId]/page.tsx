import { notFound } from "next/navigation";

import { getProject } from "@/lib/api-helpers/projects";
import { SetupForm } from "./setup-form";

type SetupPageProps = {
  params: Promise<{ projectId: string }>;
};

export default async function SetupPage({ params }: SetupPageProps) {
  const { projectId } = await params;
  const project = await getProject(projectId);

  if (!project || project.configType !== "iaedu") notFound();

  return <SetupForm project={project} />;
}
