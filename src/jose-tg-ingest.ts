import 'dotenv/config';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions';
import { triageSnapshot, buildTriageState } from './jose-triage.js';

const RICO_ENV_PATH = process.env.RICO_ENV_PATH || '/home/ubuntu/trenchfeed-trader/.env';
const OUTPUT_PATH = process.env.JOSE_TG_SNAPSHOT_PATH || '/home/ubuntu/pi-telegram-bot/data/jose-telegram-snapshot.json';
const TRIAGE_STATE_PATH = process.env.JOSE_TG_TRIAGE_STATE_PATH || '/home/ubuntu/pi-telegram-bot/data/jose-telegram-triage-state.json';
const EVENTS_PATH = process.env.JOSE_TG_EVENTS_PATH || '/home/ubuntu/pi-telegram-bot/data/jose-telegram-events.ndjson';
const POLL_MS = Number(process.env.JOSE_TG_POLL_MS || 120000);
const DIALOG_LIMIT = Number(process.env.JOSE_TG_DIALOG_LIMIT || 200);
const MESSAGE_PREVIEW_DIALOGS = Number(process.env.JOSE_TG_PREVIEW_DIALOGS || 40);
const MESSAGE_PREVIEW_COUNT = Number(process.env.JOSE_TG_PREVIEW_COUNT || 2);
const MESSAGE_PREVIEW_FETCH_DIALOGS = Number(process.env.JOSE_TG_PREVIEW_FETCH_DIALOGS || 8);

