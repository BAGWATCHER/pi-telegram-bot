// ─── Persistent Memory System ─────────────────────────────────────────────────
// Two-tier memory: protected identity + rolling session summaries.
//
// memory/<chatId>/identity.md   — NEVER auto-overwritten. Only user /memory can edit.
// memory/<chatId>/summaries.md  — Append-only rolling window of last N session summaries.
//
// On session rotation: summarize the session, APPEND to summaries.md, trim to last MAX_SUMMARIES.
// System prompt loads: identity.md + summaries.md (last 5).
// Identity is sacred — rotation can never destroy it.

import * as fs from "node:fs";
import * as path from "node:path";
import {
  createAgentSession,
  SessionManager,
} from "@mariozechner/pi-coding-agent";
import { createChowRuntime, pinSessionModel } from "./pi-session.js";
import {
  appendBrainEvent,
  getBrainContextSnippet,
  isChowPrimaryChat as isChowPrimaryBrainChat,
  maybeRunDailyBrainConsolidation,
} from "./chow-brain.js";
import { logMemoryPromotion } from "./learning-log.js";

const BOT_ROOT = process.cwd();
const MEMORY_DIR = path.join(BOT_ROOT, "memory");
const SESSIONS_DIR = path.join(BOT_ROOT, "sessions");
const ARCHIVE_DIR = path.join(BOT_ROOT, "sessions", "archive");
const MAX_SESSION_LINES = 200; // auto-rotate after this many jsonl lines
const MAX_SUMMARIES = 5; // keep last N session summaries
const SUMMARY_SEPARATOR = "\n\n---\n\n";
const MAX_SECOND_BRAIN_CONTEXT_CHARS = 6000;

fs.mkdirSync(MEMORY_DIR, { recursive: true });
fs.mkdirSync(ARCHIVE_DIR, { recursive: true });

// ─── Memory directory per chat ────────────────────────────────────────────────

