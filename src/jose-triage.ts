import * as fs from "node:fs";

export type JoseCategory =
  | "personal"
  | "business"
  | "community"
  | "news"
  | "dev"
  | "finance"
  | "crypto"
  | "shopping"
  | "travel"
  | "health"
  | "other";

export interface JoseSnapshotDialog {
  id: string;
  title: string;
  unreadCount: number;
  isChannel?: boolean;
  isGroup?: boolean;
  isUser?: boolean;
  username?: string | null;
  lastMessageAt?: string | null;
  previews?: string[];
}

export interface JoseSnapshot {
  generatedAt?: string;
  totals?: {
    dialogsFetched?: number;
    unreadDialogs?: number;
    groups?: number;
    channels?: number;
    users?: number;
  };
  dialogs?: JoseSnapshotDialog[];
  topUnread?: JoseSnapshotDialog[];
}

export interface TriageEntities {
  urls: string[];
  tickers: string[];
  cas: string[];
  emails: string[];
}

export interface TriageItem {
  dialog: JoseSnapshotDialog;
  previewText: string;
  category: JoseCategory;
  urgencyScore: number;
  noveltyKey: string;
  entities: TriageEntities;
  reasons: string[];
}

const CATEGORY_KEYWORDS: Array<{ category: JoseCategory; words: string[] }> = [
  { category: "business", words: ["invoice", "client", "contract", "proposal", "meeting", "deadline", "project", "vendor", "sales"] },
  { category: "dev", words: ["bug", "deploy", "api", "repo", "github", "release", "incident", "database", "server", "typescript", "python"] },
  { category: "finance", words: ["bank", "payment", "wire", "tax", "budget", "receipt", "accounting", "stripe", "paypal"] },
  { category: "crypto", words: ["sol", "eth", "btc", "token", "dex", "swap", "pump", "contract address", "liquidity", "rug"] },
  { category: "news", words: ["breaking", "alert", "update", "headline", "report", "announced", "press"] },
  { category: "shopping", words: ["order", "shipment", "tracking", "delivery", "coupon", "receipt", "store"] },
  { category: "travel", words: ["flight", "hotel", "booking", "reservation", "gate", "check-in", "itinerary"] },
  { category: "health", words: ["doctor", "clinic", "appointment", "medical", "lab", "prescription"] },
  { category: "community", words: ["event", "meetup", "volunteer", "community", "group", "announcement"] },
  { category: "personal", words: ["family", "mom", "dad", "birthday", "dinner", "home", "friend"] },
];

const URGENT_KEYWORDS = [
  "urgent",
  "asap",
  "immediately",
  "now",
  "critical",
  "blocked",
  "problem",
  "issue",
  "failed",
  "failure",
  "deadline",
  "action required",
  "payment due",
  "expiring",
  "security",
  "breach",
  "fraud",
  "alert",
];

function safeLower(value: unknown): string {
  return String(value ?? "").toLowerCase();
}

function minutesSince(isoMaybe?: string | null): number | null {
  if (!isoMaybe) return null;
  const ts = Date.parse(isoMaybe);
  if (Number.isNaN(ts)) return null;
  return Math.max(0, (Date.now() - ts) / 60000);
}

function normalizeForFingerprint(text: string): string {
  return text
    .toLowerCase()
    .replace(/https?:\/\/\S+/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function extractEntities(text: string): TriageEntities {
  const urls = Array.from(new Set(text.match(/https?:\/\/[^\s)]+/gi) ?? []));
  const tickers = Array.from(new Set((text.match(/\$[A-Za-z][A-Za-z0-9]{1,9}\b/g) ?? []).map((x) => x.toUpperCase())));
  const cas = Array.from(new Set(text.match(/\b[1-9A-HJ-NP-Za-km-z]{32,44}\b/g) ?? []));
  const emails = Array.from(new Set(text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}/g) ?? []));
  return { urls, tickers, cas, emails };
}

