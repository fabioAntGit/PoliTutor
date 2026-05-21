import { useState } from "react";
import { useNavigate } from "react-router";
import { ArrowLeft, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import CreateUserForm from "@/components/admin/CreateUserForm";
import CreateCourseForm from "@/components/admin/CreateCourseForm";
import UserList from "@/components/admin/UserList";

type Tab = "user" | "course" | "users";

const TABS: { id: Tab; label: string }[] = [
  { id: "user", label: "Registar utilizador" },
  { id: "course", label: "Criar cadeira" },
  { id: "users", label: "Utilizadores" },
];

export default function AdminDashboardPage() {
  const [tab, setTab] = useState<Tab>("user");
  const navigate = useNavigate();

  return (
    <main className="min-h-screen p-8 bg-background relative">
      <div className="absolute top-6 left-6">
        <Button
          variant="ghost"
          size="icon"
          title="Voltar"
          onClick={() => navigate("/")}
        >
          <ArrowLeft className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
        </Button>
      </div>

      <div className="absolute top-6 right-6">
        <Button
          variant="ghost"
          size="icon"
          title="Alterar password"
          onClick={() => navigate("/change-password")}
        >
          <KeyRound className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
        </Button>
      </div>

      <div className="max-w-lg mx-auto space-y-8">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard Admin</h1>

        <div className="flex gap-2 border-b">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                tab === id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === "user" && <CreateUserForm />}
        {tab === "course" && <CreateCourseForm />}
        {tab === "users" && <UserList />}
      </div>
    </main>
  );
}
