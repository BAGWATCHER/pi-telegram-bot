import express, { Request, Response } from "express";
import { execSync, spawn, exec } from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.DASH_PORT || 3848;
const MEMORY_DIR = path.join(os.homedir(), "pi-telegram-bot", "memory");
const PUBLIC_DIR = path.join(__dirname, "public");

app.use(express.json());
app.use(express.static(PUBLIC_DIR));

// ── helpers ────────────────────────────────────────────────────────────────

function sh(cmd: string): string {
  try { return execSync(cmd, { encoding: "utf8", timeout: 5000 }).trim(); }
  catch { return ""; }
}

function pm2List(): any[] {
  try {
    const raw = sh("pm2 jlist");
    return JSON.parse(raw) || [];
  } catch { return []; }
}

function diskInfo() {
  const out = sh("df -h / | tail -1");
  const parts = out.split(/\s+/);
  return { total: parts[1], used: parts[2], free: parts[3], pct: parts[4] };
}

function sysUptime() {
  return sh("uptime | awk -F'up ' '{print $2}' | awk -F', ' '{print $1}'");
}

// ── VMs to monitor ─────────────────────────────────────────────────────────
const VMS = [
  { name: "chow", host: "exe.dev → chow", jumpHost: "exe.dev" },
  { name: "hector-vm", host: "35.221.21.7", jumpHost: null },
];

function checkVm(host: string): Promise<"online" | "offline"> {
  return new Promise((resolve) => {
    const proc = exec(`ssh -o ConnectTimeout=4 -o BatchMode=yes ${host} "echo ok" 2>/dev/null`);
    const timer = setTimeout(() => { proc.kill(); resolve("offline"); }, 5000);
    proc.on("exit", (code) => { clearTimeout(timer); resolve(code === 0 ? "online" : "offline"); });
  });
}

// ── API routes ─────────────────────────────────────────────────────────────

app.get("/api/status", async (_req: Request, res: Response) => {
  const procs = pm2List().map((p) => ({
    name: p.name,
    status: p.pm2_env?.status ?? "unknown",
    pid: p.pid,
    restarts: p.pm2_env?.restart_time ?? 0,
    uptime: p.pm2_env?.pm_uptime,
    memory: p.monit?.memory ?? 0,
    cpu: p.monit?.cpu ?? 0,
  }));

  const disk = diskInfo();
  const uptime = sysUptime();

  // VM checks (parallel, fast timeout)
  const vmChecks = await Promise.all(
    VMS.map(async (vm) => ({
      ...vm,
      status: await checkVm(vm.name),
    }))
  );

  res.json({ procs, disk, uptime, vms: vmChecks });
});

// Memory CRUD
app.get("/api/memory/:chatId", (req: Request, res: Response) => {
  const file = path.join(MEMORY_DIR, `${req.params.chatId}.md`);
  if (!fs.existsSync(file)) return res.json({ content: "" });
  res.json({ content: fs.readFileSync(file, "utf8") });
});

app.post("/api/memory/:chatId", (req: Request, res: Response) => {
  const file = path.join(MEMORY_DIR, `${req.params.chatId}.md`);
  fs.mkdirSync(MEMORY_DIR, { recursive: true });
  fs.writeFileSync(file, req.body.content ?? "");
  res.json({ ok: true });
});

// List memory files
app.get("/api/memory", (_req: Request, res: Response) => {
  if (!fs.existsSync(MEMORY_DIR)) return res.json([]);
  const files = fs.readdirSync(MEMORY_DIR).filter((f) => f.endsWith(".md"));
  const result = files.map((f) => {
    const id = f.replace(".md", "");
    const content = fs.readFileSync(path.join(MEMORY_DIR, f), "utf8");
    const preview = content.split("\n").find((l) => l.trim() && !l.startsWith("#")) || "";
    return { id, preview: preview.slice(0, 80) };
  });
  res.json(result);
});

// PM2 actions
app.post("/api/pm2/:action/:name", (req: Request, res: Response) => {
  const { action, name } = req.params;
  const allowed = ["restart", "stop", "start"];
  if (!allowed.includes(action)) return res.status(400).json({ error: "bad action" });
  // Whitelist names to avoid injection
  if (!/^[a-zA-Z0-9_-]+$/.test(name)) return res.status(400).json({ error: "bad name" });
  const out = sh(`pm2 ${action} ${name} 2>&1`);
  res.json({ ok: true, out });
});

// ── SSE log stream ─────────────────────────────────────────────────────────
app.get("/api/logs/stream", (req: Request, res: Response) => {
  const proc = req.query.proc as string || "hector";
  if (!/^[a-zA-Z0-9_-]+$/.test(proc)) { res.status(400).end(); return; }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.flushHeaders();

  // Get last 40 lines from pm2 log file first
  const logFile = path.join(os.homedir(), `.pm2/logs/${proc}-out.log`);
  if (fs.existsSync(logFile)) {
    const last = sh(`tail -40 ${logFile}`);
    for (const line of last.split("\n")) {
      if (line.trim()) res.write(`data: ${JSON.stringify({ t: "log", line, proc })}\n\n`);
    }
  }

  // Then tail -f both out and err
  const tail = spawn("tail", ["-f", "-n", "0",
    path.join(os.homedir(), `.pm2/logs/${proc}-out.log`),
    path.join(os.homedir(), `.pm2/logs/${proc}-error.log`),
  ]);

  tail.stdout.on("data", (data: Buffer) => {
    for (const line of data.toString().split("\n")) {
      if (line.trim()) res.write(`data: ${JSON.stringify({ t: "log", line, proc })}\n\n`);
    }
  });

  // Heartbeat every 15s
  const hb = setInterval(() => res.write(`: heartbeat\n\n`), 15000);

  req.on("close", () => { clearInterval(hb); tail.kill(); });
});

// ── Catch-all → index.html ─────────────────────────────────────────────────
app.get("/{*splat}", (_req: Request, res: Response) => {
  res.sendFile(path.join(PUBLIC_DIR, "index.html"));
});

app.listen(PORT, () => {
  console.log(`🖥️  Hector dashboard running at http://localhost:${PORT}`);
});
