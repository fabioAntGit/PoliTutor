import type { ReactNode } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export interface RankedListItem {
  key: string;
  label: ReactNode;
  rawLabel?: string;
  value: number;
  valueLabel: string;
}

interface RankedListCardProps {
  icon: ReactNode;
  title: ReactNode;
  description: ReactNode;
  items: RankedListItem[] | null;
  isLoading: boolean;
  barClassName?: string;
  emptyMessage?: string;
}

export function RankedListCard({
  icon,
  title,
  description,
  items,
  isLoading,
  barClassName = "bg-primary/50",
  emptyMessage = "Sem dados disponíveis.",
}: RankedListCardProps) {
  const maxValue = items && items.length > 0 ? items[0].value : 1;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          {icon}
          <CardTitle>{title}</CardTitle>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading || items === null ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <div className="space-y-3">
            {items.map((item, i) => (
              <div key={item.key} className="flex items-center gap-4">
                <span className="w-4 shrink-0 text-right text-xs font-medium text-muted-foreground">
                  {i + 1}
                </span>
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className="truncate text-sm font-medium"
                      title={item.rawLabel}
                    >
                      {item.label}
                    </span>
                    <span className="shrink-0 tabular-nums text-xs text-muted-foreground">
                      {item.valueLabel}
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${barClassName}`}
                      style={{ width: `${(item.value / maxValue) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
