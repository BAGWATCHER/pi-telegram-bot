// ─── Embedding Memory System ───────────────────────────────────────────────────
// Uses Gemini text-embedding-004 to embed conversation chunks.
// Stores in SQLite. Cosine similarity search on every message.
//
// Flow:
//   On session rotate → embed full session text → store in DB
//   On message → embed query → find top-K similar chunks → inject into prompt

import Database from "better-sqlite3";
import * as fs from "node:fs";
import * as path from "node:path";

const BOT_ROOT = process.cwd();
const DB_PATH = path.join(BOT_ROOT, "memory", "embeddings.db");
const GEMINI_API_KEY = process.env.GEMINI_API_KEY!;
const EMBED_MODEL = "text-embedding-004";
const EMBED_DIM = 768;
const TOP_K = 5;
const MIN_SIMILARITY = 0.75; // only inject if relevant enough

fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

// ─── DB setup ─────────────────────────────────────────────────────────────────

let _db: Database.Database | null = null;

function getDb(): Database.Database {
  if (_db) return _db;
  _db = new Database(DB_PATH);
  _db.exec(`
    CREATE TABLE IF NOT EXISTS chunks (
      id        INTEGER PRIMARY KEY AUTOINCREMENT,
      chat_id   INTEGER NOT NULL,
      text      TEXT NOT NULL,
      embedding BLOB NOT NULL,
      created_at INTEGER NOT NULL,
      source    TEXT DEFAULT 'session'
    );
    CREATE INDEX IF NOT EXISTS idx_chat ON chunks(chat_id);
  `);
  return _db;
}

// ─── Embedding API ─────────────────────────────────────────────────────────────

async function embed(text: string): Promise<Float32Array | null> {
  if (!GEMINI_API_KEY) {
    console.warn("[embed] No GEMINI_API_KEY set");
    return null;
  }
  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${EMBED_MODEL}:embedContent?key=${GEMINI_API_KEY}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: `models/${EMBED_MODEL}`,
          content: { parts: [{ text: text.slice(0, 8000) }] },
          taskType: "RETRIEVAL_DOCUMENT",
        }),
      }
    );
    if (!res.ok) {
      console.error("[embed] API error:", res.status, await res.text());
      return null;
    }
    const data = await res.json() as any;
    const values: number[] = data.embedding?.values;
    if (!values) return null;
    return new Float32Array(values);
  } catch (e: any) {
    console.error("[embed] fetch error:", e.message);
    return null;
  }
}

async function embedQuery(text: string): Promise<Float32Array | null> {
  if (!GEMINI_API_KEY) return null;
  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${EMBED_MODEL}:embedContent?key=${GEMINI_API_KEY}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: `models/${EMBED_MODEL}`,
          content: { parts: [{ text: text.slice(0, 2000) }] },
          taskType: "RETRIEVAL_QUERY",
        }),
      }
    );
    if (!res.ok) return null;
    const data = await res.json() as any;
    const values: number[] = data.embedding?.values;
    if (!values) return null;
    return new Float32Array(values);
  } catch {
    return null;
  }
}

// ─── Math ──────────────────────────────────────────────────────────────────────

function cosineSimilarity(a: Float32Array, b: Float32Array): number {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB) || 1);
}

function bufferToFloat32(buf: Buffer): Float32Array {
  return new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
}

function float32ToBuffer(arr: Float32Array): Buffer {
  return Buffer.from(arr.buffer);
}

// ─── Store a chunk ─────────────────────────────────────────────────────────────

export async function storeChunk(
  chatId: number,
  text: string,
  source: string = "session"
): Promise<void> {
  if (!text.trim() || text.length < 50) return;
  const embedding = await embed(text);
  if (!embedding) return;

  const db = getDb();
  db.prepare(`
    INSERT INTO chunks (chat_id, text, embedding, created_at, source)
    VALUES (?, ?, ?, ?, ?)
  `).run(chatId, text.slice(0, 4000), float32ToBuffer(embedding), Date.now(), source);

  console.log(`[embed] Stored chunk for chat ${chatId} (${text.length} chars)`);
}

// ─── Search similar memories ───────────────────────────────────────────────────

export async function searchMemories(
  chatId: number,
  query: string,
  topK: number = TOP_K
): Promise<Array<{ text: string; similarity: number; date: string }>> {
  const queryVec = await embedQuery(query);
  if (!queryVec) return [];

  const db = getDb();
  const rows = db.prepare(`
    SELECT text, embedding, created_at FROM chunks
    WHERE chat_id = ?
    ORDER BY created_at DESC
    LIMIT 200
  `).all(chatId) as Array<{ text: string; embedding: Buffer; created_at: number }>;

  if (!rows.length) return [];

  const scored = rows
    .map(row => ({
      text: row.text,
      similarity: cosineSimilarity(queryVec, bufferToFloat32(row.embedding)),
      date: new Date(row.created_at).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric"
      }),
    }))
    .filter(r => r.similarity >= MIN_SIMILARITY)
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, topK);

  return scored;
}

// ─── Format for system prompt injection ───────────────────────────────────────

