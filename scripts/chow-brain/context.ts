import fs from 'node:fs';
import path from 'node:path';
import { getBrainContextSnippet } from '../../src/chow-brain.js';

const BOT_ROOT = process.cwd();
const MEMORY_ROOT = path.join(BOT_ROOT, 'memory');

function arg(name: string, fallback?: string): string | undefined {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return fallback;
}

function read(p: string): string {
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8').trim() : '';
}

const chatId = arg('--chat', process.env.CHAT_ID || '-1003665370879')!;
const days = Number(arg('--days', '3'));

const brainDir = path.join(MEMORY_ROOT, String(chatId), 'second-brain');
const dailyDir = path.join(brainDir, 'daily');

const soul = read(path.join(brainDir, 'SOUL.md'));
const user = read(path.join(brainDir, 'USER.md'));
const memory = read(path.join(brainDir, 'MEMORY.md'));

let dailySection = '';
if (fs.existsSync(dailyDir)) {
  const files = fs.readdirSync(dailyDir)
    .filter((f) => f.endsWith('.md'))
    .sort()
    .slice(-Math.max(1, days));
  const blocks = files.map((f) => `### ${f}\n\n${read(path.join(dailyDir, f))}`);
  dailySection = blocks.join('\n\n---\n\n');
}

const structured = getBrainContextSnippet(chatId, { eventLimit: 8, consolidationCount: 1 });

const bundle = `# Chow Context Bundle\n\n${soul ? soul : '# SOUL.md\n(missing)'}\n\n---\n\n${user ? user : '# USER.md\n(missing)'}\n\n---\n\n${memory ? memory : '# MEMORY.md\n(missing)'}\n\n---\n\n## Recent Daily Logs\n\n${dailySection || '(none)'}\n\n---\n\n${structured}\n`;

const outPath = path.join(brainDir, 'context.md');
fs.writeFileSync(outPath, bundle, 'utf8');

console.log(`[brain] wrote context bundle: ${outPath}`);
