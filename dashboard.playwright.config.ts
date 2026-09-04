import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "dashboard/e2e",
  fullyParallel: false,
  use: {
    browserName: "chromium",
  },
});
