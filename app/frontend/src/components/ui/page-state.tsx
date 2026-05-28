import { Loader2, AlertCircle, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router";

interface PageStateProps {
  loading?: boolean;
  error?: string | null;
  children: React.ReactNode;
  onRetry?: () => void;
}

export function PageState({ loading, error, children, onRetry }: PageStateProps) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center p-6">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center p-6 text-center space-y-4">
        <div className="size-12 rounded-full bg-red-500/10 flex items-center justify-center">
          <AlertCircle className="text-red-500" />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-semibold">Ops! Algo correu mal.</h2>
          <p className="text-muted-foreground">{error}</p>
        </div>
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => navigate("/")}
            className="rounded-md border border-input bg-background px-4 py-2 hover:bg-muted transition-colors flex items-center gap-2"
          >
            <ArrowLeft className="size-4" />
            Voltar ao Início
          </button>
          {onRetry && (
            <button
              onClick={onRetry}
              className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Tentar Novamente
            </button>
          )}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
