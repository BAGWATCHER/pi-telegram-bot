import "dotenv/config";
import {
  createAgentSession,
  DefaultResourceLoader,
  SessionManager,
  type AgentSession,
} from "@mariozechner/pi-coding-agent";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { createChowRuntime, type ChowModelSelection } from "../src/pi-session.js";

function arg(name: string): string | null {
  const idx = process.argv.indexOf(`--${name}`);
  if (idx === -1 || !process.argv[idx + 1]) return null;
  return process.argv[idx + 1];
}

async function captureFinalText(session: AgentSession): Promise<string> {
  for (let i = 0; i < 10; i++) {
    const text = session.getLastAssistantText()?.trim() || "";
    if (text) return text;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  return "";
}

async function main() {
  const modelArg = arg("model");
  const providerArg = arg("provider") || "openai-codex";
  const prompt = arg("prompt") || "Reply with exactly: OK";

  const selection: ChowModelSelection | undefined = modelArg
    ? { provider: providerArg, modelId: modelArg }
    : undefined;

  const { authStorage, modelRegistry, settingsManager, model } = createChowRuntime(selection);

  const sessionDir = path.join(os.tmpdir(), "chow-auth-smoke");
  fs.mkdirSync(sessionDir, { recursive: true });
  const loader = new DefaultResourceLoader({
    systemPromptOverride: () => "Reply in plain text only. Do not use tools.",
  });
  await loader.reload();

  const { session } = await createAgentSession({
    sessionManager: SessionManager.create(process.cwd(), sessionDir),
    authStorage,
    modelRegistry,
    settingsManager,
    model,
    resourceLoader: loader,
  });

  const events: string[] = [];
  session.subscribe((event) => {
    if (event.type === "message_end") {
      const msg = (event as any).message;
      const usage = msg?.usage;
      const payload = {
        role: msg?.role,
        contentCount: Array.isArray(msg?.content) ? msg.content.length : null,
        model: msg?.model,
        stopReason: msg?.stopReason ?? null,
        errorMessage: msg?.errorMessage ?? null,
        usage,
      };
      events.push(JSON.stringify(payload));
    }
  });

  try {
    await session.prompt(prompt, { streamingBehavior: "steer" });
    const text = await captureFinalText(session);
    console.log(JSON.stringify({
      ok: !!text,
      model: `${model.provider}/${model.id}`,
      text,
      events,
    }, null, 2));
  } finally {
    session.dispose();
  }
}

main().catch((err) => {
  console.error("[chow-auth-smoke] failed:", err?.message ?? String(err));
  process.exit(1);
});
