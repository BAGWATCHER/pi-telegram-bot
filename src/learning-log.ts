import * as fs from "node:fs";
import * as path from "node:path";

const BOT_ROOT = process.cwd();
const DATA_DIR = path.join(BOT_ROOT, "data");
const FEEDBACK_PATH = path.join(DATA_DIR, "chow-feedback.ndjson");
const MEMORY_PROMOTIONS_PATH = path.join(DATA_DIR, "memory-promotions.ndjson");
const CRAIGSLIST_LEARNING_PATH = path.join(
  BOT_ROOT,
  "factory",
  "projects",
  "energy-zillow",
  "data",
  "processed",
  "craigslist_learning_log.ndjson"
);

export interface ChowFeedbackLogEntry {
  ts?: string;
  chat_id: string;
  kind: "task" | "draft" | "research" | "memory";
  project?: string;
  user_request?: string;
  context_refs?: string[];
  chow_output?: string;
  final_output?: string;
  outcome?: "accepted" | "edited" | "rejected" | "sent" | "booked";
  quality?: "good" | "bad" | "mixed";
  reason_codes?: string[];
  notes?: string;
}

export interface MemoryPromotionLogEntry {
  ts?: string;
  chat_id: string;
  promoted_to: "identity" | "summary" | "second_brain";
  summary: string;
  source?: string;
}

export interface CraigslistLearningLogEntry {
  ts?: string;
  post_id: string;
  company?: string;
  role?: string;
  opportunity?: string;
  draft_id?: string;
  queue_id?: string;
  sent?: boolean;
  reply?: boolean;
  booked?: boolean;
}

function ensureParent(filePath: string): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function appendNdjson(filePath: string, row: Record<string, unknown>): void {
  try {
    ensureParent(filePath);
    fs.appendFileSync(filePath, JSON.stringify({ ts: new Date().toISOString(), ...row }) + "\n", "utf8");
  } catch (err) {
    console.warn(`[learning-log] failed to append ${filePath}:`, err);
  }
}

export function initializeLearningLogs(): void {
  for (const filePath of [FEEDBACK_PATH, MEMORY_PROMOTIONS_PATH, CRAIGSLIST_LEARNING_PATH]) {
    try {
      ensureParent(filePath);
      if (!fs.existsSync(filePath)) fs.writeFileSync(filePath, "", "utf8");
    } catch (err) {
      console.warn(`[learning-log] failed to initialize ${filePath}:`, err);
    }
  }
}

export function logChowFeedback(entry: ChowFeedbackLogEntry): void {
  appendNdjson(FEEDBACK_PATH, entry);
}

export function logMemoryPromotion(entry: MemoryPromotionLogEntry): void {
  appendNdjson(MEMORY_PROMOTIONS_PATH, entry);
}

export function logCraigslistLearning(entry: CraigslistLearningLogEntry): void {
  appendNdjson(CRAIGSLIST_LEARNING_PATH, entry);
}

initializeLearningLogs();