function classifyCategory(seedText: string, dialog: JoseSnapshotDialog): JoseCategory {
  const hay = `${safeLower(dialog.title)} ${safeLower(dialog.username)} ${safeLower(seedText)}`;
  let best: { category: JoseCategory; hits: number } = { category: "other", hits: 0 };

  for (const row of CATEGORY_KEYWORDS) {
    const hits = row.words.reduce((count, word) => (hay.includes(word) ? count + 1 : count), 0);
    if (hits > best.hits) best = { category: row.category, hits };
  }

  if (best.hits > 0) return best.category;
  if (dialog.isUser) return "personal";
  if (dialog.isGroup) return "community";
  return "other";
}

function noveltyKey(dialog: JoseSnapshotDialog, previewText: string): string {
  const normalized = normalizeForFingerprint(previewText);
  if (!normalized) return `${dialog.id}:no-preview`;
  const tokens = normalized.split(" ").filter((t) => t.length >= 4).slice(0, 10);
  return tokens.join("|") || `${dialog.id}:${normalized.slice(0, 48)}`;
}

function computeUrgency(dialog: JoseSnapshotDialog, previewText: string, entities: TriageEntities): { score: number; reasons: string[] } {
  let score = 0;
  const reasons: string[] = [];

  const unread = Number(dialog.unreadCount || 0);
  if (unread > 0) {
    score += Math.min(40, Math.log2(unread + 1) * 10);
    reasons.push(`unread=${unread}`);
  }

  const ageMin = minutesSince(dialog.lastMessageAt ?? null);
  if (ageMin !== null) {
    if (ageMin <= 15) {
      score += 25;
      reasons.push("fresh<=15m");
    } else if (ageMin <= 60) {
      score += 15;
      reasons.push("fresh<=1h");
    } else if (ageMin <= 240) {
      score += 8;
      reasons.push("fresh<=4h");
    }
  }

  const lowered = safeLower(previewText);
  const urgentHit = URGENT_KEYWORDS.find((word) => lowered.includes(word));
  if (urgentHit) {
    score += 22;
    reasons.push(`keyword:${urgentHit}`);
  }

  if (entities.urls.length) {
    score += 4;
    reasons.push(`links=${entities.urls.length}`);
  }
  if (entities.cas.length || entities.tickers.length) {
    score += 4;
    reasons.push(`market-signals=${entities.cas.length + entities.tickers.length}`);
  }

  if (dialog.isUser) {
    score += 5;
    reasons.push("dm-priority");
  }

  return { score: Math.round(score), reasons };
}

export function loadJoseSnapshot(snapshotPath: string): JoseSnapshot | null {
  if (!fs.existsSync(snapshotPath)) return null;
  try {
    const raw = fs.readFileSync(snapshotPath, "utf8");
    return JSON.parse(raw) as JoseSnapshot;
  } catch {
    return null;
  }
}

export function triageSnapshot(snapshot: JoseSnapshot): TriageItem[] {
  const dialogs = Array.isArray(snapshot.dialogs) && snapshot.dialogs.length
    ? snapshot.dialogs
    : Array.isArray(snapshot.topUnread)
      ? snapshot.topUnread
      : [];

  const items: TriageItem[] = dialogs.map((dialog) => {
    const previewText = (dialog.previews ?? []).join(" \n ").slice(0, 800);
    const entities = extractEntities(`${dialog.title || ""} ${previewText}`);
    const category = classifyCategory(previewText, dialog);
    const urgency = computeUrgency(dialog, previewText, entities);

    return {
      dialog,
      previewText,
      category,
      urgencyScore: urgency.score,
      noveltyKey: noveltyKey(dialog, previewText),
      entities,
      reasons: urgency.reasons,
    };
  });

  const dedup = new Map<string, TriageItem>();
  for (const item of items) {
    const existing = dedup.get(item.noveltyKey);
    if (!existing || item.urgencyScore > existing.urgencyScore) {
      dedup.set(item.noveltyKey, item);
    }
  }

  return Array.from(dedup.values()).sort((a, b) => b.urgencyScore - a.urgencyScore);
}

