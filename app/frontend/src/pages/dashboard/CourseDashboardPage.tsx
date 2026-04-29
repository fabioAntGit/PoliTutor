import { useNavigate } from "react-router"
import { Flame, FileText, AlertCircle } from "lucide-react"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { SectionCards } from "@/components/dashboard/section-cards"
import { ChartAreaInteractive } from "@/components/dashboard/chart-area-interactive"
import { useCourseDashboard } from "@/hooks/dashboard/useCourseDashboard"
import type { TopicPoint, SourcePoint } from "@/api/analytics"

export default function CourseDashboardPage() {
  const navigate = useNavigate()
  const { courseId, status, overview, topics, sources } = useCourseDashboard()

  if (status === "not_found") {
    return (
      <div className="flex flex-1 flex-col overflow-y-auto">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4 lg:px-6">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
          <span className="text-sm font-medium">Curso não encontrado</span>
        </header>
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4">
          <AlertCircle className="h-12 w-12 text-muted-foreground" />
          <div className="text-center">
            <h1 className="text-lg font-semibold">Curso não encontrado</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              O curso <span className="font-mono font-medium">"{courseId}"</span> não existe ou ainda não tem dados.
            </p>
          </div>
          <Button variant="outline" onClick={() => navigate("/dashboard")}>
            Voltar à Visão Geral
          </Button>
        </div>
      </div>
    )
  }

  const isLoading = status === "loading"
  const maxTopicCount = topics && topics.length > 0 ? topics[0].count : 1
  const maxSourceCount = sources && sources.length > 0 ? sources[0].references : 1

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
        <span className="text-sm font-medium truncate">{courseId ?? "Curso"}</span>
      </header>

      <div className="@container/main flex flex-1 flex-col gap-6 px-4 py-6 lg:px-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight truncate">
            {courseId?.toUpperCase()}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">Análise individual do curso</p>
        </div>

        <SectionCards data={overview} variant="course" />

        <ChartAreaInteractive course={courseId} description="Evolução das perguntas dos alunos neste curso" />

        <div className="grid grid-cols-1 gap-6 @3xl/main:grid-cols-2">
          <TopicsCard topics={topics} isLoading={isLoading} maxCount={maxTopicCount} />
          <SourcesCard sources={sources} isLoading={isLoading} maxCount={maxSourceCount} />
        </div>
      </div>
    </div>
  )
}

function TopicsCard({ topics, isLoading, maxCount }: { topics: TopicPoint[] | null; isLoading: boolean; maxCount: number }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Flame className="h-4 w-4 text-orange-500" />
          <CardTitle>Conceitos em Destaque</CardTitle>
        </div>
        <CardDescription>Conceitos mais abordados pelos alunos nas interações</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading || topics === null ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
          </div>
        ) : topics.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem dados disponíveis.</p>
        ) : (
          <div className="space-y-3">
            {topics.map(({ topic, count }, i) => (
              <div key={topic} className="flex items-center gap-4">
                <span className="w-4 shrink-0 text-right text-xs font-medium text-muted-foreground">{i + 1}</span>
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{topic}</span>
                    <span className="tabular-nums text-xs text-muted-foreground">{count}×</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary/50 transition-all duration-500"
                      style={{ width: `${(count / maxCount) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function SourcesCard({ sources, isLoading, maxCount }: { sources: SourcePoint[] | null; isLoading: boolean; maxCount: number }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-500" />
          <CardTitle>Fontes Mais Consultadas</CardTitle>
        </div>
        <CardDescription>Materiais do curso mais citados pelo tutor nas respostas aos alunos</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading || sources === null ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
          </div>
        ) : sources.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem dados disponíveis.</p>
        ) : (
          <div className="space-y-3">
            {sources.map(({ filename, references }, i) => (
              <div key={filename} className="flex items-center gap-4">
                <span className="w-4 shrink-0 text-right text-xs font-medium text-muted-foreground">{i + 1}</span>
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium" title={filename}>{filename}</span>
                    <span className="shrink-0 tabular-nums text-xs text-muted-foreground">{references} ref.</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-blue-500/40 transition-all duration-500"
                      style={{ width: `${(references / maxCount) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
