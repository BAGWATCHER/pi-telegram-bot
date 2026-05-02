import * as fs from "node:fs";
import * as path from "node:path";

export const CHOW_PRIMARY_CHAT_ID = "-1003665370879";

const BOT_ROOT = process.cwd();
const MEMORY_ROOT = path.join(BOT_ROOT, "memory");
const MAX_EVENT_TITLE_CHARS = 110;
const MAX_EVENT_DETAIL_CHARS = 420;

const IMPORTANCE_KEYWORDS = [
  "deploy",
  "shipped",
  "phase",
  "blocked",
  "error",
  "fix",
  "api",
  "endpoint",
  "oauth",
  "token",
  "key",
  "env",
  "pm2",
  "migration",
  "checkout",
  "quote",
  "merchant",
  "urgent",
  "decision",
  "status",
];

const PROJECT_SIGNALS: Record<string, string[]> = {
  bearingbrain: ["bearingbrain", "partsbrain", "merchant feed", "checkout", "mcp", "external api"],
  rico: ["rico", "trenchfeed", "jupiter", "solana", "gemini", "v3"],
  bagwatcher: ["bagwatcher", "vamp", "liquidity intel"],
  jose: ["jose", "telegram manager", "triage"],
  hive: ["hive", "room", "mrchow-manager"],
  chow: ["chow", "second-brain", "memory"],
};

const PROJECT_PRIORITY: Record<string, number> = {
  bearingbrain: 1,
  rico: 0.6,
  bagwatcher: 0.45,
  jose: 0.35,
  hive: 0.3,
  chow: 0.55,
  other: 0.25,
};

export type BrainEventType =
  | "user_request"
  | "assistant_result"
  | "manual_note"
  | "session_rotation"
  | "daily_consolidation"
  | "system";

export interface BrainEvent {
  id: string;
  timestamp: string;
  type: BrainEventType;
  title: string;
  detail?: string;
  tags: string[];
  project: string;
  importance: number; // 1..5
  source: string;
}

interface BrainDirs {
  brainDir: string;
  logsDir: string;
  consolidatedDir: string;
  eventsPath: string;
  markerPath: string;
}