export function formatMemoriesForPrompt(
  memories: Array<{ text: string; similarity: number; date: string }>
): string {
  if (!memories.length) return "";
  const lines = memories.map(m =>
    `[${m.date}] ${m.text.trim()}`
  );
  return `\n\n## Relevant memories from past conversations:\n${lines.join("\n\n---\n")}`;
}

// ─── Count stored chunks ───────────────────────────────────────────────────────

export function getChunkCount(chatId: number): number {
  const db = getDb();
  const row = db.prepare(`SELECT COUNT(*) as cnt FROM chunks WHERE chat_id = ?`).get(chatId) as any;
  return row?.cnt ?? 0;
}

// ─── Embed individual message exchange ────────────────────────────────────────
// Called after each bot response to capture the raw exchange, not just summaries.

export async function embedMessagePair(
  chatId: number,
  userText: string,
  assistantText: string
): Promise<void> {
  const combined = `User: ${userText}\n\nAssistant: ${assistantText}`;
  await storeChunk(chatId, combined, "message");
}

// ─── JSONL keyword fallback search ────────────────────────────────────────────
// When embedding search finds nothing, grep raw session files for keywords.

function extractJSONLMessages(filePath: string): Array<{ role: string; text: string }> {
  try {
    const lines = fs.readFileSync(filePath, "utf8").split("\n").filter(Boolean);
    const messages: Array<{ role: string; text: string }> = [];
    for (const line of lines) {
      try {
        const obj = JSON.parse(line);
        if (obj.type !== "message") continue;
        const msg = obj.message ?? {};
        const role: string = msg.role ?? "unknown";
        const content = msg.content ?? [];
        let text = "";
        if (Array.isArray(content)) {
          for (const block of content) {
            if (block?.type === "text") text += block.text ?? "";
          }
        } else if (typeof content === "string") {
          text = content;
        }
        if (text.trim().length > 10) messages.push({ role, text: text.trim() });
      } catch {}
    }
    return messages;
  } catch {
    return [];
  }
}

function scoreKeywordMatch(text: string, keywords: string[]): number {
  const lower = text.toLowerCase();
  return keywords.filter(k => lower.includes(k)).length;
}

export function searchConvoHistory(
  chatId: number,
  query: string,
  topK: number = 3
): Array<{ text: string; date: string; score: number }> {
  // Extract keywords (words > 3 chars, ignore common stopwords)
  const stopwords = new Set(["what","when","where","which","that","this","with","have","from","they","been","were","will","would","could","should","about","your","their","there","these","those","then","than","also","just","like","more","some","into","over","after","before","does","did","has","had","its","him","her","she","the","and","for","are","but","not","you","all","can","her","was","one","our","out","day","get","how","may","who","its"]);
  const keywords = query.toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(w => w.length > 3 && !stopwords.has(w));

  if (!keywords.length) return [];

  const sessionBase = path.join(BOT_ROOT, "sessions", String(chatId));
  const archiveBase = path.join(BOT_ROOT, "sessions", "archive");

  // Collect all JSONL files for this chat
  const files: { file: string; date: Date }[] = [];

  const addDir = (dir: string) => {
    if (!fs.existsSync(dir)) return;
    for (const f of fs.readdirSync(dir)) {
      if (!f.endsWith(".jsonl")) continue;
      // Archive files are named with chatId prefix or inside chatId subdir
      const full = path.join(dir, f);
      const match = f.match(/^(\d{4}-\d{2}-\d{2})/);
      files.push({ file: full, date: match ? new Date(match[1]) : new Date(0) });
    }
  };

  addDir(sessionBase);
  // Archive may have per-chat subdirs or flat files with chatId in name
  if (fs.existsSync(archiveBase)) {
    const chatArchive = path.join(archiveBase, String(chatId));
    if (fs.existsSync(chatArchive)) addDir(chatArchive);
    else {
      // flat archive — filter by chatId in filename
      for (const f of fs.readdirSync(archiveBase)) {
        if (!f.endsWith(".jsonl")) continue;
        files.push({ file: path.join(archiveBase, f), date: new Date(0) });
      }
    }
  }

  const results: Array<{ text: string; date: string; score: number }> = [];

  for (const { file, date } of files) {
    const messages = extractJSONLMessages(file);
    // Build sliding window pairs (user + next assistant)
    for (let i = 0; i < messages.length - 1; i++) {
      if (messages[i].role !== "user") continue;
      const user = messages[i].text;
      const assistant = messages[i + 1]?.role === "assistant" ? messages[i + 1].text : "";
      const combined = `${user} ${assistant}`;
      const score = scoreKeywordMatch(combined, keywords);
      if (score > 0) {
        const dateStr = date.getFullYear() > 1970
          ? date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
          : "unknown date";
        results.push({
          text: `User: ${user.slice(0, 300)}\nAssistant: ${assistant.slice(0, 400)}`,
          date: dateStr,
          score,
        });
      }
    }
  }

  return results.sort((a, b) => b.score - a.score).slice(0, topK);
}

export function formatConvoHistoryForPrompt(
  results: Array<{ text: string; date: string; score: number }>
): string {
  if (!results.length) return "";
  const lines = results.map(r => `[${r.date}]\n${r.text.trim()}`);
  return `\n\n## Found in conversation history:\n${lines.join("\n\n---\n")}`;
}
