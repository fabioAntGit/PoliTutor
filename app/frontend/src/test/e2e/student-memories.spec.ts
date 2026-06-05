import { test, expect, type Page } from "@playwright/test";

const MEMORY_A = "Tem dificuldade em inserir no meio de uma lista ligada.";
const MEMORY_B = "Prefere explicações com exemplos de código.";

async function openMemories(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Conta" }).click();
  await page.getByRole("menuitem", { name: "Definições" }).click();
  await expect(page.getByText("2 memórias")).toBeVisible();
}

test.describe("Student memories", () => {
  test("lists the memories stored by the tutor", async ({ page }) => {
    await openMemories(page);

    await expect(page.getByText(MEMORY_A)).toBeVisible();
    await expect(page.getByText(MEMORY_B)).toBeVisible();
  });

  test("removes a memory", async ({ page }) => {
    await openMemories(page);

    const row = page.locator("li", { hasText: MEMORY_A });
    await row.getByRole("button", { name: "Remover memória" }).click();
    await page.getByRole("button", { name: "Remover", exact: true }).click();

    await expect(page.getByText(MEMORY_A)).toHaveCount(0);
    await expect(page.getByText(MEMORY_B)).toBeVisible();
    await expect(page.getByText("1 memória", { exact: true })).toBeVisible();
  });

  test("cannot reach the teacher dashboard", async ({ page }) => {
    await page.goto("/dashboard");

    await page.waitForURL((url) => new URL(url).pathname === "/");
    await expect(page.getByRole("button", { name: "Conta" })).toBeVisible();
  });
});
