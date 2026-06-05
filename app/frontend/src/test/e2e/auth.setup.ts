import { test as setup, type Page } from "@playwright/test";

const TEACHER = { username: "prof.teste", password: "Teste1234!" };
const STUDENT = { username: "aluno.teste", password: "Teste1234!" };

const TEACHER_STATE = "src/test/e2e/.auth/teacher.json";
const STUDENT_STATE = "src/test/e2e/.auth/student.json";

async function login(page: Page, user: { username: string; password: string }) {
  await page.goto("/login");
  await page.getByLabel("Username", { exact: true }).fill(user.username);
  await page.getByLabel("Password", { exact: true }).fill(user.password);
  await page.getByRole("button", { name: "Entrar" }).click();
}

setup("authenticate teacher", async ({ page }) => {
  await login(page, TEACHER);
  await page.waitForURL("**/dashboard");
  await page.context().storageState({ path: TEACHER_STATE });
});

setup("authenticate student", async ({ page }) => {
  await login(page, STUDENT);
  await page.waitForURL((url) => new URL(url).pathname === "/");
  await page.context().storageState({ path: STUDENT_STATE });
});
