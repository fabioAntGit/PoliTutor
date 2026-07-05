import { test, expect } from "@playwright/test";

const API = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";

test.describe("First login", () => {
  test("a new user is forced to change the password on first login", async ({ page, request }) => {
    const stamp = Date.now();
    const email = `fabio.${stamp}@estg.ipp.pt`;
    const username = `fabio.${stamp}`;
    const password = "Teste1234!";

    const login = await request.post(`${API}/auth/login`, {
      form: { username: "admin.teste", password: "Teste1234!" },
    });
    const { access_token } = await login.json();

    await request.post(`${API}/users`, {
      headers: { Authorization: `Bearer ${access_token}` },
      data: { email, password, full_name: "Fabio Antunes", role: "student", courses: [] },
    });

    await page.goto("/login");
    await page.getByLabel("Username", { exact: true }).fill(username);
    await page.getByLabel("Password", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Entrar" }).click();

    await page.waitForURL("**/change-password");
    await expect(
      page.getByText("Tem de definir uma nova palavra-passe antes de continuar"),
    ).toBeVisible();

    await page.getByLabel("Palavra-passe atual").fill(password);
    await page.getByLabel("Nova palavra-passe", { exact: true }).fill("NovaPass123!");
    await page.getByLabel("Confirmar nova palavra-passe").fill("NovaPass123!");
    await page.getByRole("button", { name: "Alterar palavra-passe" }).click();

    await page.waitForURL((url) => new URL(url).pathname === "/");

    await request.delete(`${API}/users/${username}`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
  });
});
