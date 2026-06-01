import { useState } from "react";
import CreateUserForm from "@/components/admin/CreateUserForm";
import CreateCourseForm from "@/components/admin/CreateCourseForm";
import UserList from "@/components/admin/UserList";
import CourseList from "@/components/admin/CourseList";
import { UserMenu } from "@/components/account/user-menu";

type Tab = "user" | "course" | "users" | "courses";

const TABS: { id: Tab; label: string }[] = [
  { id: "user", label: "Registar utilizador" },
  { id: "course", label: "Criar cadeira" },
  { id: "users", label: "Utilizadores" },
  { id: "courses", label: "Cadeiras" },
];

export default function AdminDashboardPage() {
  const [tab, setTab] = useState<Tab>("user");

  return (
    <main className="min-h-screen p-8 bg-background relative">
      <div className="max-w-lg mx-auto space-y-8 pb-24">
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
        {tab === "courses" && <CourseList />}
      </div>

      <div className="fixed right-4 top-2.5 z-30">
        <UserMenu compact />
      </div>
    </main>
  );
}
