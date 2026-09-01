// implements: requirements/dashboard/current-snapshot/overview.md
import { execFileSync, spawn, type ChildProcess } from 'node:child_process'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { expect, test } from '@playwright/test'

import { CurrentSnapshotPage } from '../../tests/pages/CurrentSnapshotPage'

type RunningDashboard = {
  process: ChildProcess
  url: Promise<string>
  stop: () => Promise<void>
}

function createFixtureRepository(
  options: { secondTarget?: boolean } = {},
): string {
  const root = mkdtempSync(join(tmpdir(), 'current-snapshot-'))
  writeFileSync(
    join(root, 'targets.yaml'),
    [
      'targets:',
      '  vizaeo:',
      '    name: Vizaeo',
      '    base_url: https://vizaeo.example.test',
      '    environment: production',
      ...(options.secondTarget
        ? [
            '  other:',
            '    name: Other',
            '    base_url: https://other.example.test',
            '    environment: staging',
          ]
        : []),
      '',
    ].join('\n'),
  )
  mkdirSync(join(root, 'reports'))
  writeCompletedReport(root, { passed: 33, failed: 1 })
  execFileSync('git', ['init', '--initial-branch=master'], { cwd: root })
  execFileSync('git', ['add', '.'], { cwd: root })
  execFileSync(
    'git',
    [
      '-c',
      'user.name=Dashboard Test',
      '-c',
      'user.email=dashboard@example.test',
      'commit',
      '-m',
      'fixture',
    ],
    { cwd: root },
  )
  return root
}

function launchDashboard(root: string): RunningDashboard {
  const child = spawn(
    'uv',
    ['run', 'python', '-m', 'dashboard', '--root', root, '--port', '0'],
    {
      cwd: process.cwd(),
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  )
  const url = new Promise<string>((resolve, reject) => {
    let output = ''
    const onData = (chunk: Buffer) => {
      output += chunk.toString()
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+/)
      if (match) resolve(match[0])
    }
    child.stdout?.on('data', onData)
    child.stderr?.on('data', onData)
    child.once('error', reject)
    child.once('exit', (code) =>
      reject(new Error(`Dashboard exited before launch (${code}): ${output}`)),
    )
  })
  const stop = async () => {
    if (child.exitCode !== null || child.signalCode !== null) return
    await new Promise<void>((resolve) => {
      child.once('exit', () => resolve())
      child.kill('SIGINT')
    })
  }
  return { process: child, url, stop }
}

function writeCompletedReport(
  root: string,
  counts: { passed: number; failed: number },
): void {
  writeFileSync(
    join(root, 'reports', 'last-run.json'),
    JSON.stringify({
      stats: {
        expected: counts.passed,
        unexpected: counts.failed,
        flaky: 0,
        skipped: 0,
        duration: 1250,
        startTime: '2026-09-01T12:00:00.000Z',
      },
      config: { use: { baseURL: 'https://vizaeo.example.test' } },
    }),
  )
}

async function cleanup(
  dashboard: RunningDashboard,
  fixtureRoot: string,
): Promise<void> {
  await dashboard.stop()
  rmSync(fixtureRoot, { recursive: true, force: true })
}

test('QA Operator can read the Current Snapshot', async ({ page }) => {
  const fixtureRoot = createFixtureRepository()
  const dashboard = launchDashboard(fixtureRoot)
  const snapshot = new CurrentSnapshotPage(page)

  try {
    await snapshot.goto(await dashboard.url)

    await expect(snapshot.heading).toBeVisible()
    await expect(snapshot.targetHeading('Vizaeo')).toBeVisible()
    await expect(snapshot.count(33, 'passed')).toBeVisible()
    await expect(snapshot.count(1, 'failed')).toBeVisible()
    await expect(snapshot.evidenceState('Completed')).toBeVisible()
    await expect(snapshot.repositoryBranch('master')).toBeVisible()
    await expect(snapshot.repositoryCommit(/[0-9a-f]{7}/)).toBeVisible()
    await expect(snapshot.lastChecked()).toBeVisible()
  } finally {
    await cleanup(dashboard, fixtureRoot)
  }
})

