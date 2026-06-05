import { test, expect, type Page, type Locator } from "@playwright/test";

function card(page: Page, label: string): Locator {
  return page.getByText(label, { exact: true }).locator("..");
}

function rankedCard(page: Page, title: string): Locator {
  return page.locator('[data-slot="card"]', { hasText: title });
}

test.describe("Teacher dashboard", () => {
  test("overview shows the seeded metrics", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "Visão Geral" })).toBeVisible();
    await expect(card(page, "Alunos Ativos")).toContainText("1");
    await expect(card(page, "Total de Conversas")).toContainText("3");
    await expect(card(page, "Total de Mensagens")).toContainText("6");
    await expect(card(page, "Média de Perguntas / Conversa")).toContainText("2");
  });

  test("course page shows the course metrics", async ({ page }) => {
    await page.goto("/dashboard/courses/ed");

    await expect(page.getByRole("heading", { name: "ED" })).toBeVisible();
    await expect(page.getByText("Cadeira não encontrada")).toHaveCount(0);
    await expect(card(page, "Total de Conversas")).toContainText("3");
    await expect(card(page, "Total de Mensagens")).toContainText("6");
  });

  test("course page highlights top concepts and sources", async ({ page }) => {
    await page.goto("/dashboard/courses/ed");

    const concepts = rankedCard(page, "Conceitos em Destaque");
    await expect(concepts).toContainText("listas ligadas");
    await expect(concepts).toContainText("3×");
    await expect(concepts).toContainText("recursão");

    const sources = rankedCard(page, "Fontes Mais Consultadas");
    await expect(sources).toContainText("Capitulo-1-Listas.pdf");
    await expect(sources).toContainText("6 ref.");
    await expect(sources).toContainText("Capitulo-2-Arvores.pdf");
  });

  test("unknown course shows the empty state", async ({ page }) => {
    await page.goto("/dashboard/courses/inexistente");

    await expect(page.getByRole("heading", { name: "Cadeira não encontrada" })).toBeVisible();
  });
});