export function buildBrief(items: TriageItem[], generatedAt?: string): string {
  const top = items.slice(0, 12);
  const categoryCounts = new Map<JoseCategory, number>();
  for (const item of items) {
    categoryCounts.set(item.category, (categoryCounts.get(item.category) ?? 0) + 1);
  }

  const categoryLine = Array.from(categoryCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([category, count]) => `${category}:${count}`)
    .join(" | ");

  const lines = top.map((item, idx) => {
    const title = item.dialog.title || item.dialog.username || item.dialog.id;
    const unread = item.dialog.unreadCount || 0;
    const preview = item.previewText ? item.previewText.slice(0, 120).replace(/\s+/g, " ") : "(no preview)";
    return `${idx + 1}. [${item.category}] ${title} | score=${item.urgencyScore} | unread=${unread} | ${preview}`;
  });

  return [
    "--- JOSE TRIAGE BRIEF ---",
    `Generated: ${generatedAt || "unknown"}`,
    `Category mix: ${categoryLine || "n/a"}`,
    "Priority queue:",
    ...lines,
    "Caveat: snapshot-based view, not guaranteed full real-time coverage.",
    "--- END JOSE TRIAGE BRIEF ---",
  ].join("\n");
}

export function buildUrgentDigest(items: TriageItem[], limit = 10): string {
  const urgent = items.filter((item) => item.urgencyScore >= 35).slice(0, limit);
  if (!urgent.length) {
    return "No high-urgency items in current snapshot.";
  }

  return urgent
    .map((item, idx) => {
      const title = item.dialog.title || item.dialog.username || item.dialog.id;
      const preview = item.previewText ? item.previewText.slice(0, 140).replace(/\s+/g, " ") : "(no preview)";
      return `${idx + 1}. ${title} [${item.category}] score=${item.urgencyScore} reasons=${item.reasons.join(",")}\n   source=dialog:${item.dialog.id} preview="${preview}"`;
    })
    .join("\n");
}

export type JoseLoadMode = "normal" | "high" | "flood";

export interface JoseTopicLane {
  category: JoseCategory;
  count: number;
  urgentCount: number;
  unreadTotal: number;
  topDialogs: string[];
}

export interface JoseTriageState {
  generatedAt: string;
  loadMode: JoseLoadMode;
  loadReasons: string[];
  totals: {
    dialogs: number;
    unreadDialogs: number;
    urgentItems: number;
  };
  categoryCounts: Record<string, number>;
  topicLanes: JoseTopicLane[];
  priorityQueue: Array<{
    dialogId: string;
    title: string;
    category: JoseCategory;
    urgencyScore: number;
    unreadCount: number;
    reasons: string[];
    preview: string;
    noveltyKey: string;
    lastMessageAt: string | null | undefined;
  }>;
}

export function evaluateLoadMode(snapshot: JoseSnapshot, items: TriageItem[]): { mode: JoseLoadMode; reasons: string[] } {
  const unreadDialogs = Number(snapshot?.totals?.unreadDialogs ?? items.filter((i) => (i.dialog.unreadCount || 0) > 0).length);
  const maxUnread = items.reduce((max, item) => Math.max(max, Number(item.dialog.unreadCount || 0)), 0);
  const urgentItems = items.filter((item) => item.urgencyScore >= 35).length;
  const reasons: string[] = [];

  let mode: JoseLoadMode = "normal";
  if (unreadDialogs >= 40 || urgentItems >= 16 || maxUnread >= 1000) {
    mode = "flood";
  } else if (unreadDialogs >= 20 || urgentItems >= 8 || maxUnread >= 250) {
    mode = "high";
  }

  reasons.push(`unreadDialogs=${unreadDialogs}`);
  reasons.push(`urgentItems=${urgentItems}`);
  reasons.push(`maxUnread=${maxUnread}`);
  return { mode, reasons };
}

export function buildTopicLanes(items: TriageItem[]): JoseTopicLane[] {
  const map = new Map<JoseCategory, { count: number; urgentCount: number; unreadTotal: number; dialogs: Set<string> }>();

  for (const item of items) {
    const existing = map.get(item.category) ?? { count: 0, urgentCount: 0, unreadTotal: 0, dialogs: new Set<string>() };
    existing.count += 1;
    if (item.urgencyScore >= 35) existing.urgentCount += 1;
    existing.unreadTotal += Number(item.dialog.unreadCount || 0);
    const label = item.dialog.title || item.dialog.username || item.dialog.id;
    if (existing.dialogs.size < 3) existing.dialogs.add(label);
    map.set(item.category, existing);
  }

  return Array.from(map.entries())
    .map(([category, agg]) => ({
      category,
      count: agg.count,
      urgentCount: agg.urgentCount,
      unreadTotal: agg.unreadTotal,
      topDialogs: Array.from(agg.dialogs),
    }))
    .sort((a, b) => {
      if (b.urgentCount !== a.urgentCount) return b.urgentCount - a.urgentCount;
      if (b.count !== a.count) return b.count - a.count;
      return b.unreadTotal - a.unreadTotal;
    });
}

