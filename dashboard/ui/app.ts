type LatestRun = {
  state: string;
  started_at: string | null;
  counts: {
    passed: number | null;
    failed: number | null;
    flaky: number | null;
    skipped: number | null;
  } | null;
};

type Target = {
  name: string;
  base_url: string | null;
  environment: string | null;
  latest_run: LatestRun;
};

type Snapshot = {
  checked_at: string;
  repository: {
    branch: string | null;
    commit: string | null;
  };
  targets: Target[];
};

type SnapshotVersion = {
  version: string;
};

const checkedAt = requiredElement("checked-at");
const repositoryIdentity = requiredElement("repository-identity");
const targets = requiredElement("targets");
const loadError = requiredElement("load-error");
let currentVersion: string | null = null;
let refreshInFlight = false;
let pollingTimer: number | undefined;
let hasSnapshot = false;
let visibilityGeneration = 0;
let activeRefreshController: AbortController | undefined;
let refreshQueued = false;

void initialize();

async function initialize(): Promise<void> {
  document.addEventListener("visibilitychange", onVisibilityChange);
  await refreshWhenChanged();
  startPolling();
}

function onVisibilityChange(): void {
  if (document.visibilityState === "visible") {
    void refreshWhenChanged();
    startPolling();
  } else {
    visibilityGeneration += 1;
    refreshQueued = false;
    stopPolling();
  }
}

function startPolling(): void {
  if (document.visibilityState !== "visible" || pollingTimer !== undefined) return;
  pollingTimer = window.setInterval(() => void refreshWhenChanged(), 2_000);
}

function stopPolling(): void {
  activeRefreshController?.abort();
  if (pollingTimer !== undefined) {
    window.clearInterval(pollingTimer);
    pollingTimer = undefined;
  }
}

async function refreshWhenChanged(): Promise<void> {
  if (document.visibilityState !== "visible") return;
  if (refreshInFlight) {
    refreshQueued = true;
    return;
  }
  refreshQueued = false;
  const refreshGeneration = visibilityGeneration;
  const controller = new AbortController();
  activeRefreshController = controller;
  refreshInFlight = true;
  try {
    const version = await fetchVersion(controller.signal);
    if (!isCurrentRefresh(refreshGeneration)) return;
    if (version !== currentVersion) {
      if (await renderSnapshot(refreshGeneration, controller.signal)) {
        currentVersion = version;
      }
    } else if (hasSnapshot) {
      loadError.hidden = true;
    }
  } catch {
    if (isCurrentRefresh(refreshGeneration)) showUnavailable();
  } finally {
    if (activeRefreshController === controller) {
      activeRefreshController = undefined;
    }
    refreshInFlight = false;
    if (refreshQueued && document.visibilityState === "visible") {
      refreshQueued = false;
      void refreshWhenChanged();
    }
  }
}

async function fetchVersion(signal: AbortSignal): Promise<string> {
  const response = await fetch("/api/version", { cache: "no-store", signal });
  if (!response.ok) throw new Error(`Version request failed (${response.status})`);
  const body = await response.json() as SnapshotVersion;
  if (typeof body.version !== "string") throw new Error("Version response is invalid");
  return body.version;
}

async function renderSnapshot(
  refreshGeneration: number,
  signal: AbortSignal,
): Promise<boolean> {
  try {
    const response = await fetch("/api/snapshot", { cache: "no-store", signal });
    if (!response.ok) throw new Error(`Snapshot request failed (${response.status})`);
    const snapshot = await response.json() as Snapshot;
    if (!isCurrentRefresh(refreshGeneration)) return false;
    render(snapshot);
    hasSnapshot = true;
    loadError.hidden = true;
    return true;
  } catch {
    if (isCurrentRefresh(refreshGeneration)) showUnavailable();
    return false;
  }
}

function isCurrentRefresh(refreshGeneration: number): boolean {
  return (
    document.visibilityState === "visible" &&
    refreshGeneration === visibilityGeneration
  );
}

function showUnavailable(): void {
  loadError.hidden = false;
  loadError.textContent = "Current Snapshot is unavailable because the local dashboard interface could not be reached.";
  if (!hasSnapshot) {
    checkedAt.textContent = "Last checked: unavailable";
    renderRepositoryIdentity({ branch: null, commit: null });
  }
}

function render(snapshot: Snapshot): void {
  checkedAt.textContent = `Last checked: ${formatTime(snapshot.checked_at)}`;
  renderRepositoryIdentity(snapshot.repository);
  targets.replaceChildren(...snapshot.targets.map(targetCard));
}

function targetCard(target: Target): HTMLElement {
  const card = document.createElement("article");
  card.className = "target-card";

  const heading = document.createElement("h3");
  heading.textContent = target.name;
  card.append(heading, details(target));

  const counts = document.createElement("ul");
  counts.className = "run-counts";
  for (const [label, value] of countEntries(target.latest_run.counts)) {
    const item = document.createElement("li");
    item.textContent = `${value ?? "Unavailable"} ${label}`;
    counts.append(item);
  }
  card.append(counts);
  return card;
}

function details(target: Target): HTMLDListElement {
  const fields: Array<[string, string]> = [
    ["Base URL", target.base_url ?? "Unavailable"],
    ["Environment", target.environment ?? "Unavailable"],
    ["Evidence State", evidenceState(target.latest_run.state)],
    ["Source freshness", sourceFreshness(target.latest_run.state)],
    ["Latest run", formatOptionalTime(target.latest_run.started_at)],
  ];
  return definitionList(fields);
}

function definitionList(fields: Array<[string, string]>): HTMLDListElement {
  const list = document.createElement("dl");
  for (const [label, value] of fields) {
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    list.append(term, description);
  }
  return list;
}

function countEntries(counts: LatestRun["counts"]): Array<[string, number | null]> {
  return [
    ["passed", counts?.passed ?? null],
    ["failed", counts?.failed ?? null],
    ["flaky", counts?.flaky ?? null],
    ["skipped", counts?.skipped ?? null],
  ];
}

function renderRepositoryIdentity(repository: Snapshot["repository"]): void {
  repositoryIdentity.replaceChildren(
    definitionList([
      ["Branch", repository.branch ?? "Unavailable"],
      [
        "Commit",
        repository.commit ? repository.commit.slice(0, 7) : "Unavailable",
      ],
    ]),
  );
}

function evidenceState(state: string): string {
  const labels: Record<string, string> = {
    completed: "Completed",
    "never-run": "Never run",
    partial: "Partial evidence",
    stale: "Stale evidence",
    incomplete: "Incomplete evidence",
    unavailable: "Evidence unavailable",
  };
  return labels[state] ?? "Evidence unavailable";
}

function sourceFreshness(state: string): string {
  if (state === "completed") return "Current";
  if (state === "stale") return "Stale";
  return "Unavailable";
}

function formatTime(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? "unavailable" : parsed.toLocaleString();
}

function formatOptionalTime(value: string | null): string {
  return value ? formatTime(value) : "Unavailable";
}

function requiredElement(id: string): HTMLElement {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing dashboard element: ${id}`);
  return element;
}
