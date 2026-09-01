import { execFileSync, spawn, type ChildProcess } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { expect, test } from "@playwright/test";

type RunningDashboard = {
  process: ChildProcess;
  url: Promise<string>;
};

function createFixtureRepository(): string {
  const root = mkdtempSync(join(tmpdir(), "current-snapshot-"));
  writeFileSync(
    join(root, "targets.yaml"),
    [
      "targets:",
      "  vizaeo:",
      "    name: Vizaeo",
      "    base_url: https://vizaeo.example.test",
      "    environment: production",
      "",
    ].join("\n"),
  );
  mkdirSync(join(root, "reports"));
  writeFileSync(
    join(root, "reports", "last-run.json"),
    JSON.stringify({
      stats: {
        expected: 33,
        unexpected: 1,
        flaky: 0,
        skipped: 0,
        duration: 1250,
        startTime: "2026-09-01T12:00:00.000Z",
      },
      config: { use: { baseURL: "https://vizaeo.example.test" } },
    }),
  );
  execFileSync("git", ["init", "--initial-branch=master"], { cwd: root });
  execFileSync("git", ["add", "."], { cwd: root });
  execFileSync("git", ["-c", "user.name=Dashboard Test", "-c", "user.email=dashboard@example.test", "commit", "-m", "fixture"], { cwd: root });
  return root;
}

function launchDashboard(root: string): RunningDashboard {
  const child = spawn("pnpm", ["dashboard", "--", "--root", root, "--port", "0"], {
    cwd: process.cwd(),
    stdio: ["ignore", "pipe", "pipe"],
  });
  const url = new Promise<string>((resolve, reject) => {
    let output = "";
    const onData = (chunk: Buffer) => {
      output += chunk.toString();
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) resolve(match[0]);
    };
    child.stdout?.on("data", onData);
    child.stderr?.on("data", onData);
    child.once("error", reject);
    child.once("exit", (code) => reject(new Error(`Dashboard exited before launch (${code}): ${output}`)));
  });
  return { process: child, url };
}

function writeCompletedReport(root: string, counts: { passed: number; failed: number }): void {
  writeFileSync(
    join(root, "reports", "last-run.json"),
    JSON.stringify({
      stats: {
        expected: counts.passed,
        unexpected: counts.failed,
        flaky: 0,
        skipped: 0,
        duration: 1250,
        startTime: "2026-09-01T12:00:00.000Z",
      },
      config: { use: { baseURL: "https://vizaeo.example.test" } },
    }),
  );
}

test("QA Operator can read the Current Snapshot", async ({ page }) => {
  const fixtureRoot = createFixtureRepository();
  const dashboard = launchDashboard(fixtureRoot);

  try {
    const dashboardUrl = await dashboard.url;
    await page.goto(dashboardUrl);

    await expect(page.getByRole("heading", { name: "Current Snapshot" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Vizaeo" })).toBeVisible();
    await expect(page.getByText("33 passed")).toBeVisible();
    await expect(page.getByText("1 failed")).toBeVisible();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await expect(page.getByText(/master · [0-9a-f]{7}/)).toBeVisible();
    await expect(page.getByText("Last checked", { exact: false })).toBeVisible();
  } finally {
    dashboard.process.kill("SIGINT");
    rmSync(fixtureRoot, { recursive: true, force: true });
  }
});

test("Overview refreshes when repository evidence changes", async ({ page }) => {
  const fixtureRoot = createFixtureRepository();
  const dashboard = launchDashboard(fixtureRoot);

  try {
    const dashboardUrl = await dashboard.url;
    await page.goto(dashboardUrl);
    await expect(page.getByText("33 passed")).toBeVisible();

    writeCompletedReport(fixtureRoot, { passed: 32, failed: 2 });

    await expect(page.getByText("32 passed")).toBeVisible();
    await expect(page.getByText("2 failed")).toBeVisible();
  } finally {
    dashboard.process.kill("SIGINT");
    rmSync(fixtureRoot, { recursive: true, force: true });
  }
});
