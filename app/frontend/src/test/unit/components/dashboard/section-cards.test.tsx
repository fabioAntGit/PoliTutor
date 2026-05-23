import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SectionCards } from "@/components/dashboard/section-cards";

const data = {
  total_conversations: 12,
  active_students: 5,
  total_messages: 42,
  avg_questions_per_conversation: 3.5,
};

describe("SectionCards", () => {
  it("renders the four metric labels", () => {
    render(<SectionCards data={data} />);
    expect(screen.getByText("Alunos Ativos")).toBeInTheDocument();
    expect(screen.getByText("Total de Conversas")).toBeInTheDocument();
    expect(screen.getByText("Total de Mensagens")).toBeInTheDocument();
    expect(screen.getByText("Média de Perguntas / Conversa")).toBeInTheDocument();
  });

  it("renders metric values", () => {
    render(<SectionCards data={data} />);
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("3,5")).toBeInTheDocument();
  });

  it("uses course-specific subtitles for the course variant", () => {
    render(<SectionCards data={data} variant="course" />);
    expect(screen.getByText("Alunos que interagiram neste curso")).toBeInTheDocument();
  });

  it("shows no metric values while data is null", () => {
    render(<SectionCards data={null} />);
    expect(screen.getByText("Alunos Ativos")).toBeInTheDocument();
    expect(screen.queryByText("5")).not.toBeInTheDocument();
  });
});
