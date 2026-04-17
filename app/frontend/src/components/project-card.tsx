import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Project } from "@/types/project";

interface ProjectCardProps {
  project: Project;
  selected: boolean;
  onSelect?: (project: Project) => void;
}

export function ProjectCard({ project, selected, onSelect }: ProjectCardProps) {
  return (
    <Card
      onClick={onSelect ? () => onSelect(project) : undefined}
      className={cn(
        "cursor-pointer transition-colors",
        selected
          ? "border-primary ring-1 ring-primary"
          : "hover:border-muted-foreground/40"
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{project.name}</CardTitle>
        </div>
        <CardDescription className="text-xs">{project.institution}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{project.description}</p>
      </CardContent>
    </Card>
  );
}
