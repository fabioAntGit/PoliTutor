import { test, expect } from "@playwright/test";

test.describe("Admin dashboard", () => {
  test("creates a user and shows it in the users list", async ({ page }) => {
    const stamp = Date.now();
    const email = `fabio.antunes.${stamp}@estg.ipp.pt`;
    const username = `fabio.antunes.${stamp}`;

    await page.goto("/admin");

    await page.getByLabel("Nome completo").fill("Fabio Antunes");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Palavra-passe", { exact: true }).fill("Password123!");
    await page.getByRole("button", { name: "Criar utilizador" }).click();

    await expect(page.getByText("Utilizador criado com sucesso")).toBeVisible();
    await expect(page.getByText(username)).toBeVisible(); 
    await page.getByRole("button", { name: "Fechar" }).click();

    await page.getByRole("button", { name: "Utilizadores" }).click();
    await page.getByPlaceholder("Procurar por nome, username ou email").fill(username);
    await expect(page.getByText("Fabio Antunes")).toBeVisible();
  });

  test("creates a course and shows it in the courses list", async ({ page }) => {
    const stamp = Date.now();
    const code = `test${stamp}`;
    const name = `Cadeira ${stamp}`;

    await page.goto("/admin");
    await page.getByRole("button", { name: "Criar cadeira" }).click();

    await page.getByLabel("Código").fill(code);
    await page.getByLabel("Nome").fill(name);
    await page.locator("form").getByRole("button", { name: "Criar cadeira" }).click();

    await expect(page.getByText("Cadeira criada com sucesso")).toBeVisible();

    await page.getByRole("button", { name: "Cadeiras" }).click();
    await expect(page.getByText(name)).toBeVisible();
  });

  test("lists the seeded courses", async ({ page }) => {
    await page.goto("/admin");
    await page.getByRole("button", { name: "Cadeiras" }).click();

    await expect(page.getByText("Estruturas de Dados")).toBeVisible();
    await expect(page.getByText("Inteligência Artificial")).toBeVisible();
  });

  test("lists the seeded users", async ({ page }) => {
    await page.goto("/admin");
    await page.getByRole("button", { name: "Utilizadores" }).click();

    await expect(page.getByText("Professor de Teste")).toBeVisible();
    await expect(page.getByText("Aluno de Teste")).toBeVisible();
  });
});
