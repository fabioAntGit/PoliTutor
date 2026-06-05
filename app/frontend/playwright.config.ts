import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./src/test/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }], ["list"]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "teacher",
      testMatch: /teacher-.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], storageState: "src/test/e2e/.auth/teacher.json" },
      dependencies: ["setup"],
    },
    {
      name: "student",
      testMatch: /student-.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], storageState: "src/test/e2e/.auth/student.json" },
      dependencies: ["setup"],
    },
  ],
});
