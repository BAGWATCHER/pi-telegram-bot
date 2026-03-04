import "dotenv/config";
import { Telegraf, Context } from "telegraf";
import { message } from "telegraf/filters";
import {
  createAgentSession,
  SessionManager,
  SettingsManager,
  AuthStorage,
  ModelRegistry,
  DefaultResourceLoader,
  type AgentSession,
} from "@mariozechner/pi-coding-agent";
import * as path from "node:path";
import * as fs from "node:fs";
import * as os from "node:os";
import { isRelayEnabled, relayPost, relayGet, formatGroupContext } from "./relay.js";
import {
  buildSystemPrompt,
  shouldRotateSession,
  summarizeAndRotate,
  readMemory,
  getMemoryPath,
} from "./memory.js";

// ─── Config ──────────────────────────────────────────────────────────────────

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const BOT_NAME = process.env.BOT_NAME ?? "Bot";
const ALLOWED_CHAT_IDS = process.env.ALLOWED_CHAT_IDS
  ? process.env.ALLOWED_CHAT_IDS.split(",").map((s) => s.trim())
  : [];

if (!BOT_TOKEN) throw new Error("TELEGRAM_BOT_TOKEN is required in .env");
console.log(`🤖 Bot name: ${BOT_NAME} | Relay: ${isRelayEnabled() ? process.env.RELAY_URL : "disabled"}`);

const SESSIONS_DIR = path.join(process.cwd(), "sessions");
const TG_MAX_LENGTH = 4000; // leave headroom under 4096
const EDIT_INTERVAL_MS = 1500; // how often to edit streaming message

fs.mkdirSync(SESSIONS_DIR, { recursive: true });

// ─── Session management ───────────────────────────────────────────────────────

interface ChatState {
  session: AgentSession;
  busy: boolean;
  abortController?: AbortController;
}

const chatStates = new Map<number, ChatState>();

