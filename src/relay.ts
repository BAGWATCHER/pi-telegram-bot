// ─── Relay Client ─────────────────────────────────────────────────────────────
// Connects this bot to the shared group chat relay server.

export interface RelayMessage {
  id: string;
  chatId: string;
  botName: string;
  role: "user" | "bot";
  text: string;
  ts: number;
}

const RELAY_URL = process.env.RELAY_URL ?? "";
const RELAY_SECRET = process.env.RELAY_SECRET ?? "";

function relayHeaders(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (RELAY_SECRET) h["x-relay-secret"] = RELAY_SECRET;
  return h;
}

export function isRelayEnabled(): boolean {
  return !!RELAY_URL;
}

export async function relayPost(
  chatId: number,
  botName: string,
  role: "user" | "bot",
  text: string
): Promise<void> {
  if (!RELAY_URL) return;
  try {
    await fetch(`${RELAY_URL}/message`, {
      method: "POST",
      headers: relayHeaders(),
      body: JSON.stringify({ chatId: String(chatId), botName, role, text }),
    });
  } catch (e) {
    console.warn("[relay] POST failed:", e);
  }
}

export async function relayGet(chatId: number, limit = 20): Promise<RelayMessage[]> {
  if (!RELAY_URL) return [];
  try {
    const res = await fetch(`${RELAY_URL}/messages/${chatId}?limit=${limit}`, {
      headers: relayHeaders(),
    });
    if (!res.ok) return [];
    return (await res.json()) as RelayMessage[];
  } catch (e) {
    console.warn("[relay] GET failed:", e);
    return [];
  }
}

export function formatGroupContext(messages: RelayMessage[], myName: string): string {
  if (messages.length === 0) return "";

  const lines = messages.map((m) => {
    const who = m.role === "user" ? m.botName : `[${m.botName}]`;
    const preview = m.text.length > 400 ? m.text.slice(0, 400) + "…" : m.text;
    return `${who}: ${preview}`;
  });

  return (
    `--- GROUP CHAT HISTORY (most recent last) ---\n` +
    lines.join("\n") +
    `\n--- END HISTORY ---\n\n` +
    `You are ${myName}. Decide if you should respond. ` +
    `If the message isn't really directed at you or another agent already handled it well, ` +
    `respond with exactly: [SKIP]\n` +
    `Otherwise reply naturally as yourself.`
  );
}
