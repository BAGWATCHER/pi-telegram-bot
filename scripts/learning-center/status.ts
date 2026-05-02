import path from "node:path";
import { readNdjson } from "./utils.ts";

type Source = { track?: string; capturedAt?: string; title?: string; type?: string };
type Note = { track?: string; capturedAt?: string; type?: string; text?: string };

function topTracks(items: Array<{ track?: string }>): Array<[string, number]> {
  const counts = new Map<string, number>();
  for (const item of items) {
    const key = item.track ?? "unknown";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

async function main() {
  const sources = await readNdjson<Source>(path.resolve("learning-center/data/sources.ndjson"));
  const notes = await readNdjson<Note>(path.resolve("learning-center/data/notes.ndjson"));

  console.log("\n=== Learning Center Status ===");
  console.log(`Sources: ${sources.length}`);
  console.log(`Notes:   ${notes.length}`);

  console.log("\nTracks (sources):");
  for (const [track, count] of topTracks(sources)) {
    console.log(`- ${track}: ${count}`);
  }

  console.log("\nTracks (notes):");
  for (const [track, count] of topTracks(notes)) {
    console.log(`- ${track}: ${count}`);
  }

  const latestSource = [...sources].sort((a, b) => new Date(b.capturedAt ?? 0).getTime() - new Date(a.capturedAt ?? 0).getTime())[0];
  const latestNote = [...notes].sort((a, b) => new Date(b.capturedAt ?? 0).getTime() - new Date(a.capturedAt ?? 0).getTime())[0];

  console.log("\nLatest source:");
  if (latestSource) {
    console.log(`- [${latestSource.track}] ${latestSource.title} (${latestSource.type}) @ ${latestSource.capturedAt}`);
  } else {
    console.log("- none");
  }

  console.log("\nLatest note:");
  if (latestNote) {
    console.log(`- [${latestNote.track}] ${latestNote.type}: ${latestNote.text} @ ${latestNote.capturedAt}`);
  } else {
    console.log("- none");
  }
}

main().catch((err) => {
  console.error("status failed", err);
  process.exit(1);
});
