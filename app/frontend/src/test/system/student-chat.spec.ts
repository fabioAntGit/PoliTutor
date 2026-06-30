import { test, expect } from "@playwright/test";

const COURSE_NAME = "Estruturas de Dados";
const OTHER_COURSE_NAME = "Inteligência Artificial";
const CHAT_URL = /\/chat\/[a-f0-9]{24}/;
const API = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";

test.describe("Student chat", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/chat/*/messages", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user_message_id: "u-stub",
          assistant_message_id: "a-stub",
          answer: "Resposta de teste.",
          sources: [],
          is_fallback: false,
          guardrail_triggered: false,
        }),
      });
    });
  });

  test("lists the seeded chat history and opens a conversation", async ({ page }) => {
    await page.goto("/");

    const conversations = page.getByRole("button", { name: new RegExp(COURSE_NAME) });
    await expect(conversations).toHaveCount(3);

    await conversations.first().click();

    await expect(page).toHaveURL(CHAT_URL);
    await expect(page.getByText("user message 0-0")).toBeVisible();
  });

  test("the course dropdown only offers the student's own courses", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("combobox").click();

    await expect(page.getByRole("option", { name: COURSE_NAME })).toBeVisible();
    await expect(page.getByRole("option", { name: OTHER_COURSE_NAME })).toHaveCount(0);
  });

  test("creates a chat for the chosen course", async ({ page }) => {
    await page.goto("/");

    await page.getByPlaceholder("Pergunte alguma coisa").fill("O que é uma lista ligada?");
    await page.getByRole("button", { name: "Iniciar conversa" }).click();

    await expect(page).toHaveURL(CHAT_URL);
    await expect(page.getByRole("heading", { name: COURSE_NAME })).toBeVisible();

    const conversationId = page.url().match(/\/chat\/([a-f0-9]{24})/)?.[1];
    const token = await page.evaluate(() => localStorage.getItem("poli-tutor-access"));
    await page.request.delete(`${API}/chat/${conversationId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  });

  test("sends the student's message (without hitting the LLM)", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: new RegExp(COURSE_NAME) }).first().click();
    await expect(page).toHaveURL(CHAT_URL);

    const question = "Podes explicar recursão?";
    await page.getByPlaceholder("Pergunte alguma coisa").fill(question);

    const sent = page.waitForRequest("**/api/v1/chat/*/messages");
    await page.getByRole("button", { name: "Enviar mensagem" }).click();

    const request = await sent;
    expect(request.postDataJSON()).toMatchObject({ question });
    await expect(page.getByText(question)).toBeVisible();
  });
});
