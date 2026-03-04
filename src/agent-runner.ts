/**
 * agent-runner.ts
 * Standalone headless pi agent. Spawned in a tmux session by /work command.
 * When done, POSTs result to Telegram directly so Chow doesn't need to wait.
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

function arg(name: string): string {
  const idx = process.argv.indexOf(`--${name}`);
  if (idx === -1 || !process.argv[idx + 1]) {
    console.error(`Missing --${name}`);
    process.exit(1);
  }
  return process.argv[idx + 1];
}

const TASK_ID = arg("task-id");
const PROJECT = arg("project");
const PROJECT_PATH = arg("project-path");
const TASK_DESC = arg("task");
const CHAT_ID = parseInt(arg("chat-id"), 10);
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN!;

console.log(`[agent-runner] task=${TASK_ID} project=${PROJECT} path=${PROJECT_PATH}`);
console.log(`[agent-runner] task: ${TASK_DESC}`);

// ─── Telegram notify ──────────────────────────────────────────────────────────

async function tgSend(text: string): Promise<void> {
  const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: CHAT_ID, text, parse_mode: "Markdown" }),
  });
}

// ─── Run agent ────────────────────────────────────────────────────────────────

async function run() {
  const startTime = Date.now();

  // Change to project directory
  if (!fs.existsSync(PROJECT_PATH)) {
    await tgSend(`❌ *Task ${TASK_ID} failed*\nProject path not found: \`${PROJECT_PATH}\``);
    updateTask(TASK_ID, { status: "failed", finishedAt: new Date().toISOString(), summary: "Project path not found" });
    process.exit(1);
  }
  process.chdir(PROJECT_PATH);

  const authStorage = AuthStorage.create();
  const modelRegistry = new ModelRegistry(authStorage);
  const settingsManager = SettingsManager.inMemory({ compaction: { enabled: true } });

  // Use task-specific session dir so it doesn't collide with Chow's chat sessions
  const sessionDir = path.join(process.cwd(), "agent-sessions", TASK_ID);
  fs.mkdirSync(sessionDir, { recursive: true });

  const loader = new DefaultResourceLoader({
    systemPromptOverride: () =>
      `You are a senior developer working autonomously on the "${PROJECT}" project at ${PROJECT_PATH}. ` +
      `You have full access to the codebase. Complete the assigned task thoroughly, then stop. ` +
      `At the end, write a concise summary of what you did (files changed, key decisions).`,
  });
  await loader.reload();

  const { session } = await createAgentSession({
    sessionManager: SessionManager.create(PROJECT_PATH, sessionDir),
    authStorage,
    modelRegistry,
    settingsManager,
    resourceLoader: loader,
  });

  let output = "";
  let toolsUsed: string[] = [];

  const unsub = session.subscribe((event) => {
    switch (event.type) {
      case "message_update":
        if (event.assistantMessageEvent.type === "text_delta") {
          output += event.assistantMessageEvent.delta;
          process.stdout.write(event.assistantMessageEvent.delta);
        }
        break;
      case "tool_execution_start":
        console.log(`\n[tool] ${event.toolName}`);
        if (!toolsUsed.includes(event.toolName)) toolsUsed.push(event.toolName);
        break;
    }
  });

  let status: "done" | "failed" = "done";
  let summary = "";

  try {
    await session.prompt(
      `Task: ${TASK_DESC}\n\n` +
      `Work through this completely. When finished, write "DONE: " followed by a 2-3 sentence summary of what you changed.`
    );
    unsub();

    // Extract summary from output (last DONE: line)
    const doneMatch = output.match(/DONE:\s*(.+?)(?:\n|$)/s);
    summary = doneMatch ? doneMatch[1].trim() : output.slice(-300).trim();

    const elapsed = Math.round((Date.now() - startTime) / 1000);
    const toolStr = toolsUsed.length ? `\nTools: ${toolsUsed.join(", ")}` : "";

    writeOutput(TASK_ID, `# Task: ${TASK_DESC}\n\nProject: ${PROJECT}\nPath: ${PROJECT_PATH}\nStarted: ${new Date(startTime).toISOString()}\nElapsed: ${elapsed}s\n\n## Output\n\n${output}`);

    updateTask(TASK_ID, {
      status: "done",
      finishedAt: new Date().toISOString(),
      summary,
    });

    await tgSend(
      `✅ *Agent done: ${PROJECT}*\n` +
      `Task: _${TASK_DESC}_\n\n` +
      `${summary}\n` +
      `⏱ ${elapsed}s${toolStr}\n\n` +
      `View full output: /review ${TASK_ID}`
    );

  } catch (err: any) {
    status = "failed";
    summary = err?.message ?? String(err);
    updateTask(TASK_ID, { status: "failed", finishedAt: new Date().toISOString(), summary });
    await tgSend(`❌ *Agent failed: ${PROJECT}*\nTask: _${TASK_DESC}_\n\nError: ${summary}`);
    process.exit(1);
  }

  session.dispose();
  process.exit(0);
}

run().catch((err) => {
  console.error("[agent-runner] fatal:", err);
  process.exit(1);
});
