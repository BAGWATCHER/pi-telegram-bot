import { spawn, spawnSync } from "node:child_process";

export type MeetTransport = "chrome" | "chrome-node" | "twilio";
export type MeetMode = "realtime" | "transcribe";

export type MeetCommandResult<T = any> = {
  ok: boolean;
  command: string[];
  exitCode: number;
  stdout: string;
  stderr: string;
  durationMs: number;
  data?: T;
  error?: string;
};

const MEET_ENABLED = String(process.env.MEET_SIDECAR_ENABLED ?? "1").trim() !== "0";
const MEET_TIMEOUT_MS = Math.max(5_000, Number(process.env.MEET_SIDECAR_TIMEOUT_MS ?? 120_000));
const MEET_DEFAULT_TRANSPORT = normalizeTransport(process.env.MEET_SIDECAR_DEFAULT_TRANSPORT) ?? "chrome-node";
const MEET_DEFAULT_MODE = normalizeMode(process.env.MEET_SIDECAR_DEFAULT_MODE) ?? "realtime";
const OPENCLAW_LAUNCH_CMD = process.env.OPENCLAW_LAUNCH_CMD?.trim() || "";
const OPENCLAW_BIN = process.env.OPENCLAW_BIN?.trim() || "openclaw";

let cachedLauncher: string[] | null = null;

function normalizeTransport(value: unknown): MeetTransport | undefined {
  const lower = String(value ?? "").trim().toLowerCase();
  if (lower === "chrome" || lower === "chrome-node" || lower === "twilio") return lower;
  return undefined;
}

function normalizeMode(value: unknown): MeetMode | undefined {
  const lower = String(value ?? "").trim().toLowerCase();
  if (lower === "realtime" || lower === "transcribe") return lower;
  return undefined;
}

function splitCommandLine(input: string): string[] {
  const out: string[] = [];
  let token = "";
  let quote: '"' | "'" | null = null;

  for (let i = 0; i < input.length; i += 1) {
    const ch = input[i]!;
    if (quote) {
      if (ch === quote) {
        quote = null;
      } else if (ch === "\\" && i + 1 < input.length) {
        token += input[i + 1];
        i += 1;
      } else {
        token += ch;
      }
      continue;
    }

    if (ch === '"' || ch === "'") {
      quote = ch;
      continue;
    }

    if (/\s/.test(ch)) {
      if (token) {
        out.push(token);
        token = "";
      }
      continue;
    }

    token += ch;
  }

  if (token) out.push(token);
  return out;
}

function canExecute(command: string): boolean {
  try {
    const result = spawnSync(command, ["--version"], {
      stdio: "ignore",
      timeout: 8_000,
      env: process.env,
    });
    return result.status === 0;
  } catch {
    return false;
  }
}

function resolveLauncher(): string[] {
  if (cachedLauncher) return cachedLauncher;

  if (OPENCLAW_LAUNCH_CMD) {
    const parsed = splitCommandLine(OPENCLAW_LAUNCH_CMD);
    if (parsed.length > 0) {
      cachedLauncher = parsed;
      return cachedLauncher;
    }
  }

  if (canExecute(OPENCLAW_BIN)) {
    cachedLauncher = [OPENCLAW_BIN];
    return cachedLauncher;
  }

  cachedLauncher = ["npx", "-y", "openclaw"];
  return cachedLauncher;
}

function extractJsonFromText(raw: string): any | undefined {
  const text = raw.trim();
  if (!text) return undefined;

  const candidates: string[] = [text];
  const firstObj = text.indexOf("{");
  const lastObj = text.lastIndexOf("}");
  if (firstObj >= 0 && lastObj > firstObj) {
    candidates.push(text.slice(firstObj, lastObj + 1));
  }
  const firstArr = text.indexOf("[");
  const lastArr = text.lastIndexOf("]");
  if (firstArr >= 0 && lastArr > firstArr) {
    candidates.push(text.slice(firstArr, lastArr + 1));
  }

  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const line = lines[i]!;
    if (line.startsWith("{") || line.startsWith("[")) {
      candidates.push(line);
    }
  }

  for (const candidate of candidates) {
    try {
      return JSON.parse(candidate);
    } catch {
      // try next
    }
  }
  return undefined;
}

async function runGoogleMeetCommand<T = any>(args: string[], timeoutMs = MEET_TIMEOUT_MS): Promise<MeetCommandResult<T>> {
  const launcher = resolveLauncher();
  const command = [...launcher, "googlemeet", ...args];
  const started = Date.now();

  return await new Promise((resolve) => {
    const child = spawn(command[0]!, command.slice(1), {
      cwd: process.cwd(),
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    let timedOut = false;

    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });

    const timer = setTimeout(() => {
      timedOut = true;
      try {
        child.kill("SIGTERM");
      } catch {
        // ignore
      }
      setTimeout(() => {
        try {
          child.kill("SIGKILL");
        } catch {
          // ignore
        }
      }, 1_500).unref();
    }, timeoutMs);
    timer.unref();

    child.on("close", (code) => {
      clearTimeout(timer);
      const durationMs = Date.now() - started;
      const exitCode = typeof code === "number" ? code : 1;
      const parsed = extractJsonFromText(stdout) ?? extractJsonFromText(stderr) ?? extractJsonFromText(`${stdout}\n${stderr}`);

      if (exitCode === 0) {
        resolve({
          ok: true,
          command,
          exitCode,
          stdout,
          stderr,
          durationMs,
          data: parsed as T,
        });
        return;
      }

      const fallbackError = timedOut
        ? `googlemeet command timed out after ${timeoutMs}ms`
        : String((parsed as any)?.error || (parsed as any)?.message || stderr.trim() || stdout.trim() || `googlemeet exited with code ${exitCode}`);

      resolve({
        ok: false,
        command,
        exitCode,
        stdout,
        stderr,
        durationMs,
        data: parsed as T,
        error: fallbackError,
      });
    });

    child.on("error", (err) => {
      clearTimeout(timer);
      resolve({
        ok: false,
        command,
        exitCode: 1,
        stdout,
        stderr,
        durationMs: Date.now() - started,
        error: String(err?.message || err),
      });
    });
  });
}