function getSessionDir(chatId: number): string {
  const dir = path.join(SESSIONS_DIR, String(chatId));
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

async function getOrCreateSession(chatId: number): Promise<AgentSession> {
  const existing = chatStates.get(chatId);
  if (existing) return existing.session;

  // Auto-rotate if session is too large — summarize into memory first
  if (shouldRotateSession(chatId)) {
    console.log(`[session] Auto-rotating session for chat ${chatId}`);
    await summarizeAndRotate(chatId, BOT_NAME);
  }

  const authStorage = AuthStorage.create();
  const modelRegistry = new ModelRegistry(authStorage);
  const settingsManager = await SettingsManager.create();
  const sessionDir = getSessionDir(chatId);

  const loader = new DefaultResourceLoader({
    systemPromptOverride: () => buildSystemPrompt(chatId, BOT_NAME),
  });
  await loader.reload();

  const { session } = await createAgentSession({
    sessionManager: SessionManager.continueRecent(process.cwd(), sessionDir),
    authStorage,
    modelRegistry,
    settingsManager,
    resourceLoader: loader,
  });

  chatStates.set(chatId, { session, busy: false });
  return session;
}

async function resetSession(chatId: number, summarize = true): Promise<AgentSession> {
  const existing = chatStates.get(chatId);
  if (existing) {
    existing.session.dispose();
    chatStates.delete(chatId);
  }

  // Summarize old session into memory before wiping
  if (summarize) {
    await summarizeAndRotate(chatId, BOT_NAME);
  }

  const authStorage = AuthStorage.create();
  const modelRegistry = new ModelRegistry(authStorage);
  const settingsManager = await SettingsManager.create();
  const sessionDir = getSessionDir(chatId);

  const loader = new DefaultResourceLoader({
    systemPromptOverride: () => buildSystemPrompt(chatId, BOT_NAME),
  });
  await loader.reload();

  const { session } = await createAgentSession({
    sessionManager: SessionManager.create(process.cwd(), sessionDir),
    authStorage,
    modelRegistry,
    settingsManager,
    resourceLoader: loader,
  });

  chatStates.set(chatId, { session, busy: false });
  return session;
}

// ─── Telegram helpers ─────────────────────────────────────────────────────────

function escapeMarkdown(text: string): string {
  // Escape special Markdown V2 chars
  return text.replace(/[_*[\]()~`>#+\-=|{}.!\\]/g, "\\$&");
}

function truncate(text: string, max = TG_MAX_LENGTH): string {
  if (text.length <= max) return text;
  return text.slice(0, max - 3) + "...";
}

async function safeSend(ctx: Context, text: string): Promise<any> {
  const chunks = splitMessage(text);
  let last: any;
  for (const chunk of chunks) {
    last = await ctx.reply(chunk, { parse_mode: undefined }).catch(() =>
      ctx.reply(chunk.replace(/[<>&]/g, ""))
    );
  }
  return last;
}

async function safeEdit(ctx: Context, msgId: number, text: string): Promise<void> {
  const chunks = splitMessage(text);
  // Only edit the first chunk; additional chunks would need new messages
  try {
    await ctx.telegram.editMessageText(
      ctx.chat!.id,
      msgId,
      undefined,
      truncate(chunks[0])
    );
  } catch {
    // Message not modified or too fast — ignore
  }
}

function splitMessage(text: string): string[] {
  const chunks: string[] = [];
  let remaining = text;
  while (remaining.length > TG_MAX_LENGTH) {
    // Split at last newline before limit
    let idx = remaining.lastIndexOf("\n", TG_MAX_LENGTH);
    if (idx < 0) idx = TG_MAX_LENGTH;
    chunks.push(remaining.slice(0, idx));
    remaining = remaining.slice(idx).trimStart();
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

function isAllowed(chatId: number): boolean {
  if (ALLOWED_CHAT_IDS.length === 0) return true; // open if no allowlist
  return ALLOWED_CHAT_IDS.includes(String(chatId));
}

// ─── Core: run pi and stream to Telegram ─────────────────────────────────────

async function runPiPrompt(
  ctx: Context,
  chatId: number,
  userText: string,
  senderName?: string
): Promise<void> {
  const state = chatStates.get(chatId)!;
  if (state.busy) {
    await ctx.reply("⏳ Still working on the previous request. Send /abort to cancel.");
    return;
  }

  state.busy = true;

  // Auto-reset if stuck after 4 minutes
  const stuckTimer = setTimeout(async () => {
    if (!chatStates.get(chatId)?.busy) return;
    console.warn(`[STUCK] chatId=${chatId} — aborting after 4min`);
    try { await state.session.abort(); } catch {}
    state.busy = false;
    ctx.reply("⏱️ Timed out after 4 minutes. Send your message again.").catch(() => {});
  }, 4 * 60 * 1000);

  // ── Relay: log user message & fetch group history ──────────────────────────
  const userName = senderName ?? "User";
  await relayPost(chatId, userName, "user", userText);
  const history = await relayGet(chatId, 30);
  const groupContext = formatGroupContext(history, BOT_NAME);
  const promptWithContext = groupContext
    ? `${groupContext}\n\nLatest message from ${userName}: ${userText}`
    : userText;

  // Send a placeholder message we'll edit in real-time
  const placeholder = await ctx.reply("🤔 Thinking...");
  const msgId = placeholder.message_id;

  let fullText = "";
  let toolLine = "";
  let lastEditText = "";
  let editTimer: ReturnType<typeof setInterval> | null = null;

  // Throttled edits
  editTimer = setInterval(async () => {
    const display = buildDisplay(fullText, toolLine);
    if (display !== lastEditText) {
      lastEditText = display;
      await safeEdit(ctx, msgId, display);
    }
  }, EDIT_INTERVAL_MS);

  function buildDisplay(text: string, tool: string): string {
    let out = text || "";
    if (tool) out += (out ? "\n\n" : "") + `🔧 \`${tool}\``;
    return truncate(out || "🤔 Thinking...") ;
  }

  try {
    const session = state.session;

    const unsub = session.subscribe((event) => {
      switch (event.type) {
        case "message_update":
          if (event.assistantMessageEvent.type === "text_delta") {
            fullText += event.assistantMessageEvent.delta;
            toolLine = "";
          }
          break;

        case "tool_execution_start":
          toolLine = event.toolName;
          break;

        case "tool_execution_end":
          toolLine = "";
          break;

        case "agent_end":
          toolLine = "";
          break;
      }
    });

    // Inject relevant long-term memories
    let promptWithMemories = promptWithContext;
    try {
      const memories = await searchMemories(chatId, promptWithContext);
      if (memories.length > 0) {
        promptWithMemories = promptWithContext + formatMemoriesForPrompt(memories);
        console.log(`[embed] Injecting ${memories.length} semantic memories`);
      } else {
        // Fallback: keyword search through raw conversation history
        const histResults = searchConvoHistory(chatId, promptWithContext);
        if (histResults.length > 0) {
          promptWithMemories = promptWithContext + formatConvoHistoryForPrompt(histResults);
          console.log(`[embed] Fallback: injecting ${histResults.length} keyword matches from history`);
        }
      }
    } catch (e: any) {
      console.error("[embed] search failed:", e.message);
    }

    await session.prompt(promptWithMemories);
    unsub();

    // Final edit
    if (editTimer) clearInterval(editTimer);

    const finalText = fullText.trim() || "(no response)";

    // Embed this exchange for future memory retrieval
    embedMessagePair(chatId, promptWithContext, finalText).catch(e =>
      console.error("[embed] message pair store failed:", e.message)
    );

    // ── Relay: check if bot wants to skip ─────────────────────────────────────
    if (finalText === "[SKIP]") {
      console.log(`[${new Date().toISOString()}] ${BOT_NAME} skipped this message`);
      try { await ctx.telegram.deleteMessage(ctx.chat!.id, msgId); } catch {}
      return;
    }

    // ── Relay: log our response ───────────────────────────────────────────────
    await relayPost(chatId, BOT_NAME, "bot", finalText);

    console.log(`[${new Date().toISOString()}] → replied (${finalText.length} chars)`);
    const chunks = splitMessage(finalText);

    // Edit the placeholder with first chunk
    try {
      await ctx.telegram.editMessageText(
        ctx.chat!.id,
        msgId,
        undefined,
        chunks[0]
      );
    } catch {
      await ctx.reply(chunks[0]);
    }

    // Send remaining chunks as new messages
    for (let i = 1; i < chunks.length; i++) {
      await ctx.reply(chunks[i]);
    }
  } catch (err: any) {
    if (editTimer) clearInterval(editTimer);
    const errMsg = `❌ Error: ${err?.message ?? String(err)}`;
    try {
      await ctx.telegram.editMessageText(ctx.chat!.id, msgId, undefined, errMsg);
    } catch {
      await ctx.reply(errMsg);
    }
  } finally {
    clearTimeout(stuckTimer);
    state.busy = false;
  }
}

// ─── Bot setup ────────────────────────────────────────────────────────────────

const bot = new Telegraf(BOT_TOKEN);

// Auth middleware — silent ignore for unauthorized chats (no reply = no crash)
bot.use(async (ctx, next) => {
  const chatId = ctx.chat?.id;
  if (!chatId || !isAllowed(chatId)) {
    console.log(`[AUTH BLOCKED] chat_id=${chatId} type=${ctx.chat?.type} title=${(ctx.chat as any)?.title ?? "dm"}`);
    return; // silent — don't reply, avoids crash if bot was kicked
  }
  await next();
});

// Commands
bot.start(async (ctx) => {
  const chatId = ctx.chat.id;
  await getOrCreateSession(chatId);
  await ctx.reply(
    `👋 *Pi Coding Agent* is ready!\n\n` +
      `Send me any message and I'll use Claude + pi's full toolkit to help.\n\n` +
      `*Commands:*\n` +
      `/new — Start a fresh session\n` +
      `/compact — Compact the conversation\n` +
      `/abort — Abort current task\n` +
      `/status — Show session info`,
    { parse_mode: "Markdown" }
  );
});

bot.command("new", async (ctx) => {
  const chatId = ctx.chat.id;
  const state = chatStates.get(chatId);
  if (state?.busy) {
    await ctx.reply("⏳ Can't reset while busy. Send /abort first.");
    return;
  }
  await ctx.reply("🧠 Saving memory from this session, then starting fresh...");
  await resetSession(chatId, true);
  await ctx.reply("✅ Fresh session ready! I remember everything important from before.");
});

bot.command("compact", async (ctx) => {
  const chatId = ctx.chat.id;
  const state = chatStates.get(chatId);
  if (!state) {
    await ctx.reply("No active session. Send a message first.");
    return;
  }
  if (state.busy) {
    await ctx.reply("⏳ Busy right now.");
    return;
  }
  await ctx.reply("🗜️ Compacting...");
  try {
    await state.session.compact();
    await ctx.reply("✅ Compaction done!");
  } catch (e: any) {
    await ctx.reply(`❌ Compaction failed: ${e?.message}`);
  }
});

bot.command("abort", async (ctx) => {
  const chatId = ctx.chat.id;
  const state = chatStates.get(chatId);
  if (!state?.busy) {
    await ctx.reply("Nothing running.");
    return;
  }
  await state.session.abort();
  state.busy = false;
  await ctx.reply("🛑 Aborted.");
});

bot.command("status", async (ctx) => {
  const chatId = ctx.chat.id;
  const state = chatStates.get(chatId);
  if (!state) {
    await ctx.reply("No active session yet.");
    return;
  }
  const model = state.session.model;
  const modelStr = model ? `${model.provider}/${model.id}` : "unknown";
  const msgs = state.session.messages.length;
  const sessionFile = state.session.sessionFile ?? "in-memory";
  await ctx.reply(
    `📊 *Session Status*\n` +
      `Model: \`${modelStr}\`\n` +
      `Messages: ${msgs}\n` +
      `Busy: ${state.busy ? "Yes" : "No"}\n` +
      `Session: \`${path.basename(sessionFile)}\``,
    { parse_mode: "Markdown" }
  );
});

bot.command("memory", async (ctx) => {
  const chatId = ctx.chat.id;
  const memory = readMemory(chatId);
  if (!memory) {
    await ctx.reply("🧠 No memory yet. I'll start building it as we talk.");
    return;
  }
  const chunks = splitMessage(`🧠 *My memory for this chat:*\n\n${memory}`);
  for (const chunk of chunks) await ctx.reply(chunk, { parse_mode: "Markdown" }).catch(() => ctx.reply(chunk));
});

// Text messages → pi (fire & forget so Telegraf's 90s handler timeout doesn't kill us)
bot.on(message("text"), (ctx) => {
  const chatId = ctx.chat.id;
  const user = ctx.from?.username ?? ctx.from?.first_name ?? String(chatId);
  const text = ctx.message.text;

  console.log(`[${new Date().toISOString()}] @${user} (${chatId}): ${text.slice(0, 80)}`);

  // Run async in background — don't await
  getOrCreateSession(chatId)
    .then(() => runPiPrompt(ctx, chatId, text, user))
    .catch((err) => {
      console.error(`[ERROR] chatId=${chatId}:`, err?.message ?? err);
      ctx.reply(`❌ Error: ${err?.message ?? "Unknown error"}`).catch(() => {});
    });
});

// Photo messages → pass as text description for now
bot.on(message("photo"), (ctx) => {
  const chatId = ctx.chat.id;
  const caption = ctx.message.caption ?? "Describe this image.";

  getOrCreateSession(chatId)
    .then(() => runPiPrompt(ctx, chatId, `[User sent a photo] ${caption}`))
    .catch((err) => {
      ctx.reply(`❌ Error: ${err?.message ?? "Unknown error"}`).catch(() => {});
    });
});

// Global error handler — log but don't crash
bot.catch((err, ctx) => {
  console.error(`[BOT ERROR] chat=${ctx.chat?.id}:`, (err as any)?.message ?? err);
});

// Graceful shutdown
process.once("SIGINT", () => {
  console.log("Shutting down...");
  for (const [, state] of chatStates) {
    state.session.dispose();
  }
  bot.stop("SIGINT");
});
process.once("SIGTERM", () => {
  for (const [, state] of chatStates) {
    state.session.dispose();
  }
  bot.stop("SIGTERM");
});

// ─── Launch ───────────────────────────────────────────────────────────────────

console.log("🤖 Pi Telegram Bot starting...");
// Launch with 409 retry logic
(async () => {
  // Force-clear any existing polling session
  try {
    const token = process.env.BOT_TOKEN || process.env.TELEGRAM_BOT_TOKEN;
    // Call deleteWebhook first
    await fetch(`https://api.telegram.org/bot${token}/deleteWebhook?drop_pending_updates=true`);
    // Short poll to flush the connection slot
    await fetch(`https://api.telegram.org/bot${token}/getUpdates?timeout=1&limit=1`).catch(() => {});
    await new Promise(r => setTimeout(r, 5000));
    console.log('[LAUNCH] Connection slot cleared, starting bot...');
  } catch {}

  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      await bot.launch({ dropPendingUpdates: true });
      break;
    } catch (e: any) {
      if (e?.response?.error_code === 409) {
        console.log(`[LAUNCH] 409 conflict, attempt ${attempt+1}/5, waiting 30s...`);
        await new Promise(r => setTimeout(r, 30000));
      } else {
        throw e;
      }
    }
  }
})().catch(e => { console.error('[LAUNCH] Fatal:', e.message); process.exit(1); });
console.log(`✅ ${BOT_NAME} is running! Relay: ${isRelayEnabled() ? process.env.RELAY_URL : "disabled"}`);
