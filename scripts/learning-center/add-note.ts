import path from "node:path";
import { appendNdjson, makeId, nowIso, parseArgs } from "./utils.ts";

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const track = args.track ?? "general";
  const type = args.type ?? "insight";
  const text = args.text;
  const sourceUrl = args.sourceUrl ?? "";
  const author = args.author ?? "chow";
  const tags = (args.tags ?? "")
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  if (!text) {
    console.error("Usage: npm run learn:add-note -- --track <track> --type <type> --text \"...\" [--sourceUrl <url>] [--tags a,b] [--author chow|adam|agent]");
    process.exit(1);
  }

  const payload = {
    id: makeId("note"),
    capturedAt: nowIso(),
    track,
    type,
    text,
    sourceUrl,
    tags,
    author,
  };

  const file = path.resolve("learning-center/data/notes.ndjson");
  await appendNdjson(file, payload);
  console.log(`✅ note added (${type})`);
}

main().catch((err) => {
  console.error("add-note failed", err);
  process.exit(1);
});
