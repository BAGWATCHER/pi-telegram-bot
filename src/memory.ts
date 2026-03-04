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
import { storeChunk } from "./embeddings.js";
import * as path from "node:path";
import {
  createAgentSession,
  SessionManager,
  AuthStorage,
  ModelRegistry,
} from "@mariozechner/pi-coding-agent";

const BOT_ROOT = process.cwd();
const MEMORY_DIR = path.join(BOT_ROOT, "memory");
const SESSIONS_DIR = path.join(BOT_ROOT, "sessions");
const ARCHIVE_DIR = path.join(BOT_ROOT, "sessions", "archive");
const MAX_SESSION_LINES = 200; // auto-rotate after this many jsonl lines
const MAX_SUMMARIES = 5; // keep last N session summaries
const SUMMARY_SEPARATOR = "\n\n---\n\n";

fs.mkdirSync(MEMORY_DIR, { recursive: true });
fs.mkdirSync(ARCHIVE_DIR, { recursive: true });

// ─── Memory directory per chat ────────────────────────────────────────────────

function getChatMemoryDir(chatId: number): string {
  const dir = path.join(MEMORY_DIR, String(chatId));
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

export function getIdentityPath(chatId: number): string {
  return path.join(getChatMemoryDir(chatId), "identity.md");
}

export function getSummariesPath(chatId: number): string {
  return path.join(getChatMemoryDir(chatId), "summaries.md");
}

// Legacy path for migration
function getLegacyMemoryPath(chatId: number): string {
  return path.join(MEMORY_DIR, `${chatId}.md`);
}

// ─── Migration: move old memory/<chatId>.md → memory/<chatId>/identity.md ─────

function migrateIfNeeded(chatId: number): void {
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

export function readIdentity(chatId: number): string {
  migrateIfNeeded(chatId);
  const p = getIdentityPath(chatId);
  if (!fs.existsSync(p)) return "";
  return fs.readFileSync(p, "utf8").trim();
}

export function writeIdentity(chatId: number, content: string): void {
  migrateIfNeeded(chatId);
  fs.writeFileSync(getIdentityPath(chatId), content.trim() + "\n", "utf8");
}

export function readSummaries(chatId: number): string[] {
  const p = getSummariesPath(chatId);
  if (!fs.existsSync(p)) return [];
  const content = fs.readFileSync(p, "utf8").trim();
  if (!content) return [];
  return content.split(SUMMARY_SEPARATOR).filter(Boolean);
}

function appendSummary(chatId: number, summary: string): void {
  const summaries = readSummaries(chatId);
  summaries.push(summary.trim());
  // Keep only last MAX_SUMMARIES
  const trimmed = summaries.slice(-MAX_SUMMARIES);
  fs.writeFileSync(
    getSummariesPath(chatId),
    trimmed.join(SUMMARY_SEPARATOR) + "\n",
    "utf8"
  );
}

// ─── Combined memory read (for backward compat) ──────────────────────────────

/** @deprecated use readIdentity + readSummaries */
export function getMemoryPath(chatId: number): string {
  return getIdentityPath(chatId);
}

/** @deprecated */
export function readMemory(chatId: number): string {
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
export function writeMemory(chatId: number, content: string): void {
  writeIdentity(chatId, content);
}

// ─── Build system prompt with memory injected ─────────────────────────────────

export function buildSystemPrompt(chatId: number, botName: string): string {
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

  return `You are ${botName}, an AI coding and research assistant running inside a Telegram bot powered by pi + Claude.

${identitySection}

${summarySection ? summarySection + "\n\n" : ""}---

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

export function getSessionDir(chatId: number): string {
  return path.join(SESSIONS_DIR, String(chatId));
}

export function getSessionFiles(chatId: number): string[] {
  const dir = getSessionDir(chatId);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".jsonl"))
    .map((f) => path.join(dir, f))
    .sort();
}

export function getSessionLineCount(chatId: number): number {
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

export function shouldRotateSession(chatId: number): boolean {
  return getSessionLineCount(chatId) > MAX_SESSION_LINES;
}

// ─── Session rotation with summarization ──────────────────────────────────────

export async function summarizeAndRotate(chatId: number, botName: string): Promise<void> {
  const files = getSessionFiles(chatId);
  if (files.length === 0) return;

  console.log(`[memory] Summarizing session for chat ${chatId} before rotation...`);

  try {
    const authStorage = AuthStorage.create();
    const modelRegistry = new ModelRegistry(authStorage);

    const { session } = await createAgentSession({
      sessionManager: SessionManager.continueRecent(
        process.cwd(),
        getSessionDir(chatId)
      ),
      authStorage,
      modelRegistry,
    });

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
      // Embed summary for long-term semantic search
      storeChunk(chatId, summary.trim(), "summary").catch(e =>
        console.error("[embed] store failed:", e.message)
      );
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
