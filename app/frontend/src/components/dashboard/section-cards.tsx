import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

interface OverviewData {
  total_conversations: number
  active_students: number
  total_messages: number
  avg_questions_per_conversation: number
}

interface SectionCardsProps {
  data: OverviewData | null
  variant?: "global" | "course"
}

export function SectionCards({ data, variant = "global" }: SectionCardsProps) {
  const fmt = (n: number) => n.toLocaleString("pt-PT")
  const fmtDec = (n: number) =>
    n.toLocaleString("pt-PT", { minimumFractionDigits: 1, maximumFractionDigits: 1 })

  const isCourse = variant === "course"

  const cards = [
    {
      label: "Alunos Ativos",
      value: data ? fmt(data.active_students) : null,
      sub: isCourse ? "Alunos que interagiram neste curso" : "Alunos com pelo menos uma conversa",
    },
    {
      label: "Total de Conversas",
      value: data ? fmt(data.total_conversations) : null,
      sub: isCourse ? "Conversas iniciadas neste curso" : "Em todos os projetos ativos",
    },
    {
      label: "Total de Mensagens",
      value: data ? fmt(data.total_messages) : null,
      sub: isCourse ? "Perguntas colocadas neste curso" : "Perguntas colocadas pelos alunos",
    },
    {
      label: "Média de Perguntas / Conversa",
      value: data ? fmtDec(data.avg_questions_per_conversation) : null,
      sub: isCourse ? "Média de perguntas por conversa neste curso" : "Média geral de perguntas por conversa",
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      {cards.map(({ label, value, sub }) => (
        <Card
          key={label}
          className="@container/card h-full bg-gradient-to-t from-primary/5 to-card shadow-xs"
        >
          <CardHeader>
            <CardDescription>{label}</CardDescription>
            <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {value ?? <Skeleton className="h-8 w-24" />}
            </CardTitle>
          </CardHeader>
          <CardFooter className="text-sm text-muted-foreground">
            {sub}
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}