function getChatMemoryDir(chatId: string | number): string {
  const dir = path.join(MEMORY_DIR, String(chatId));
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

export function getIdentityPath(chatId: string | number): string {
  return path.join(getChatMemoryDir(chatId), "identity.md");
}

export function getSummariesPath(chatId: string | number): string {
  return path.join(getChatMemoryDir(chatId), "summaries.md");
}

function getSecondBrainDir(chatId: string | number): string {
  return path.join(getChatMemoryDir(chatId), "second-brain");
}

function sectionFromMarkdown(md: string, heading: string): string {
  const header = `## ${heading}`;
  const start = md.indexOf(header);
  if (start < 0) return "";
  const bodyStart = md.indexOf("\n", start);
  if (bodyStart < 0) return "";
  const nextHeader = md.indexOf("\n## ", bodyStart + 1);
  const bodyEnd = nextHeader >= 0 ? nextHeader : md.length;
  return md.slice(bodyStart + 1, bodyEnd).trim();
}

function readSecondBrainContext(chatId: string | number): string {
  if (!isChowPrimaryBrainChat(chatId)) return "";

  const sections: string[] = [];
  const contextPath = path.join(getSecondBrainDir(chatId), "context.md");
  if (fs.existsSync(contextPath)) {
    const raw = fs.readFileSync(contextPath, "utf8").trim();
    if (raw) sections.push(raw);
  }

  const structured = getBrainContextSnippet(chatId, { eventLimit: 8, consolidationCount: 1 }).trim();
  if (structured) {
    const alreadyIncluded = sections.some((section) => section.includes("## Structured Event Memory (Phase 3)"));
    if (!alreadyIncluded) sections.push(structured);
  }

  const combined = sections.join("\n\n---\n\n").trim();
  if (!combined) return "";
  if (combined.length <= MAX_SECOND_BRAIN_CONTEXT_CHARS) return combined;
  return `${combined.slice(0, MAX_SECOND_BRAIN_CONTEXT_CHARS)}\n\n[second-brain context truncated]`;
}

function syncChowSecondBrain(chatId: string | number, note: string): void {
  if (!isChowPrimaryBrainChat(chatId)) return;

  const identity = readIdentity(chatId);
  if (!identity.trim()) return;

  const summaries = readSummaries(chatId);
  const brainDir = getSecondBrainDir(chatId);
  const dailyDir = path.join(brainDir, "daily");

  fs.mkdirSync(brainDir, { recursive: true });
  fs.mkdirSync(dailyDir, { recursive: true });

  const nowIso = new Date().toISOString();
  const today = nowIso.slice(0, 10);

  // Lazy daily scheduler: run exactly once/day when Chow is active.
  maybeRunDailyBrainConsolidation(chatId, "sync");

  const userPrefs = sectionFromMarkdown(identity, "User preferences");
  const projects = sectionFromMarkdown(identity, "Projects");
  const server = sectionFromMarkdown(identity, "Server");

  const soul = `# SOUL.md

## Identity
- Name: Mr Chow
- Mode: Server-side operator + coding/research assistant
- Scope: Chow-only implementation

## Non-Negotiables
- Protect identity continuity and operational memory
- Keep actions verifiable and reversible when possible
- Keep Jose isolated unless explicitly requested

## Current Runtime Snapshot
${server ? server : "- Server section unavailable in identity snapshot"}

## Last Reflected
- ${nowIso}
`;

  const user = `# USER.md

## Preferences Snapshot
${userPrefs ? userPrefs : "- User preference section unavailable in identity snapshot"}

## Last Reflected
- ${nowIso}
`;

  const memory = `# MEMORY.md

## Source of Truth
- Protected identity: ${getIdentityPath(chatId)}
- Rolling summaries: ${getSummariesPath(chatId)}

## Projects Snapshot
${projects ? projects : "- Projects section unavailable in identity snapshot"}

## Recent Summary Window
${summaries.length > 0 ? summaries.join("\n\n---\n\n") : "- No summaries yet"}

## Last Reflected
- ${nowIso}
`;

  fs.writeFileSync(path.join(brainDir, "SOUL.md"), soul.trim() + "\n", "utf8");
  fs.writeFileSync(path.join(brainDir, "USER.md"), user.trim() + "\n", "utf8");
  fs.writeFileSync(path.join(brainDir, "MEMORY.md"), memory.trim() + "\n", "utf8");

  const recentDailyFiles = fs
    .readdirSync(dailyDir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .slice(-3);

  const recentDailyBlocks = recentDailyFiles.map((f) => {
    const content = fs.readFileSync(path.join(dailyDir, f), "utf8").trim();
    return `### ${f}\n\n${content}`;
  });

  const structuredBrain = getBrainContextSnippet(chatId, { eventLimit: 8, consolidationCount: 1 });

  const context = `# Chow Context Bundle

${soul.trim()}

---

${user.trim()}

---

${memory.trim()}

---

## Recent Daily Logs

${recentDailyBlocks.length > 0 ? recentDailyBlocks.join("\n\n---\n\n") : "(none)"}

---

${structuredBrain}
`;
  fs.writeFileSync(path.join(brainDir, "context.md"), context, "utf8");

  const dailyPath = path.join(dailyDir, `${today}.md`);
  const dailyEntry = `\n## ${nowIso}\n- ${note}\n- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.\n`;

  if (!fs.existsSync(dailyPath)) {
    fs.writeFileSync(dailyPath, `# Daily Log — ${today}\n${dailyEntry}`, "utf8");
  } else {
    fs.appendFileSync(dailyPath, dailyEntry, "utf8");
  }
}

// Legacy path for migration
function getLegacyMemoryPath(chatId: string | number): string {
  return path.join(MEMORY_DIR, `${chatId}.md`);
}

// ─── Migration: move old memory/<chatId>.md → memory/<chatId>/identity.md ─────

function migrateIfNeeded(chatId: string | number): void {
  const legacy = getLegacyMemoryPath(chatId);
  const identity = getIdentityPath(chatId);
  if (fs.existsSync(legacy) && !fs.existsSync(identity)) {
    const content = fs.readFileSync(legacy, "utf8");
    fs.writeFileSync(identity, content, "utf8");
    fs.renameSync(legacy, legacy + ".migrated");
    console.log(`[memory] Migrated ${legacy} → ${identity}`);
  }
}

// ─── Read/write helpers ───────────────────────────────────────────────────────

export function readIdentity(chatId: string | number): string {
  migrateIfNeeded(chatId);
  const p = getIdentityPath(chatId);
  if (!fs.existsSync(p)) return "";
  return fs.readFileSync(p, "utf8").trim();
}

export function writeIdentity(chatId: string | number, content: string): void {
  migrateIfNeeded(chatId);
  fs.writeFileSync(getIdentityPath(chatId), content.trim() + "\n", "utf8");
  logMemoryPromotion({
    chat_id: String(chatId),
    promoted_to: "identity",
    summary: `Identity updated at ${getIdentityPath(chatId)}`,
    source: "writeIdentity",
  });
}

export function readSummaries(chatId: string | number): string[] {
  const p = getSummariesPath(chatId);
  if (!fs.existsSync(p)) return [];
  const content = fs.readFileSync(p, "utf8").trim();
  if (!content) return [];
  return content.split(SUMMARY_SEPARATOR).filter(Boolean);
}

function appendSummary(chatId: string | number, summary: string): void {
  const summaries = readSummaries(chatId);
  summaries.push(summary.trim());
  // Keep only last MAX_SUMMARIES
  const trimmed = summaries.slice(-MAX_SUMMARIES);
  fs.writeFileSync(
    getSummariesPath(chatId),
    trimmed.join(SUMMARY_SEPARATOR) + "\n",
    "utf8"
  );
  logMemoryPromotion({
    chat_id: String(chatId),
    promoted_to: "summary",
    summary: summary.trim().slice(0, 300),
    source: "session-rotation",
  });
}

// ─── Combined memory read (for backward compat) ──────────────────────────────

/** @deprecated use readIdentity + readSummaries */
export function getMemoryPath(chatId: string | number): string {
  return getIdentityPath(chatId);
}

/** @deprecated */
export function readMemory(chatId: string | number): string {
  const identity = readIdentity(chatId);
  const summaries = readSummaries(chatId);
  const parts: string[] = [];
  if (identity) parts.push(identity);
  if (summaries.length > 0) {
    parts.push("## Recent Session Summaries\n\n" + summaries.join("\n\n---\n\n"));
  }
  return parts.join("\n\n---\n\n");
}

/** @deprecated */
export function writeMemory(chatId: string | number, content: string): void {
  writeIdentity(chatId, content);
}

// ─── Build system prompt with memory injected ─────────────────────────────────

export function buildSystemPrompt(chatId: string | number, botName: string): string {
  const identity = readIdentity(chatId);
  const summaries = readSummaries(chatId);
  const identityPath = getIdentityPath(chatId);
  const summariesPath = getSummariesPath(chatId);

  const identitySection = identity
    ? `## Your Identity & Core Memory (PROTECTED)\n\n${identity}`
    : `## Your Identity & Core Memory (PROTECTED)\n\n(empty — use /memory to set up)`;

  const summarySection = summaries.length > 0
    ? `## Recent Conversation Summaries (auto-managed, last ${summaries.length})\n\n${summaries.join("\n\n---\n\n")}`
    : "";

  const secondBrainContext = readSecondBrainContext(chatId);
  const secondBrainSection = secondBrainContext
    ? `## Chow Second Brain Context (Cole-style, additive)\n\n${secondBrainContext}`
    : "";

  return `You are ${botName}, an AI coding and research assistant running inside a Telegram bot powered by pi + Claude.

${identitySection}

${summarySection ? summarySection + "\n\n" : ""}${secondBrainSection ? secondBrainSection + "\n\n" : ""}---

## Memory instructions

You have two memory files:
1. **Identity** (${identityPath}) — your core knowledge, who you are, what you manage, key facts. PROTECTED from auto-rotation.
2. **Summaries** (${summariesPath}) — auto-managed rolling window of recent session summaries. You don't need to update this.

### When to update your identity memory:
After ANY conversation that introduces important new information — projects, decisions, credentials, preferences, IDs, status changes — update your identity file IMMEDIATELY:

\`\`\`bash
cat > ${identityPath} << 'MEMORY_EOF'
(full updated identity content here)
MEMORY_EOF
\`\`\`

Write the FULL file each time (not appended notes). Keep it under 200 lines. Be concise — bullet points, not paragraphs.

### IMPORTANT: Always update memory when you learn something new. Don't skip this — your memory is how you persist across sessions.`;
}

// ─── Session files ────────────────────────────────────────────────────────────

export function getSessionDir(chatId: string | number): string {
  return path.join(SESSIONS_DIR, String(chatId));
}

export function getSessionFiles(chatId: string | number): string[] {
  const dir = getSessionDir(chatId);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".jsonl"))
    .map((f) => path.join(dir, f))
    .sort();
}