export function buildTriageState(snapshot: JoseSnapshot, items: TriageItem[]): JoseTriageState {
  const load = evaluateLoadMode(snapshot, items);
  const topicLanes = buildTopicLanes(items);
  const categoryCounts: Record<string, number> = {};
  for (const lane of topicLanes) categoryCounts[lane.category] = lane.count;

  return {
    generatedAt: snapshot.generatedAt || new Date().toISOString(),
    loadMode: load.mode,
    loadReasons: load.reasons,
    totals: {
      dialogs: Number(snapshot?.totals?.dialogsFetched ?? items.length),
      unreadDialogs: Number(snapshot?.totals?.unreadDialogs ?? items.filter((i) => (i.dialog.unreadCount || 0) > 0).length),
      urgentItems: items.filter((item) => item.urgencyScore >= 35).length,
    },
    categoryCounts,
    topicLanes,
    priorityQueue: items.slice(0, 40).map((item) => ({
      dialogId: item.dialog.id,
      title: item.dialog.title || item.dialog.username || item.dialog.id,
      category: item.category,
      urgencyScore: item.urgencyScore,
      unreadCount: Number(item.dialog.unreadCount || 0),
      reasons: item.reasons,
      preview: item.previewText.slice(0, 220),
      noveltyKey: item.noveltyKey,
      lastMessageAt: item.dialog.lastMessageAt,
    })),
  };
}

export function loadJoseTriageState(statePath: string): JoseTriageState | null {
  if (!fs.existsSync(statePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(statePath, "utf8")) as JoseTriageState;
  } catch {
    return null;
  }
}

export function buildTopicsDigestFromState(state: JoseTriageState): string {
  if (!state.topicLanes.length) return "No topic lanes available in current triage state.";
  return [
    `Topics snapshot: ${state.generatedAt}`,
    `Load mode: ${state.loadMode} (${state.loadReasons.join(", ")})`,
    "Top topic lanes:",
    ...state.topicLanes.slice(0, 8).map((lane, idx) =>
      `${idx + 1}. ${lane.category} | items=${lane.count} urgent=${lane.urgentCount} unread=${lane.unreadTotal} | lanes=${lane.topDialogs.join("; ")}`
    ),
  ].join("\n");
}

export function askFromSnapshot(items: TriageItem[], query: string, limit = 5): string {
  const q = query
    .toLowerCase()
    .split(/\s+/)
    .map((t) => t.trim())
    .filter((t) => t.length >= 2);

  if (!q.length) return "Please provide a specific query after /ask.";

  const scored = items
    .map((item) => {
      const hay = `${item.dialog.title} ${item.dialog.username || ""} ${item.previewText}`.toLowerCase();
      const overlap = q.reduce((sum, token) => (hay.includes(token) ? sum + 1 : sum), 0);
      const score = overlap * 20 + Math.min(20, item.urgencyScore / 2);
      return { item, score, overlap };
    })
    .filter((row) => row.overlap > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);

  if (!scored.length) {
    return `No matching items found for: "${query}" in current snapshot.`;
  }

  return [
    `Ask query: "${query}"`,
    "Top grounded matches:",
    ...scored.map((row, idx) => {
      const item = row.item;
      const title = item.dialog.title || item.dialog.username || item.dialog.id;
      const preview = item.previewText ? item.previewText.slice(0, 180).replace(/\s+/g, " ") : "(no preview)";
      return `${idx + 1}. ${title} [${item.category}] match=${row.score}\n   source=dialog:${item.dialog.id} last=${item.dialog.lastMessageAt || "unknown"}\n   preview="${preview}"`;
    }),
  ].join("\n");
}