export interface BrainStatus {
  chatId: string;
  eventCount: number;
  lastEventAt: string | null;
  lastConsolidatedDate: string | null;
  latestConsolidationPath: string | null;
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

function ensureDir(p: string): void {
  fs.mkdirSync(p, { recursive: true });
}

function getChatMemoryDir(chatId: string | number): string {
  const dir = path.join(MEMORY_ROOT, String(chatId));
  ensureDir(dir);
  return dir;
}

function getBrainDirs(chatId: string | number): BrainDirs {
  const brainDir = path.join(getChatMemoryDir(chatId), "second-brain");
  const logsDir = path.join(brainDir, "logs");
  const consolidatedDir = path.join(brainDir, "consolidated");

  ensureDir(brainDir);
  ensureDir(logsDir);
  ensureDir(consolidatedDir);

  return {
    brainDir,
    logsDir,
    consolidatedDir,
    eventsPath: path.join(brainDir, "events.ndjson"),
    markerPath: path.join(logsDir, "last-consolidated-date.txt"),
  };
}

export function isChowPrimaryChat(chatId: string | number): boolean {
  return String(chatId) === CHOW_PRIMARY_CHAT_ID;
}

function utcDate(date = new Date()): string {
  return date.toISOString().slice(0, 10);
}

function truncate(text: string, maxChars: number): string {
  const t = text.replace(/\s+/g, " ").trim();
  if (t.length <= maxChars) return t;
  return `${t.slice(0, Math.max(1, maxChars - 1)).trimEnd()}…`;
}

function toTokens(input: string): string[] {
  return Array.from(
    new Set(
      input
        .toLowerCase()
        .split(/[^a-z0-9_]+/g)
        .map((s) => s.trim())
        .filter((s) => s.length > 1)
    )
  );
}

function detectProject(text: string): string {
  const hay = text.toLowerCase();
  for (const [project, signals] of Object.entries(PROJECT_SIGNALS)) {
    if (signals.some((signal) => hay.includes(signal))) return project;
  }
  return "other";
}

function estimateImportance(text: string): number {
  const hay = text.toLowerCase();
  let score = 1;

  if (/[A-Z0-9_]{8,}/.test(text)) score += 1;
  if (/https?:\/\//i.test(text) || /\/[a-z0-9\-_/]+/i.test(text)) score += 1;
  if (/(blocked|failing|failed|urgent|critical|incident|down)/i.test(text)) score += 1;
  if (/(deployed|shipped|launched|completed|phase|rolled out|migrated)/i.test(text)) score += 1;
  if (IMPORTANCE_KEYWORDS.some((keyword) => hay.includes(keyword))) score += 1;

  return clamp(score, 1, 5);
}

function inferTags(text: string, extraTags: string[]): string[] {
  const tags = new Set<string>(extraTags.map((t) => t.trim().toLowerCase()).filter(Boolean));

  for (const keyword of IMPORTANCE_KEYWORDS) {
    if (text.toLowerCase().includes(keyword)) tags.add(keyword);
  }

  const project = detectProject(text);
  if (project !== "other") tags.add(project);

  return Array.from(tags).slice(0, 8);
}

function isLikelyImportantText(text: string): boolean {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) return false;
  if (normalized.length >= 220) return true;
  if (/(http|api|endpoint|token|key|env|deployed|phase|urgent|error|fix|blocked|checkout|quote|merchant|oauth)/i.test(normalized)) {
    return true;
  }
  if (/\b(-100\d{7,}|\d{2,}\.\d{2,}\.\d{2,}\.\d{2,}|pm2|docker|postgres|stripe)\b/i.test(normalized)) {
    return true;
  }
  return false;
}

function readAllEvents(chatId: string | number): BrainEvent[] {
  const { eventsPath } = getBrainDirs(chatId);
  if (!fs.existsSync(eventsPath)) return [];

  const lines = fs.readFileSync(eventsPath, "utf8").split("\n").filter(Boolean);
  const out: BrainEvent[] = [];

  for (const line of lines) {
    try {
      const parsed = JSON.parse(line) as BrainEvent;
      if (parsed?.id && parsed?.timestamp && parsed?.type && parsed?.title) {
        out.push({
          ...parsed,
          tags: Array.isArray(parsed.tags) ? parsed.tags : [],
          importance: clamp(Number(parsed.importance) || 1, 1, 5),
        });
      }
    } catch {
      // tolerate malformed historical lines
    }
  }

  return out.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

export function appendBrainEvent(
  chatId: string | number,
  input: Omit<Partial<BrainEvent>, "id" | "timestamp"> & { title: string; type: BrainEventType }
): BrainEvent {
  const dirs = getBrainDirs(chatId);
  const now = new Date().toISOString();
  const baseText = `${input.title || ""} ${input.detail || ""}`.trim();

  const event: BrainEvent = {
    id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: now,
    type: input.type,
    title: truncate(input.title, MAX_EVENT_TITLE_CHARS),
    detail: input.detail ? truncate(input.detail, MAX_EVENT_DETAIL_CHARS) : undefined,
    tags: inferTags(baseText, input.tags || []),
    project: input.project || detectProject(baseText),
    importance: clamp(input.importance ?? estimateImportance(baseText), 1, 5),
    source: input.source || "runtime",
  };

  fs.appendFileSync(dirs.eventsPath, JSON.stringify(event) + "\n", "utf8");
  return event;
}

function summarizeTitle(text: string, fallback: string): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (!clean) return fallback;
  const firstSentence = clean.split(/(?<=[.!?])\s+/)[0] || clean;
  return truncate(firstSentence, MAX_EVENT_TITLE_CHARS);
}

export function captureBrainUserRequest(chatId: string | number, text: string, source = "telegram"): BrainEvent | null {
  if (!isChowPrimaryChat(chatId)) return null;
  if (!isLikelyImportantText(text)) return null;

  return appendBrainEvent(chatId, {
    type: "user_request",
    title: summarizeTitle(text, "User request"),
    detail: truncate(text, MAX_EVENT_DETAIL_CHARS),
    source,
    tags: ["request"],
  });
}

export function captureBrainAssistantResult(chatId: string | number, text: string, source = "telegram"): BrainEvent | null {
  if (!isChowPrimaryChat(chatId)) return null;
  if (!isLikelyImportantText(text)) return null;

  return appendBrainEvent(chatId, {
    type: "assistant_result",
    title: summarizeTitle(text, "Assistant result"),
    detail: truncate(text, MAX_EVENT_DETAIL_CHARS),
    source,
    tags: ["result"],
  });
}

export function addManualBrainNote(chatId: string | number, note: string, source = "brain-command"): BrainEvent | null {
  if (!isChowPrimaryChat(chatId)) return null;
  const trimmed = note.trim();
  if (!trimmed) return null;

  return appendBrainEvent(chatId, {
    type: "manual_note",
    title: summarizeTitle(trimmed, "Manual note"),
    detail: truncate(trimmed, MAX_EVENT_DETAIL_CHARS),
    source,
    tags: ["manual"],
    importance: estimateImportance(trimmed),
  });
}

export function listBrainEvents(chatId: string | number, limit = 8): BrainEvent[] {
  return readAllEvents(chatId).slice(-Math.max(1, limit)).reverse();
}

function scoreEvent(event: BrainEvent, query: string, queryTokens: string[], nowMs: number): number {
  const hay = `${event.title} ${event.detail || ""} ${event.project} ${(event.tags || []).join(" ")}`.toLowerCase();

  let relevance = 0;
  if (queryTokens.length > 0) {
    const hitCount = queryTokens.filter((token) => hay.includes(token)).length;
    const overlap = hitCount / queryTokens.length;
    const phraseBonus = query && hay.includes(query.toLowerCase()) ? 0.3 : 0;
    relevance = clamp(overlap + phraseBonus, 0, 1);
  }

  const ageMs = Math.max(0, nowMs - new Date(event.timestamp).getTime());
  const ageDays = ageMs / (1000 * 60 * 60 * 24);
  const recency = 1 / (1 + ageDays / 7);

  const importance = clamp(event.importance / 5, 0, 1);
  const priority = PROJECT_PRIORITY[event.project] ?? PROJECT_PRIORITY.other;

  if (queryTokens.length === 0) {
    return 0.45 * recency + 0.35 * importance + 0.2 * priority;
  }

  return 0.42 * relevance + 0.28 * recency + 0.18 * importance + 0.12 * priority;
}

export function searchBrainEvents(chatId: string | number, query: string, limit = 8): Array<BrainEvent & { score: number }> {
  const events = readAllEvents(chatId);
  const trimmed = query.trim();
  const tokens = toTokens(trimmed);
  const nowMs = Date.now();

  return events
    .map((event) => ({ event, score: scoreEvent(event, trimmed, tokens, nowMs) }))
    .filter(({ event, score }) => {
      if (!trimmed) return score > 0;
      return score >= 0.2 || `${event.title} ${event.detail || ""}`.toLowerCase().includes(trimmed.toLowerCase());
    })
    .sort((a, b) => b.score - a.score || b.event.timestamp.localeCompare(a.event.timestamp))
    .slice(0, Math.max(1, limit))
    .map(({ event, score }) => ({ ...event, score: Number(score.toFixed(3)) }));
}

export function formatBrainEventLine(event: BrainEvent, index?: number): string {
  const date = event.timestamp.slice(0, 10);
  const time = event.timestamp.slice(11, 16);
  const prefix = typeof index === "number" ? `${index + 1}. ` : "- ";
  const scoreBlock = event.importance ? ` | imp:${event.importance}` : "";
  const tags = event.tags?.length ? ` | tags:${event.tags.slice(0, 3).join(",")}` : "";
  const detail = event.detail ? ` — ${event.detail}` : "";
  return `${prefix}[${date} ${time}] (${event.project}/${event.type}${scoreBlock}${tags}) ${event.title}${detail}`;
}

export function consolidateBrainDay(
  chatId: string | number,
  options?: { date?: string; reason?: string; includeEventLog?: boolean }
): { date: string; path: string; eventCount: number } {
  const date = options?.date || utcDate();
  const dirs = getBrainDirs(chatId);
  const all = readAllEvents(chatId);
  const events = all.filter((event) => event.timestamp.startsWith(date));

  const byProject = new Map<string, BrainEvent[]>();
  for (const event of events) {
    const bucket = byProject.get(event.project) || [];
    bucket.push(event);
    byProject.set(event.project, bucket);
  }

  const topHighlights = [...events]
    .sort((a, b) => b.importance - a.importance || b.timestamp.localeCompare(a.timestamp))
    .slice(0, 12);

  const projectBlocks = Array.from(byProject.entries())
    .sort((a, b) => b[1].length - a[1].length)
    .map(([project, projectEvents]) => {
      const lines = [...projectEvents]
        .sort((a, b) => b.importance - a.importance || b.timestamp.localeCompare(a.timestamp))
        .slice(0, 6)
        .map((event) => `- ${formatBrainEventLine(event).replace(/^-\s*/, "")}`)
        .join("\n");
      return `### ${project} (${projectEvents.length})\n${lines || "- (none)"}`;
    });

  const content = [
    `# Brain Consolidation — ${date}`,
    "",
    `- Generated: ${new Date().toISOString()}`,
    `- Reason: ${options?.reason || "daily"}`,
    `- Events today: ${events.length}`,
    "",
    "## Top Highlights",
    topHighlights.length
      ? topHighlights.map((event) => `- ${formatBrainEventLine(event).replace(/^-\s*/, "")}`).join("\n")
      : "- No notable events captured today.",
    "",
    "## By Project",
    projectBlocks.length ? projectBlocks.join("\n\n") : "- No project buckets for this date.",
    "",
  ].join("\n");

  const outPath = path.join(dirs.consolidatedDir, `${date}.md`);
  fs.writeFileSync(outPath, content, "utf8");

  if (options?.includeEventLog) {
    appendBrainEvent(chatId, {
      type: "daily_consolidation",
      title: `Consolidated brain events for ${date}`,
      detail: `${events.length} events summarized into ${path.relative(BOT_ROOT, outPath)}`,
      project: "chow",
      source: options.reason || "daily",
      importance: 2,
      tags: ["consolidation"],
    });
  }

  return { date, path: outPath, eventCount: events.length };
}

export function maybeRunDailyBrainConsolidation(
  chatId: string | number,
  reason = "auto"
): { ran: boolean; date: string; path?: string; eventCount?: number } {
  if (!isChowPrimaryChat(chatId)) {
    return { ran: false, date: utcDate() };
  }

  const dirs = getBrainDirs(chatId);
  const today = utcDate();

  if (fs.existsSync(dirs.markerPath)) {
    const last = fs.readFileSync(dirs.markerPath, "utf8").trim();
    if (last === today) {
      return { ran: false, date: today };
    }
  }

  const consolidated = consolidateBrainDay(chatId, {
    date: today,
    reason,
    includeEventLog: false,
  });

  fs.writeFileSync(dirs.markerPath, today + "\n", "utf8");

  return {
    ran: true,
    date: today,
    path: consolidated.path,
    eventCount: consolidated.eventCount,
  };
}

export function forceDailyBrainConsolidation(
  chatId: string | number,
  reason = "manual"
): { date: string; path: string; eventCount: number } {
  const today = utcDate();
  const dirs = getBrainDirs(chatId);
  const consolidated = consolidateBrainDay(chatId, {
    date: today,
    reason,
    includeEventLog: true,
  });
  fs.writeFileSync(dirs.markerPath, today + "\n", "utf8");
  return consolidated;
}

function readLatestConsolidations(chatId: string | number, count = 2): Array<{ file: string; content: string }> {
  const { consolidatedDir } = getBrainDirs(chatId);
  if (!fs.existsSync(consolidatedDir)) return [];

  const files = fs
    .readdirSync(consolidatedDir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .slice(-Math.max(1, count));

  return files.map((file) => ({
    file,
    content: fs.readFileSync(path.join(consolidatedDir, file), "utf8").trim(),
  }));
}

export function getBrainContextSnippet(chatId: string | number, options?: { eventLimit?: number; consolidationCount?: number }): string {
  const recent = listBrainEvents(chatId, options?.eventLimit ?? 6);
  const consolidations = readLatestConsolidations(chatId, options?.consolidationCount ?? 1);

  const recentSection = recent.length
    ? recent.map((event) => formatBrainEventLine(event).replace(/^-\s*/, "- ")).join("\n")
    : "- No structured events yet.";

  const consolidationSection = consolidations.length
    ? consolidations
        .map((item) => `### ${item.file}\n\n${truncate(item.content, 1800)}`)
        .join("\n\n---\n\n")
    : "(none)";

  return [
    "## Structured Event Memory (Phase 3)",
    "",
    recentSection,
    "",
    "## Daily Consolidations",
    "",
    consolidationSection,
  ].join("\n");
}

export function getBrainStatus(chatId: string | number): BrainStatus {
  const events = readAllEvents(chatId);
  const dirs = getBrainDirs(chatId);

  let lastConsolidatedDate: string | null = null;
  if (fs.existsSync(dirs.markerPath)) {
    const value = fs.readFileSync(dirs.markerPath, "utf8").trim();
    lastConsolidatedDate = value || null;
  }

  const latestConsolidation = readLatestConsolidations(chatId, 1)[0];

  return {
    chatId: String(chatId),
    eventCount: events.length,
    lastEventAt: events.length ? events[events.length - 1].timestamp : null,
    lastConsolidatedDate,
    latestConsolidationPath: latestConsolidation
      ? path.join(getBrainDirs(chatId).consolidatedDir, latestConsolidation.file)
      : null,
  };
}