test('Overview labels latest run time for every target', async ({ page }) => {
  const fixtureRoot = createFixtureRepository({ secondTarget: true })
  const dashboard = launchDashboard(fixtureRoot)
  const snapshot = new CurrentSnapshotPage(page)

  try {
    await snapshot.goto(await dashboard.url)

    const expectedStartedAt = await page.evaluate(() =>
      new Date('2026-09-01T12:00:00.000Z').toLocaleString(),
    )
    await expect(snapshot.latestRun('Vizaeo', expectedStartedAt)).toBeVisible()
    await expect(snapshot.latestRun('Other', 'Unavailable')).toBeVisible()
  } finally {
    await cleanup(dashboard, fixtureRoot)
  }
})

test('Overview preserves available repository identity fields', async ({ page }) => {
  const fixtureRoot = createFixtureRepository()
  const commit = execFileSync('git', ['rev-parse', 'HEAD'], {
    cwd: fixtureRoot,
    encoding: 'utf8',
  }).trim()
  execFileSync('git', ['checkout', '--quiet', '--detach'], { cwd: fixtureRoot })
  const dashboard = launchDashboard(fixtureRoot)
  const snapshot = new CurrentSnapshotPage(page)

  try {
    await snapshot.goto(await dashboard.url)

    await expect(snapshot.repositoryBranch('Unavailable')).toBeVisible()
    await expect(snapshot.repositoryCommit(commit.slice(0, 7))).toBeVisible()
  } finally {
    await cleanup(dashboard, fixtureRoot)
  }
})

test('Overview refreshes when repository evidence changes', async ({ page }) => {
  const fixtureRoot = createFixtureRepository()
  const dashboard = launchDashboard(fixtureRoot)
  const snapshot = new CurrentSnapshotPage(page)

  try {
    await snapshot.goto(await dashboard.url)
    await expect(snapshot.count(33, 'passed')).toBeVisible()

    writeCompletedReport(fixtureRoot, { passed: 32, failed: 2 })

    await expect(snapshot.count(32, 'passed')).toBeVisible()
    await expect(snapshot.count(2, 'failed')).toBeVisible()
  } finally {
    await cleanup(dashboard, fixtureRoot)
  }
})

test('Overview retains the last good snapshot when refresh fails', async ({ page }) => {
  const fixtureRoot = createFixtureRepository()
  const dashboard = launchDashboard(fixtureRoot)
  const snapshot = new CurrentSnapshotPage(page)

  try {
    await snapshot.goto(await dashboard.url)
    await expect(snapshot.count(33, 'passed')).toBeVisible()

    await dashboard.stop()

    await expect(snapshot.unavailableNotice).toBeVisible()
    await expect(snapshot.count(33, 'passed')).toBeVisible()
    await expect(snapshot.count(1, 'failed')).toBeVisible()
  } finally {
    await cleanup(dashboard, fixtureRoot)
  }
})

test('Overview pauses refresh while hidden and refreshes when visible', async ({
  page,
}) => {
  const fixtureRoot = createFixtureRepository()
  const dashboard = launchDashboard(fixtureRoot)
  const snapshot = new CurrentSnapshotPage(page)

  try {
    await snapshot.installClock()
    await snapshot.goto(await dashboard.url)
    await expect(snapshot.count(33, 'passed')).toBeVisible()

    await snapshot.setVisibility('hidden')
    const requestsBeforeHidden = snapshot.versionRequestCount()
    writeCompletedReport(fixtureRoot, { passed: 32, failed: 2 })
    await snapshot.advanceTime(10_000)

    await expect.poll(() => snapshot.versionRequestCount()).toBe(requestsBeforeHidden)
    await expect(snapshot.count(33, 'passed')).toBeVisible()
    await expect(snapshot.count(32, 'passed')).toHaveCount(0)

    await snapshot.setVisibility('visible')

    await expect(snapshot.count(32, 'passed')).toBeVisible()
    await expect(snapshot.count(2, 'failed')).toBeVisible()
  } finally {
    await cleanup(dashboard, fixtureRoot)
  }
})
