import Link from "next/link";

import { ProjectCard } from "@/components/project-card";
import { getProjects } from "@/lib/api-helpers/projects";

export default async function Home() {
  const projects = await getProjects();
  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-xl space-y-8">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Selecione um projeto para começar.</h1>
          {/* <p className="text-sm text-muted-foreground">
            Selecione um projeto para começar.
          </p> */}
        </div>

        <div className="grid gap-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={
                project.configType === "iaedu"
                  ? `/setup/${project.id}`
                  : `/chat/${project.id}`
              }
            >
              <ProjectCard project={project} selected={false} />
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
