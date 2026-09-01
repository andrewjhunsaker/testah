type LatestRun = {
  state: string;
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

const checkedAt = requiredElement("checked-at");
const repositoryIdentity = requiredElement("repository-identity");
const targets = requiredElement("targets");
const loadError = requiredElement("load-error");

void renderSnapshot();

async function renderSnapshot(): Promise<void> {
  try {
    const response = await fetch("/api/snapshot", { cache: "no-store" });
    if (!response.ok) throw new Error(`Snapshot request failed (${response.status})`);
    render(await response.json() as Snapshot);
  } catch {
    loadError.hidden = false;
    loadError.textContent = "Current Snapshot is unavailable because the local dashboard interface could not be reached.";
    checkedAt.textContent = "Last checked: unavailable";
    repositoryIdentity.textContent = "Repository identity unavailable";
  }
}

function render(snapshot: Snapshot): void {
  checkedAt.textContent = `Last checked: ${formatTime(snapshot.checked_at)}`;
  repositoryIdentity.textContent = repositoryText(snapshot.repository);
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
  ];
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

function repositoryText(repository: Snapshot["repository"]): string {
  if (!repository.branch || !repository.commit) return "Repository identity unavailable";
  return `${repository.branch} · ${repository.commit.slice(0, 7)}`;
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

function requiredElement(id: string): HTMLElement {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing dashboard element: ${id}`);
  return element;
}
