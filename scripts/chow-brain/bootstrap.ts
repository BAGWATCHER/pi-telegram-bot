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

function writeIfMissing(file: string, content: string) {
  if (fs.existsSync(file)) return;
  fs.writeFileSync(file, content.trim() + '\n', 'utf8');
}

const chatId = arg('--chat', process.env.CHAT_ID || '-1003665370879')!;
const chatMemoryDir = path.join(MEMORY_ROOT, String(chatId));
const brainDir = path.join(chatMemoryDir, 'second-brain');
const dailyDir = path.join(brainDir, 'daily');
const logsDir = path.join(brainDir, 'logs');

ensureDir(brainDir);
ensureDir(dailyDir);
ensureDir(logsDir);

const today = new Date().toISOString().slice(0, 10);

writeIfMissing(
  path.join(brainDir, 'SOUL.md'),
  `# SOUL.md\n\n## Identity\n- Name: Mr Chow\n- Role: Server-side AI coding/research operator\n- Scope: Chow-only (do not repoint Jose)\n\n## Operating Values\n- Be direct, fast, and action-oriented\n- Prefer safe additive changes in shared repos\n- Keep memory updated when new facts appear\n- Verify with commands/tests before claiming done\n\n## Guardrails\n- Never rename/repoint Jose when fixing Chow\n- Prioritize BearingBrain agent-side work unless user overrides\n- Keep responses professional and low-hype\n\n## Runtime\n- Host: /home/ubuntu\n- Main bot project: /home/ubuntu/pi-telegram-bot\n- This second-brain folder is Chow-only and additive\n`
);

writeIfMissing(
  path.join(brainDir, 'USER.md'),
  `# USER.md\n\n## User\n- Name/display: adam\n- Style preference: concise, direct confirmations, immediate action links\n- Priority lane: BearingBrain checkout + merchant distribution + agent discoverability\n\n## Project Preferences\n- Keep Chow focused on agent-side infrastructure and delivery\n- Keep Jose separate\n- When systems are unstable (e.g., Mac crashes), prioritize rapid extraction/migration\n\n## Communication\n- Avoid hype and fluffy language\n- Confirm what was done and what remains\n`
);

writeIfMissing(
  path.join(brainDir, 'MEMORY.md'),
  `# MEMORY.md\n\n## Purpose\nLong-lived operational memory for Chow, inspired by Cole-style second-brain architecture.\n\n## Current Focus\n- BearingBrain external API/MCP discoverability and developer onboarding\n- Azure migration lane for Rico runtime\n- Chow bot reliability and memory continuity\n\n## Notes\n- Primary identity source remains: memory/${chatId}/identity.md\n- Summaries source remains: memory/${chatId}/summaries.md\n- Use reflect script to sync structured brain files from protected identity\n`
);

writeIfMissing(
  path.join(dailyDir, `${today}.md`),
  `# Daily Log — ${today}\n\n- Initialized Chow second-brain scaffold.\n- Next: run reflection sync from identity.md + summaries.md.\n`
);

writeIfMissing(
  path.join(brainDir, 'README.md'),
  `# Chow Second Brain (Cole-style, adapted)\n\nThis is an additive, Chow-only memory layer inspired by Cole's setup.\n\n## Files\n- SOUL.md: operating identity and guardrails\n- USER.md: user preferences and collaboration constraints\n- MEMORY.md: long-lived distilled state\n- daily/YYYY-MM-DD.md: rolling operational logs\n\n## Commands\n- Bootstrap: \`npm run brain:bootstrap\`\n- Reflect sync: \`npm run brain:reflect\`\n- Build context: \`npm run brain:context\`\n\n## Safety\n- Does not modify Jose settings\n- Does not replace protected identity.md; it derives/syncs from it\n`
);

console.log(`[brain] bootstrap complete for chat ${chatId}`);
console.log(`[brain] path: ${brainDir}`);