export function getSessionLineCount(chatId: string | number): number {
  const files = getSessionFiles(chatId);
  if (files.length === 0) return 0;
  const latest = files[files.length - 1];
  try {
    const content = fs.readFileSync(latest, "utf8");
    return content.split("\n").filter(Boolean).length;
  } catch {
    return 0;
  }
}

export function shouldRotateSession(chatId: string | number): boolean {
  return getSessionLineCount(chatId) > MAX_SESSION_LINES;
}

// ─── Session rotation with summarization ──────────────────────────────────────

export async function summarizeAndRotate(chatId: string | number, botName: string): Promise<void> {
  const files = getSessionFiles(chatId);
  if (files.length === 0) return;

  console.log(`[memory] Summarizing session for chat ${chatId} before rotation...`);

  try {
    const { authStorage, modelRegistry, settingsManager, model } = createChowRuntime();

    const { session } = await createAgentSession({
      sessionManager: SessionManager.continueRecent(
        process.cwd(),
        getSessionDir(chatId)
      ),
      authStorage,
      modelRegistry,
      settingsManager,
      model,
    });
    await pinSessionModel(session, model);

    let summary = "";
    const unsub = session.subscribe((event) => {
      if (
        event.type === "message_update" &&
        event.assistantMessageEvent.type === "text_delta"
      ) {
        summary += event.assistantMessageEvent.delta;
      }
    });

    await session.prompt(
      `This session is about to be archived. Write a concise summary of what was discussed and accomplished.

Include:
- What topics were discussed
- What was built, fixed, or decided
- Any important values, IDs, or config that came up
- Current status of any ongoing work

Format: 3-10 bullet points, no headers, no code fences. Just the raw summary text.
Start with the date: [${new Date().toISOString().slice(0, 10)}]`
    );

    unsub();
    session.dispose();

    if (summary.trim()) {
      appendSummary(chatId, summary.trim());
      const totalSummaries = readSummaries(chatId).length;
      console.log(`[memory] Appended summary for chat ${chatId} (${summary.length} chars, ${totalSummaries} total)`);

      try {
        if (isChowPrimaryBrainChat(chatId)) {
          appendBrainEvent(chatId, {
            type: "session_rotation",
            title: "Session rotated with archived summary",
            detail: summary.trim(),
            source: "memory-rotation",
            project: "chow",
            importance: 3,
            tags: ["rotation", "summary"],
          });
        }
      } catch (eventErr) {
        console.error(`[memory] Failed to append brain event for chat ${chatId}:`, eventErr);
      }

      try {
        syncChowSecondBrain(chatId, "Auto-reflect after session rotation");
      } catch (syncErr) {
        console.error(`[memory] Chow second-brain sync failed for chat ${chatId}:`, syncErr);
      }
    }
  } catch (err) {
    console.error(`[memory] Summarize failed for chat ${chatId}:`, err);
  }

  // Archive all session files
  for (const f of files) {
    const dest = path.join(ARCHIVE_DIR, path.basename(f));
    try {
      fs.renameSync(f, dest);
    } catch {}
  }

  console.log(`[memory] Archived ${files.length} session file(s) for chat ${chatId}`);
}
