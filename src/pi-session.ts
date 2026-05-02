import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import {
  AuthStorage,
  ModelRegistry,
  SettingsManager,
  type AgentSession,
} from "@mariozechner/pi-coding-agent";

const DEFAULT_CHOW_PROVIDER = "openai-codex";
const DEFAULT_CHOW_MODEL = "gpt-5.3-codex";
const DEFAULT_CHOW_FALLBACK_MODELS = [
  "google/gemma-4-31b-it",
  "google/gemini-2.5-flash-lite",
  "openai-codex/gpt-5.4-mini",
  "openai-codex/gpt-5.3-codex",
];
const FORBIDDEN_MODELS = new Set(["google/gemini-2.5-flash"]);
const ALLOWED_PROVIDERS = new Set(["openai-codex", "anthropic", "google", "ollama"]);

const CHOW_PROVIDER = (process.env.CHOW_PI_PROVIDER?.trim() || DEFAULT_CHOW_PROVIDER).trim();
const CHOW_MODEL = (process.env.CHOW_PI_MODEL?.trim() || DEFAULT_CHOW_MODEL).trim();
const CHOW_FALLBACK_MODELS = (process.env.CHOW_PI_FALLBACK_MODELS?.trim() || DEFAULT_CHOW_FALLBACK_MODELS.join(",")).trim();
const HOME_DIR = os.homedir();
const CODEX_AUTH_PATH = path.join(HOME_DIR, ".codex", "auth.json");
const PI_AUTH_PATH = path.join(HOME_DIR, ".pi", "agent", "auth.json");
const PINNED_AUTH_PROFILE_DIR = process.env.CHOW_PINNED_AUTH_PROFILE_DIR?.trim() || "";

export type ChowModelSelection = { provider: string; modelId: string };

function readJsonFile(filePath: string): any | null {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function decodeJwtPayload(token: string): Record<string, any> | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const payload = parts[1] + "=".repeat((4 - (parts[1].length % 4)) % 4);
    return JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
  } catch {
    return null;
  }
}

function readPiOAuthExpiryMs(): number | null {
  const piAuth = readJsonFile(PI_AUTH_PATH);
  const wrapped = piAuth?.["openai-codex"];
  const expires = wrapped?.expires;
  return typeof expires === "number" && Number.isFinite(expires) ? expires : null;
}

function rebuildPiAuthFromCodex(): boolean {
  const codexAuth = readJsonFile(CODEX_AUTH_PATH);
  const tokens = codexAuth?.tokens;
  const access = typeof tokens?.access_token === "string" ? tokens.access_token : "";
  const refresh = typeof tokens?.refresh_token === "string" ? tokens.refresh_token : "";
  if (!access || !refresh) return false;

  const payload = decodeJwtPayload(access);
  const expSeconds = Number(payload?.exp || 0);
  if (!expSeconds) return false;

  const accountId =
    tokens?.account_id ||
    payload?.["https://api.openai.com/auth"]?.chatgpt_account_id ||
    null;

  fs.mkdirSync(path.dirname(PI_AUTH_PATH), { recursive: true });
  fs.writeFileSync(
    PI_AUTH_PATH,
    JSON.stringify(
      {
        "openai-codex": {
          type: "oauth",
          access,
          refresh,
          expires: expSeconds * 1000,
          accountId,
        },
      },
      null,
      2
    ) + "\n",
    "utf8"
  );
  return true;
}

function restorePinnedAuthProfile(): boolean {
  if (!PINNED_AUTH_PROFILE_DIR) return false;
  const codexPath = path.join(PINNED_AUTH_PROFILE_DIR, "codex-auth.json");
  const piPath = path.join(PINNED_AUTH_PROFILE_DIR, "pi-auth.json");
  if (!fs.existsSync(codexPath) || !fs.existsSync(piPath)) return false;

  fs.mkdirSync(path.dirname(CODEX_AUTH_PATH), { recursive: true });
  fs.mkdirSync(path.dirname(PI_AUTH_PATH), { recursive: true });
  fs.copyFileSync(codexPath, CODEX_AUTH_PATH);
  fs.copyFileSync(piPath, PI_AUTH_PATH);
  return true;
}

