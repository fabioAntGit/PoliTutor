import { CircleHelp } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

interface ProjectDescriptionInfoProps {
  projectName?: string;
  description: string;
  loading?: boolean;
}

export function ProjectDescriptionInfo({
  projectName,
  description,
  loading = false,
}: ProjectDescriptionInfoProps) {
  const title = projectName ? `Sobre ${projectName}` : "Sobre o projeto";

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          aria-label="Ver descrição do projeto"
          title="Ver descrição do projeto"
          className="rounded-full border-border/70 bg-background/70 px-3 text-foreground shadow-sm backdrop-blur hover:bg-muted/80"
        >
          <CircleHelp className="h-4 w-4" />
          <span>Info</span>
        </Button>
      </SheetTrigger>

      <SheetContent side="right" className="w-[92%] border-border bg-background text-foreground sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
          <SheetDescription className="whitespace-pre-line text-muted-foreground">
            {loading
              ? "A carregar descrição..."
              : description || "Sem descrição disponível para este projeto."}
          </SheetDescription>
        </SheetHeader>
      </SheetContent>
    </Sheet>
  );
}
