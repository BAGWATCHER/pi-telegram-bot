import "dotenv/config";
import * as http from "node:http";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

// ─── Config ───────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env.RELAY_PORT ?? "3001");
const SECRET = process.env.RELAY_SECRET ?? "";
const STORE_FILE = path.join(os.homedir(), "pi-telegram-bot", "relay-store.json");
const MAX_MESSAGES_PER_CHAT = 50;

// ─── Store ────────────────────────────────────────────────────────────────────

interface RelayMessage {
  id: string;
  chatId: string;
  botName: string;
  role: "user" | "bot";
  text: string;
  ts: number;
}

type Store = Record<string, RelayMessage[]>;

function loadStore(): Store {
  try {
    if (fs.existsSync(STORE_FILE)) {
      return JSON.parse(fs.readFileSync(STORE_FILE, "utf8"));
    }
  } catch {}
  return {};
}

function saveStore(store: Store) {
  fs.mkdirSync(path.dirname(STORE_FILE), { recursive: true });
  fs.writeFileSync(STORE_FILE, JSON.stringify(store, null, 2));
}

let store: Store = loadStore();

function addMessage(msg: Omit<RelayMessage, "id" | "ts">): RelayMessage {
  const full: RelayMessage = {
    ...msg,
    id: Math.random().toString(36).slice(2),
    ts: Date.now(),
  };
  if (!store[msg.chatId]) store[msg.chatId] = [];
  store[msg.chatId].push(full);
  // Trim to max
  if (store[msg.chatId].length > MAX_MESSAGES_PER_CHAT) {
    store[msg.chatId] = store[msg.chatId].slice(-MAX_MESSAGES_PER_CHAT);
  }
  saveStore(store);
  return full;
}

function getMessages(chatId: string, limit = 20): RelayMessage[] {
  const msgs = store[chatId] ?? [];
  return msgs.slice(-limit);
}

// ─── HTTP Server ──────────────────────────────────────────────────────────────

function readBody(req: http.IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function checkAuth(req: http.IncomingMessage): boolean {
  if (!SECRET) return true;
  return req.headers["x-relay-secret"] === SECRET;
}

function json(res: http.ServerResponse, status: number, data: unknown) {
  const body = JSON.stringify(data);
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  if (!checkAuth(req)) {
    return json(res, 401, { error: "Unauthorized" });
  }

  const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);

  // POST /message — add a message
  if (req.method === "POST" && url.pathname === "/message") {
    try {
      const body = await readBody(req);
      const { chatId, botName, role, text } = JSON.parse(body);
      if (!chatId || !botName || !role || !text) {
        return json(res, 400, { error: "Missing fields: chatId, botName, role, text" });
      }
      const msg = addMessage({ chatId, botName, role, text });
      console.log(`[relay] +msg chatId=${chatId} bot=${botName} role=${role} len=${text.length}`);
      return json(res, 200, msg);
    } catch (e: any) {
      return json(res, 400, { error: e.message });
    }
  }

  // GET /messages/:chatId?limit=20 — fetch recent messages
  if (req.method === "GET" && url.pathname.startsWith("/messages/")) {
    const chatId = url.pathname.slice("/messages/".length);
    const limit = parseInt(url.searchParams.get("limit") ?? "20");
    const msgs = getMessages(chatId, limit);
    return json(res, 200, msgs);
  }

  // GET /health
  if (req.method === "GET" && url.pathname === "/health") {
    return json(res, 200, { ok: true, chats: Object.keys(store).length });
  }

  return json(res, 404, { error: "Not found" });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`🔗 Relay server running on 0.0.0.0:${PORT}`);
  console.log(`   Health: http://localhost:${PORT}/health`);
  if (SECRET) console.log(`   Auth: x-relay-secret required`);
  else console.log(`   ⚠️  No RELAY_SECRET set — open access!`);
});