function ensureOpenAICodexOAuthReady(): void {
  if (CHOW_PROVIDER !== "openai-codex") return;

  const now = Date.now();
  const expiresMs = readPiOAuthExpiryMs();
  const minFreshMs = 10 * 60 * 1000;
  if (expiresMs && expiresMs - now > minFreshMs) return;

  const restoredPinned = restorePinnedAuthProfile();
  const refreshedExpiry = readPiOAuthExpiryMs();
  if (refreshedExpiry && refreshedExpiry - now > minFreshMs) {
    console.log(
      `[pi-session] Refreshed Chow OAuth from ${restoredPinned ? "pinned auth profile" : "local pi auth"}`
    );
    return;
  }

  if (rebuildPiAuthFromCodex()) {
    console.log("[pi-session] Rebuilt Chow OAuth from ~/.codex/auth.json");
    return;
  }

  console.warn("[pi-session] Chow OAuth may be stale: could not refresh ~/.pi/agent/auth.json");
}

function parseModelSpec(spec: string): ChowModelSelection | null {
  const trimmed = spec.trim();
  if (!trimmed) return null;
  const slash = trimmed.indexOf("/");
  if (slash <= 0 || slash === trimmed.length - 1) return null;
  return {
    provider: trimmed.slice(0, slash).trim(),
    modelId: trimmed.slice(slash + 1).trim(),
  };
}

export function getChowModelSelection(override?: ChowModelSelection): ChowModelSelection {
  const selection = {
    provider: (override?.provider?.trim() || CHOW_PROVIDER).trim(),
    modelId: (override?.modelId?.trim() || CHOW_MODEL).trim(),
  };
  console.log(`[pi-session] Using model from env: ${selection.provider}/${selection.modelId}`);
  const key = `${selection.provider}/${selection.modelId}`;

  if (FORBIDDEN_MODELS.has(key)) {
    throw new Error(`Chow is not allowed to use ${key}. Set CHOW_PI_PROVIDER/CHOW_PI_MODEL to an approved model.`);
  }

  if (!ALLOWED_PROVIDERS.has(selection.provider)) {
    throw new Error(
      `Chow provider ${selection.provider} is not allowed. Allowed providers: ${Array.from(ALLOWED_PROVIDERS).join(", ")}`
    );
  }

  return selection;
}

export function getChowFallbackSelections(): ChowModelSelection[] {
  const primaryKey = `${CHOW_PROVIDER}/${CHOW_MODEL}`;
  const seen = new Set<string>([primaryKey]);
  const selections: ChowModelSelection[] = [];

  for (const raw of CHOW_FALLBACK_MODELS.split(",")) {
    const parsed = parseModelSpec(raw);
    if (!parsed) continue;
    const key = `${parsed.provider}/${parsed.modelId}`;
    if (seen.has(key) || FORBIDDEN_MODELS.has(key) || !ALLOWED_PROVIDERS.has(parsed.provider)) {
      continue;
    }
    seen.add(key);
    selections.push(parsed);
  }

  return selections;
}

export function findChowFallbackModel(excludeKeys: string[] = []): { selection: ChowModelSelection; model: any } | null {
  const authStorage = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);
  const excluded = new Set(excludeKeys.map((key) => key.trim()).filter(Boolean));

  for (const selection of getChowFallbackSelections()) {
    const key = `${selection.provider}/${selection.modelId}`;
    if (excluded.has(key)) continue;
    const model = modelRegistry.find(selection.provider, selection.modelId);
    if (model) {
      return { selection, model };
    }
  }

  return null;
}

export function createChowRuntime(selectionOverride?: ChowModelSelection) {
  const { provider, modelId } = getChowModelSelection(selectionOverride);
  ensureOpenAICodexOAuthReady();
  const authStorage = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);
  const settingsManager = SettingsManager.inMemory({
    defaultProvider: provider,
    defaultModel: modelId,
    defaultThinkingLevel: "xhigh",
  });

  const model = modelRegistry.find(provider, modelId);
  if (!model) {
    const available = modelRegistry
      .getAvailable()
      .slice(0, 20)
      .map((item) => `${item.provider}/${item.id}`)
      .join(", ");
    console.error(`[pi-session ERROR] Model ${provider}/${modelId} NOT found in registry! Available: ${available.slice(0, 100)}...`);
    throw new Error(
      `Chow model ${provider}/${modelId} not found. Available models: ${available || "none"}`
    );
  }
  console.log(`[pi-session] Model loaded: ${model.provider}/${model.id}`);

  return { authStorage, modelRegistry, settingsManager, model };
}

export async function pinSessionModel(session: AgentSession, expectedModel: { provider: string; id: string }): Promise<void> {
  if (session.model?.provider === expectedModel.provider && session.model?.id === expectedModel.id) {
    return;
  }
  await session.setModel(expectedModel as any);
}
