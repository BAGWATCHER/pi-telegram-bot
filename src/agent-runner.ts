/**
 * agent-runner.ts
 * Standalone headless pi agent. Spawned as a detached background process by /work.
 * Runs indefinitely (no stuck timer). Sends heartbeats every 5 min + pings on done/fail.
 *
 * Usage:
 *   tsx src/agent-runner.ts --task-id t1abc --project coworkers \
 *     --project-path /home/ubuntu/clawd/apps/coworkers \
 *     --task "add Stripe billing" --chat-id 1340648617
 */

import "dotenv/config";
import {
  createAgentSession,
  SessionManager,
  SettingsManager,
  AuthStorage,
  ModelRegistry,
  DefaultResourceLoader,
} from "@mariozechner/pi-coding-agent";
import * as path from "node:path";
import * as fs from "node:fs";
import * as os from "node:os";
import { updateTask, writeOutput } from "./tasks.js";

// ─── Parse args ───────────────────────────────────────────────────────────────

function arg(name: string, required = true): string {
  const idx = process.argv.indexOf(`--${name}`);
  if (idx === -1 || !process.argv[idx + 1]) {
    if (required) { console.error(`Missing --${name}`); process.exit(1); }
    return "";
  }
  return process.argv[idx + 1];
}

const TASK_ID       = arg("task-id");
const PROJECT       = arg("project");
const PROJECT_PATH  = arg("project-path");
const TASK_DESC     = arg("task");
const CHAT_ID       = parseInt(arg("chat-id"), 10);
const MODEL_SPEC    = arg("model", false);
const BOT_TOKEN     = process.env.TELEGRAM_BOT_TOKEN!;

// Bot root is where agent-runner.ts lives (pi-telegram-bot/), not the project path
const BOT_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const AGENT_DIR = path.join(os.homedir(), ".pi", "agent");

console.log(`[agent-runner] task=${TASK_ID} project=${PROJECT} path=${PROJECT_PATH}`);
console.log(`[agent-runner] task: ${TASK_DESC}`);
if (MODEL_SPEC) console.log(`[agent-runner] model override: ${MODEL_SPEC}`);

// ─── Telegram notify ──────────────────────────────────────────────────────────

async function tgSend(text: string): Promise<void> {
  try {
    const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: CHAT_ID, text, parse_mode: "Markdown" }),
    });
  } catch { /* best effort */ }
}

// ─── Run agent ────────────────────────────────────────────────────────────────