export function isMeetSidecarEnabled(): boolean {
  return MEET_ENABLED;
}

export function getMeetSidecarRuntimeInfo(): {
  enabled: boolean;
  timeoutMs: number;
  defaultTransport: MeetTransport;
  defaultMode: MeetMode;
  launcher: string;
} {
  const launcher = resolveLauncher();
  return {
    enabled: MEET_ENABLED,
    timeoutMs: MEET_TIMEOUT_MS,
    defaultTransport: MEET_DEFAULT_TRANSPORT,
    defaultMode: MEET_DEFAULT_MODE,
    launcher: launcher.join(" "),
  };
}

export function normalizeMeetUrlOrThrow(value: string): string {
  const raw = String(value || "").trim();
  if (!raw) throw new Error("Meet URL is required");

  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error("Meet URL must be a valid https://meet.google.com/... link");
  }

  if (parsed.protocol !== "https:" || parsed.hostname.toLowerCase() !== "meet.google.com") {
    throw new Error("Meet URL must be on https://meet.google.com");
  }

  if (!/^\/[a-z]{3}-[a-z]{4}-[a-z]{3}(?:$|[/?#])/i.test(parsed.pathname)) {
    throw new Error("Meet URL must include a valid meeting code path");
  }

  return parsed.toString();
}

export async function meetSetup(options: { transport?: MeetTransport } = {}) {
  const args = ["setup", "--json"];
  const transport = normalizeTransport(options.transport);
  if (transport) args.push("--transport", transport);
  return await runGoogleMeetCommand(args);
}

export async function meetJoin(options: {
  url: string;
  transport?: MeetTransport;
  mode?: MeetMode;
  message?: string;
}) {
  const args = ["join", normalizeMeetUrlOrThrow(options.url)];
  const transport = normalizeTransport(options.transport) ?? MEET_DEFAULT_TRANSPORT;
  const mode = normalizeMode(options.mode) ?? MEET_DEFAULT_MODE;
  args.push("--transport", transport, "--mode", mode);
  if (options.message?.trim()) args.push("--message", options.message.trim());
  return await runGoogleMeetCommand(args);
}

export async function meetStatus(options: { sessionId?: string } = {}) {
  const args = ["status"];
  if (options.sessionId?.trim()) args.push(options.sessionId.trim());
  return await runGoogleMeetCommand(args);
}

export async function meetRecoverCurrentTab(options: { url?: string; transport?: MeetTransport } = {}) {
  const args = ["recover-tab"];
  if (options.url?.trim()) args.push(normalizeMeetUrlOrThrow(options.url));
  const transport = normalizeTransport(options.transport);
  if (transport) args.push("--transport", transport);
  args.push("--json");
  return await runGoogleMeetCommand(args);
}

export async function meetLeave(sessionId: string) {
  const id = String(sessionId || "").trim();
  if (!id) throw new Error("sessionId is required");
  return await runGoogleMeetCommand(["leave", id]);
}

export async function meetSpeak(options: { sessionId: string; message?: string }) {
  const id = String(options.sessionId || "").trim();
  if (!id) throw new Error("sessionId is required");
  const args = ["speak", id];
  if (options.message?.trim()) args.push(options.message.trim());
  return await runGoogleMeetCommand(args);
}

export async function meetScreenshot(sessionId: string) {
  const id = String(sessionId || "").trim();
  if (!id) throw new Error("sessionId is required");
  return await runGoogleMeetCommand(["screenshot", id, "--json"]);
}

export function getMeetManualAction(payload: any): { reason?: string; message?: string } | null {
  if (!payload || typeof payload !== "object") return null;

  const directRequired = Boolean(payload.manualActionRequired);
  if (directRequired) {
    return {
      reason: String(payload.manualActionReason || "manual-action-required"),
      message: String(payload.manualActionMessage || "Manual action is required in Chrome before retrying."),
    };
  }

  const sessions = Array.isArray(payload.sessions)
    ? payload.sessions
    : payload.session
      ? [payload.session]
      : [];

  for (const session of sessions) {
    const health = session?.chrome?.health;
    if (health?.manualActionRequired) {
      return {
        reason: String(health.manualActionReason || "manual-action-required"),
        message: String(health.manualActionMessage || "Manual action is required in the meeting browser."),
      };
    }
  }

  return null;
}
