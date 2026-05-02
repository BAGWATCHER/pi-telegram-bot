import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

export type Dict = Record<string, string>;

export function parseArgs(argv: string[]): Dict {
  const out: Dict = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      out[key] = "true";
      continue;
    }
    out[key] = next;
    i += 1;
  }
  return out;
}

export async function ensureDirForFile(filePath: string): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
}

export async function appendNdjson(filePath: string, payload: unknown): Promise<void> {
  await ensureDirForFile(filePath);
  let existing = "";
  try {
    existing = await readFile(filePath, "utf8");
  } catch {
    existing = "";
  }
  const line = JSON.stringify(payload);
  const next = existing.trim().length > 0 ? `${existing.trimEnd()}\n${line}\n` : `${line}\n`;
  await writeFile(filePath, next, "utf8");
}

export async function readNdjson<T = Record<string, unknown>>(filePath: string): Promise<T[]> {
  try {
    const raw = await readFile(filePath, "utf8");
    return raw
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line) as T);
  } catch {
    return [];
  }
}

export function nowIso(): string {
  return new Date().toISOString();
}

export function makeId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