async function run() {
  const startTime = Date.now();

  if (!fs.existsSync(PROJECT_PATH)) {
    await tgSend(`❌ *Task ${TASK_ID} failed*\nProject path not found: \`${PROJECT_PATH}\``);
    updateTask(TASK_ID, { status: "failed", finishedAt: new Date().toISOString(), summary: "Project path not found" });
    process.exit(1);
  }
  process.chdir(PROJECT_PATH);

  const authStorage  = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);

  let settingsManager = SettingsManager.create(AGENT_DIR);
  let model: any | undefined;
  if (MODEL_SPEC) {
    const slash = MODEL_SPEC.indexOf("/");
    if (slash <= 0 || slash === MODEL_SPEC.length - 1) {
      throw new Error(`Invalid --model ${MODEL_SPEC}; expected provider/model-id`);
    }
    const provider = MODEL_SPEC.slice(0, slash);
    const modelId = MODEL_SPEC.slice(slash + 1);
    model = modelRegistry.find(provider, modelId);
    if (!model) throw new Error(`Model not found: ${MODEL_SPEC}`);
    settingsManager = SettingsManager.inMemory({
      defaultProvider: provider,
      defaultModel: modelId,
      defaultThinkingLevel: "xhigh",
    });
  }

  const sessionDir = path.join(BOT_ROOT, "agent-sessions", TASK_ID);
  fs.mkdirSync(sessionDir, { recursive: true });

  const loader = new DefaultResourceLoader({
    cwd: PROJECT_PATH,
    agentDir: AGENT_DIR,
    settingsManager,
    systemPromptOverride: () =>
      `You are Mr Chow, a senior developer and AI builder. You are working autonomously on the "${PROJECT}" project.\n` +
      `Project path: ${PROJECT_PATH}\n\n` +
      `Rules:\n` +
      `- Complete the task thoroughly and independently\n` +
      `- Use all available tools (bash, read, edit, write, web search, etc.)\n` +
      `- When done, end your final message with:\n` +
      `  DONE: <2-3 sentence summary of what you changed and why>\n` +
      `- If you hit a blocker you can't resolve, say:\n` +
      `  BLOCKED: <what's blocking you and what you need>`,
  });
  await loader.reload();

  const { session } = await createAgentSession({
    sessionManager: SessionManager.create(PROJECT_PATH, sessionDir),
    authStorage,
    modelRegistry,
    settingsManager,
    ...(model ? { model } : {}),
    resourceLoader: loader,
  });

  let output = "";
  let toolsUsed: string[] = [];
  let lastToolName = "";

  const unsub = session.subscribe((event) => {
    switch (event.type) {
      case "message_update":
        if (event.assistantMessageEvent.type === "text_delta") {
          output += event.assistantMessageEvent.delta;
          process.stdout.write(event.assistantMessageEvent.delta);
        }
        break;
      case "tool_execution_start":
        lastToolName = event.toolName;
        console.log(`\n[tool] ${event.toolName}`);
        if (!toolsUsed.includes(event.toolName)) toolsUsed.push(event.toolName);
        break;
    }
  });

  // ── Heartbeat: ping every 5 minutes so you know it's alive ───────────────
  const HEARTBEAT_MS = 5 * 60 * 1000;
  const heartbeat = setInterval(async () => {
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    const mins = Math.floor(elapsed / 60);
    const tool = lastToolName ? ` (last: \`${lastToolName}\`)` : "";
    await tgSend(`⏳ *Still working: ${PROJECT}*\n_${TASK_DESC.slice(0, 80)}_\n\n${mins}min elapsed${tool}`);
  }, HEARTBEAT_MS);

  let status: "done" | "failed" = "done";
  let summary = "";

  try {
    await session.prompt(
      `Task: ${TASK_DESC}\n\n` +
      `Work through this completely and independently. ` +
      `When finished, write "DONE: " followed by a 2-3 sentence summary of what you changed.`
    );
    unsub();
    clearInterval(heartbeat);

    // Extract summary (last DONE: line)
    const doneMatch  = output.match(/DONE:\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)/s);
    const blockMatch = output.match(/BLOCKED:\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)/s);
    summary = doneMatch
      ? doneMatch[1].trim()
      : blockMatch
        ? `⚠️ Blocked: ${blockMatch[1].trim()}`
        : output.slice(-400).trim();

    const elapsed  = Math.round((Date.now() - startTime) / 1000);
    const mins     = Math.floor(elapsed / 60);
    const secs     = elapsed % 60;
    const timeStr  = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
    const toolStr  = toolsUsed.length ? `\nTools: ${toolsUsed.join(", ")}` : "";

    writeOutput(
      TASK_ID,
      `# Task: ${TASK_DESC}\n\nProject: ${PROJECT}\nPath: ${PROJECT_PATH}\n` +
      `Started: ${new Date(startTime).toISOString()}\nElapsed: ${timeStr}\n\n## Output\n\n${output}`
    );

    updateTask(TASK_ID, { status: "done", finishedAt: new Date().toISOString(), summary });

    const emoji = blockMatch ? "⚠️" : "✅";
    await tgSend(
      `${emoji} *Agent done: ${PROJECT}*\n` +
      `_${TASK_DESC.slice(0, 100)}_\n\n` +
      `${summary}\n\n` +
      `⏱ ${timeStr}${toolStr}\n` +
      `/review ${TASK_ID}`
    );

  } catch (err: any) {
    clearInterval(heartbeat);
    unsub();
    summary = err?.message ?? String(err);
    updateTask(TASK_ID, { status: "failed", finishedAt: new Date().toISOString(), summary });
    await tgSend(`❌ *Agent failed: ${PROJECT}*\n_${TASK_DESC.slice(0, 80)}_\n\nError: ${summary.slice(0, 300)}`);
    process.exit(1);
  }

  session.dispose();
  process.exit(0);
}

run().catch(async (err) => {
  console.error("[agent-runner] fatal:", err);
  await tgSend(`💀 *Agent crashed: ${PROJECT}*\n${String(err).slice(0, 300)}`);
  process.exit(1);
});
