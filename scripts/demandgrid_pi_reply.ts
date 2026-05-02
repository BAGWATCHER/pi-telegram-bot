import "dotenv/config";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  AuthStorage,
  createAgentSession,
  DefaultResourceLoader,
  ModelRegistry,
  SessionManager,
} from "@mariozechner/pi-coding-agent";

type PromptPayload = {
  user_message?: string;
  intent?: string;
  scope?: Record<string, unknown>;
  tool_calls?: unknown[];
  suggested_actions?: string[];
  grounded_reply?: string;
  cards?: unknown[];
};

const PROVIDER = process.env.DEMANDGRID_PI_PROVIDER?.trim() || "openai-codex";
const MODEL = process.env.DEMANDGRID_PI_MODEL?.trim() || "gpt-5.4";
const THINKING = (process.env.DEMANDGRID_PI_THINKING?.trim() || "medium") as
  | "off"
  | "minimal"
  | "low"
  | "medium"
  | "high"
  | "xhigh";
const SESSION_DIR = path.join(os.homedir(), "pi-telegram-bot", "sessions", "demandgrid-copilot");

fs.mkdirSync(SESSION_DIR, { recursive: true });

function readStdin(): Promise<string> {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

async function main() {
  const raw = await readStdin();
  const payload = (raw ? JSON.parse(raw) : {}) as PromptPayload;

  const authStorage = AuthStorage.create();
  const modelRegistry = new ModelRegistry(authStorage);
  const model = modelRegistry.find(PROVIDER, MODEL);
  if (!model) {
    process.stdout.write(JSON.stringify({ reply: "", error: `model_not_found:${PROVIDER}/${MODEL}` }));
    return;
  }

  const loader = new DefaultResourceLoader({
    systemPromptOverride: () =>
      [
        "You are Chow inside DemandGrid.",
        "You are an execution-focused sales operator brain, not a generic analyst chatbot.",
        "You must stay grounded in the supplied DemandGrid tool output.",
        "Do not invent data, leads, prices, contact paths, or trigger evidence.",
        "Prefer direct operator language, clear next steps, and practical scripts.",
        "Keep replies concise and practical.",
      ].join("\n"),
  });
  await loader.reload();

  const { session } = await createAgentSession({
    sessionManager: SessionManager.continueRecent(process.cwd(), SESSION_DIR),
    authStorage,
    modelRegistry,
    model,
    thinkingLevel: THINKING,
    resourceLoader: loader,
  });

  const prompt = [
    "Rewrite the grounded DemandGrid Chow answer for a sales operator.",
    "Rules:",
    "- Use only the provided grounded data.",
    "- Keep the answer under 120 words.",
    "- Preserve any concrete scope, lead, route, or status facts.",
    "- If the grounded reply is already correct, tighten it rather than expanding it.",
    "",
    JSON.stringify(payload, null, 2),
  ].join("\n");

  await session.prompt(prompt);
  const reply = session.getLastAssistantText()?.trim() || "";
  process.stdout.write(JSON.stringify({ reply }));
}

main().catch((err) => {
  process.stdout.write(JSON.stringify({ reply: "", error: String(err instanceof Error ? err.message : err) }));
  process.exit(1);
});
