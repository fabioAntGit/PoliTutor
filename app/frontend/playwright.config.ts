import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./src/test/system",
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
      use: { ...devices["Desktop Chrome"], storageState: "src/test/system/.auth/teacher.json" },
      dependencies: ["setup"],
    },
    {
      name: "student",
      testMatch: /student-.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], storageState: "src/test/system/.auth/student.json" },
      dependencies: ["setup"],
    },
    {
      name: "admin",
      testMatch: /admin-.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], storageState: "src/test/system/.auth/admin.json" },
      dependencies: ["setup"],
    },
    {
      name: "no-auth",
      testMatch: /first-login\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
