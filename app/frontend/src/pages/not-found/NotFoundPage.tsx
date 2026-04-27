export default function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="flex flex-col items-center gap-6 text-center sm:flex-row sm:text-left">
        <h1 className="text-2xl font-medium sm:text-3xl">404</h1>
        <div className="hidden h-10 w-px bg-border sm:block" />
        <h2 className="text-sm text-muted-foreground sm:text-base">
          Esta página não foi encontrada
        </h2>
      </div>
    </main>
  );
}
