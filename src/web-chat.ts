/**
 * web-chat.ts — Chow's HTTP chat endpoint (port 3849)
 * Runs a pi agent session that the dashboard (and any web client) can talk to.
 * Independent from the Telegram bot — separate session, same memory/identity.
 */
import "dotenv/config";
import express, { Request, Response } from "express";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import {
  createAgentSession,
  SessionManager,
  SettingsManager,
  AuthStorage,
  ModelRegistry,
  DefaultResourceLoader,
  type AgentSession,
} from "@mariozechner/pi-coding-agent";
import { buildSystemPrompt, shouldRotateSession, summarizeAndRotate } from "./memory.js";

const PORT = process.env.WEB_CHAT_PORT ?? 3849;
const BOT_NAME = process.env.BOT_NAME ?? "Mr Chow";
const WEB_CHAT_ID = 1340648627; // separate ID from Telegram so sessions don't collide
const SESSIONS_DIR = path.join(os.homedir(), "pi-telegram-bot", "sessions");
const HISTORY_FILE = path.join(os.homedir(), "pi-telegram-bot", "web-chat-history.json");

fs.mkdirSync(SESSIONS_DIR, { recursive: true });

// ── Session ────────────────────────────────────────────────────────────────

interface ChatState {
  session: AgentSession;
  busy: boolean;
}

let chatState: ChatState | null = null;

function getSessionDir() {
  const dir = path.join(SESSIONS_DIR, "web-" + WEB_CHAT_ID);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

async function getOrCreateSession(): Promise<AgentSession> {
  if (chatState) return chatState.session;

  if (shouldRotateSession(WEB_CHAT_ID)) {
    console.log("[web-chat] Auto-rotating session");
    await summarizeAndRotate(WEB_CHAT_ID, BOT_NAME);
  }

  const authStorage = AuthStorage.create();
  const modelRegistry = new ModelRegistry(authStorage);
  const settingsManager = SettingsManager.create();

  const loader = new DefaultResourceLoader({
    systemPromptOverride: () => buildSystemPrompt(WEB_CHAT_ID, BOT_NAME),
  });
  await loader.reload();

  const { session } = await createAgentSession({
    sessionManager: SessionManager.continueRecent(process.cwd(), getSessionDir()),
    authStorage,
    modelRegistry,
    settingsManager,
    resourceLoader: loader,
  });

  chatState = { session, busy: false };
  return session;
}

// ── History ────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  ts: number;
}

function loadHistory(): Message[] {
  try {
    return JSON.parse(fs.readFileSync(HISTORY_FILE, "utf8"));
  } catch {
    return [];
  }
}

function appendHistory(msg: Message) {
  const hist = loadHistory();
  hist.push(msg);
  // Keep last 200 messages
  const trimmed = hist.slice(-200);
  fs.writeFileSync(HISTORY_FILE, JSON.stringify(trimmed, null, 2));
}

// ── Express ────────────────────────────────────────────────────────────────

const app = express();
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.sendStatus(204);
  next();
});
app.use(express.json());

// Health check
app.get("/health", (_req: Request, res: Response) => {
  res.json({ ok: true, busy: chatState?.busy ?? false });
});

// Get history
app.get("/history", (_req: Request, res: Response) => {
  res.json({ messages: loadHistory() });
});

// Clear history + reset session
app.post("/reset", async (_req: Request, res: Response) => {
  if (chatState) {
    chatState.session.dispose();
    chatState = null;
  }
  fs.writeFileSync(HISTORY_FILE, "[]");
  res.json({ ok: true });
});

// Send a message — SSE stream back
app.post("/message", async (req: Request, res: Response) => {
  const { text } = req.body as { text: string };
  if (!text?.trim()) return res.status(400).json({ error: "text required" });

  // SSE setup
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  const send = (data: object) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  if (chatState?.busy) {
    send({ type: "error", text: "Chow is busy with another request. Try /abort." });
    res.end();
    return;
  }

  // Save user message
  const userMsg: Message = { id: Date.now() + "-u", role: "user", text, ts: Date.now() };
  appendHistory(userMsg);
  send({ type: "user_ack", id: userMsg.id });

  let session: AgentSession;
  try {
    session = await getOrCreateSession();
  } catch (err: any) {
    send({ type: "error", text: "Failed to create session: " + err.message });
    res.end();
    return;
  }

  chatState!.busy = true;

  // Stuck timeout: 25 minutes
  const stuckTimer = setTimeout(() => {
    if (!chatState?.busy) return;
    try { session.abort(); } catch {}
    chatState!.busy = false;
    send({ type: "error", text: "Timed out after 25 minutes." });
    res.end();
  }, 25 * 60 * 1000);

  let fullText = "";

  const unsub = session.subscribe((event) => {
    switch (event.type) {
      case "message_update":
        if (event.assistantMessageEvent.type === "text_delta") {
          const delta = event.assistantMessageEvent.delta;
          fullText += delta;
          send({ type: "delta", delta });
        }
        break;
      case "tool_call":
        send({ type: "tool", tool: event.toolCall.name });
        break;
    }
  });

  try {
    await session.prompt(text);

    unsub();
    clearTimeout(stuckTimer);
    chatState!.busy = false;

    const finalText = fullText.trim() || "(no response)";

    // Save assistant response
    const assistantMsg: Message = {
      id: Date.now() + "-a",
      role: "assistant",
      text: finalText,
      ts: Date.now(),
    };
    appendHistory(assistantMsg);

    send({ type: "done", text: finalText, id: assistantMsg.id });
    res.end();
  } catch (err: any) {
    unsub();
    clearTimeout(stuckTimer);
    if (chatState) chatState.busy = false;
    send({ type: "error", text: err.message ?? "Unknown error" });
    res.end();
  }
});

app.listen(PORT, () => {
  console.log(`💬 Chow web-chat running on port ${PORT}`);
});
