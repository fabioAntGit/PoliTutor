import { notFound } from "next/navigation";

import { PROJECTS } from "@/constants/projects";
import { SetupForm } from "./setup-form";

type SetupPageProps = {
  params: Promise<{ projectId: string }>;
};

export default async function SetupPage({ params }: SetupPageProps) {
  const { projectId } = await params;
  const project = PROJECTS.find((p) => p.id === projectId);

  if (!project || project.configType !== "iaedu") notFound();

  return <SetupForm project={project} />;
}