function parseEnvFile(filePath: string): Record<string, string> {
  const out: Record<string, string> = {};
  if (!fs.existsSync(filePath)) return out;
  const content = fs.readFileSync(filePath, 'utf8');
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf('=');
    if (idx <= 0) continue;
    const key = trimmed.slice(0, idx).trim();
    const value = trimmed.slice(idx + 1).trim().replace(/^['"]|['"]$/g, '');
    out[key] = value;
  }
  return out;
}

function getConfig() {
  const env = parseEnvFile(RICO_ENV_PATH);
  const apiId = Number(env.TELEGRAM_API_ID || process.env.TELEGRAM_API_ID || 0);
  const apiHash = env.TELEGRAM_API_HASH || process.env.TELEGRAM_API_HASH || '';
  const session = env.TELEGRAM_SESSION || process.env.TELEGRAM_SESSION || '';
  if (!apiId || !apiHash || !session) {
    throw new Error('Missing Telegram credentials (API_ID/API_HASH/SESSION) from Rico env');
  }
  return { apiId, apiHash, session };
}

function loadPreviousSnapshot(): any | null {
  if (!fs.existsSync(OUTPUT_PATH)) return null;
  try {
    return JSON.parse(fs.readFileSync(OUTPUT_PATH, 'utf8')) as any;
  } catch {
    return null;
  }
}

function appendEvents(events: any[]) {
  if (!events.length) return;
  const lines = events.map((e) => JSON.stringify(e)).join('\n') + '\n';
  fs.appendFileSync(EVENTS_PATH, lines);
}

function buildDeltaEvents(prev: any | null, curr: any): any[] {
  const now = curr?.generatedAt || new Date().toISOString();
  const events: any[] = [];

  const prevMap = new Map<string, any>();
  for (const d of (prev?.dialogs ?? [])) prevMap.set(String(d?.id ?? ''), d);

  for (const d of (curr?.dialogs ?? [])) {
    const id = String(d?.id ?? '');
    if (!id) continue;
    const old = prevMap.get(id);
    const oldUnread = Number(old?.unreadCount ?? 0);
    const newUnread = Number(d?.unreadCount ?? 0);

    if (!old) {
      events.push({
        ts: now,
        type: 'dialog_seen',
        dialogId: id,
        title: d?.title || d?.username || id,
        unreadCount: newUnread,
      });
      continue;
    }

    if (newUnread !== oldUnread) {
      events.push({
        ts: now,
        type: 'unread_delta',
        dialogId: id,
        title: d?.title || d?.username || id,
        unreadBefore: oldUnread,
        unreadAfter: newUnread,
        delta: newUnread - oldUnread,
      });
    }
  }

  return events.slice(-500);
}

function normalizePreview(value: unknown): string {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

async function buildSnapshot(client: TelegramClient) {
  const dialogs = await client.getDialogs({ limit: DIALOG_LIMIT });
  const top = dialogs.slice(0, MESSAGE_PREVIEW_DIALOGS);

  const items: Array<any> = [];
  for (let i = 0; i < top.length; i++) {
    const d: any = top[i];
    const previews: string[] = [];

    const fromDialog = normalizePreview(d?.message?.message || d?.message?.text || '');
    if (fromDialog) previews.push(fromDialog);

    if (i < MESSAGE_PREVIEW_FETCH_DIALOGS && previews.length < MESSAGE_PREVIEW_COUNT) {
      try {
        const msgs = await client.getMessages(d.entity, { limit: MESSAGE_PREVIEW_COUNT });
        for (const m of msgs as any[]) {
          const text = normalizePreview(m?.message || m?.text || '');
          if (text && !previews.includes(text)) previews.push(text);
          if (previews.length >= MESSAGE_PREVIEW_COUNT) break;
        }
      } catch {
        // best-effort only
      }
    }

    items.push({
      id: String((d.entity as any)?.id ?? ''),
      title: d.title || '',
      unreadCount: d.unreadCount || 0,
      isChannel: !!d.isChannel,
      isGroup: !!d.isGroup,
      isUser: !!d.isUser,
      username: (d.entity as any)?.username || null,
      lastMessageAt: d.date
        ? new Date(typeof d.date === 'number' && d.date < 1e12 ? d.date * 1000 : d.date).toISOString()
        : null,
      previews: previews.slice(0, MESSAGE_PREVIEW_COUNT),
    });
  }

  const byUnread = [...items].sort((a, b) => (b.unreadCount || 0) - (a.unreadCount || 0));

  return {
    generatedAt: new Date().toISOString(),
    totals: {
      dialogsFetched: dialogs.length,
      groups: items.filter((x) => x.isGroup).length,
      channels: items.filter((x) => x.isChannel).length,
      users: items.filter((x) => x.isUser).length,
      unreadDialogs: items.filter((x) => (x.unreadCount || 0) > 0).length,
    },
    topUnread: byUnread.slice(0, 50),
    dialogs: items,
  };
}

async function run() {
  const { apiId, apiHash, session } = getConfig();
  const client = new TelegramClient(new StringSession(session), apiId, apiHash, {
    connectionRetries: 5,
  });

  await client.connect();
  console.log('[jose-ingest] connected using Rico Telegram session');

  const outputDir = path.dirname(OUTPUT_PATH);
  fs.mkdirSync(outputDir, { recursive: true });

  const tick = async () => {
    try {
      const previousSnapshot = loadPreviousSnapshot();
      const snapshot = await buildSnapshot(client);
      fs.writeFileSync(OUTPUT_PATH, JSON.stringify(snapshot, null, 2));

      const triaged = triageSnapshot(snapshot);
      const triageState = buildTriageState(snapshot, triaged);
      fs.writeFileSync(TRIAGE_STATE_PATH, JSON.stringify(triageState, null, 2));

      const deltaEvents = buildDeltaEvents(previousSnapshot, snapshot);
      appendEvents(deltaEvents);

      console.log(
        `[jose-ingest] snapshot updated: dialogs=${snapshot.totals.dialogsFetched} unreadDialogs=${snapshot.totals.unreadDialogs} mode=${triageState.loadMode} urgent=${triageState.totals.urgentItems} events=${deltaEvents.length}`
      );
    } catch (err: any) {
      console.error('[jose-ingest] snapshot failed:', err?.message || err);
    }
  };

  await tick();
  setInterval(tick, POLL_MS);
}

run().catch((err) => {
  console.error('[jose-ingest] fatal:', err?.message || err);
  process.exit(1);
});
