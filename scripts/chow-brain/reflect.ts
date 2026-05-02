import fs from 'node:fs';
import path from 'node:path';

const BOT_ROOT = process.cwd();
const MEMORY_ROOT = path.join(BOT_ROOT, 'memory');

function arg(name: string, fallback?: string): string | undefined {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return fallback;
}

function ensureDir(p: string) {
  fs.mkdirSync(p, { recursive: true });
}

function readIfExists(p: string): string {
  if (!fs.existsSync(p)) return '';
  return fs.readFileSync(p, 'utf8');
}

function sectionFromMarkdown(md: string, heading: string): string {
  const header = `## ${heading}`;
  const start = md.indexOf(header);
  if (start < 0) return '';

  const bodyStart = md.indexOf('\n', start);
  if (bodyStart < 0) return '';

  const nextHeader = md.indexOf('\n## ', bodyStart + 1);
  const bodyEnd = nextHeader >= 0 ? nextHeader : md.length;
  return md.slice(bodyStart + 1, bodyEnd).trim();
}

const chatId = arg('--chat', process.env.CHAT_ID || '-1003665370879')!;
const note = arg('--note', 'Reflection sync completed.');

const chatMemoryDir = path.join(MEMORY_ROOT, String(chatId));
const identityPath = path.join(chatMemoryDir, 'identity.md');
const summariesPath = path.join(chatMemoryDir, 'summaries.md');

const brainDir = path.join(chatMemoryDir, 'second-brain');
const dailyDir = path.join(brainDir, 'daily');
ensureDir(brainDir);
ensureDir(dailyDir);

const identity = readIfExists(identityPath);
const summaries = readIfExists(summariesPath);

if (!identity.trim()) {
  console.error(`[brain] missing identity at ${identityPath}`);
  process.exit(1);
}

const userPrefs = sectionFromMarkdown(identity, 'User preferences');
const projects = sectionFromMarkdown(identity, 'Projects');
const server = sectionFromMarkdown(identity, 'Server');

const nowIso = new Date().toISOString();
const today = nowIso.slice(0, 10);

const soul = `# SOUL.md

## Identity
- Name: Mr Chow
- Mode: Server-side operator + coding/research assistant
- Scope: Chow-only implementation

## Non-Negotiables
- Protect identity continuity and operational memory
- Keep actions verifiable and reversible when possible
- Keep Jose isolated unless explicitly requested

## Current Runtime Snapshot
${server ? server : '- Server section unavailable in identity snapshot'}

## Last Reflected
- ${nowIso}
`;

const user = `# USER.md

## Preferences Snapshot
${userPrefs ? userPrefs : '- User preference section unavailable in identity snapshot'}

## Last Reflected
- ${nowIso}
`;

const memory = `# MEMORY.md

## Source of Truth
- Protected identity: ${identityPath}
- Rolling summaries: ${summariesPath}

## Projects Snapshot
${projects ? projects : '- Projects section unavailable in identity snapshot'}

## Recent Summary Window
${summaries.trim() ? summaries.trim() : '- No summaries yet'}

## Last Reflected
- ${nowIso}
`;

fs.writeFileSync(path.join(brainDir, 'SOUL.md'), soul.trim() + '\n', 'utf8');
fs.writeFileSync(path.join(brainDir, 'USER.md'), user.trim() + '\n', 'utf8');
fs.writeFileSync(path.join(brainDir, 'MEMORY.md'), memory.trim() + '\n', 'utf8');

const dailyPath = path.join(dailyDir, `${today}.md`);
const dailyEntry = `\n## ${nowIso}\n- ${note}\n- Synced SOUL.md / USER.md / MEMORY.md from identity + summaries.\n`;
if (!fs.existsSync(dailyPath)) {
  fs.writeFileSync(dailyPath, `# Daily Log — ${today}\n${dailyEntry}`, 'utf8');
} else {
  fs.appendFileSync(dailyPath, dailyEntry, 'utf8');
}

console.log('[brain] reflection sync complete');
console.log(`[brain] updated: ${path.join(brainDir, 'SOUL.md')}`);
console.log(`[brain] updated: ${path.join(brainDir, 'USER.md')}`);
console.log(`[brain] updated: ${path.join(brainDir, 'MEMORY.md')}`);
console.log(`[brain] daily log: ${dailyPath}`);
