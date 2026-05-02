import { CHOW_PRIMARY_CHAT_ID, consolidateBrainDay, forceDailyBrainConsolidation } from "../../src/chow-brain.js";

function arg(name: string, fallback?: string): string | undefined {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return fallback;
}

function hasFlag(name: string): boolean {
  return process.argv.includes(name);
}

const chatId = arg("--chat", process.env.CHAT_ID || CHOW_PRIMARY_CHAT_ID)!;
const date = arg("--date");
const reason = arg("--reason", "cli");
const force = hasFlag("--force");

if (force && !date) {
  const out = forceDailyBrainConsolidation(chatId, reason);
  console.log(`[brain] force consolidated ${out.date}`);
  console.log(`[brain] events: ${out.eventCount}`);
  console.log(`[brain] file: ${out.path}`);
  process.exit(0);
}

const out = consolidateBrainDay(chatId, {
  date: date || undefined,
  reason,
  includeEventLog: !!force,
});

console.log(`[brain] consolidated ${out.date}`);
console.log(`[brain] events: ${out.eventCount}`);
console.log(`[brain] file: ${out.path}`);
