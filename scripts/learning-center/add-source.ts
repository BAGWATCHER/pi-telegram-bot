import path from "node:path";
import { appendNdjson, makeId, nowIso, parseArgs } from "./utils.ts";

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const track = args.track ?? "general";
  const type = args.type ?? "article";
  const title = args.title;
  const url = args.url;
  const notes = args.notes ?? "";

  if (!title || !url) {
    console.error("Usage: npm run learn:add-source -- --track <track> --type <type> --title \"...\" --url \"...\" [--notes \"...\"]");
    process.exit(1);
  }

  const payload = {
    id: makeId("src"),
    capturedAt: nowIso(),
    track,
    type,
    title,
    url,
    notes,
  };

  const file = path.resolve("learning-center/data/sources.ndjson");
  await appendNdjson(file, payload);
  console.log(`✅ source added: ${title}`);
}

main().catch((err) => {
  console.error("add-source failed", err);
  process.exit(1);
});
