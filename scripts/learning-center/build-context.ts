import path from "node:path";
import { writeFile } from "node:fs/promises";
import { parseArgs, readNdjson } from "./utils.ts";

type Source = {
  id: string;
  capturedAt: string;
  track: string;
  type: string;
  title: string;
  url: string;
  notes?: string;
};

type Note = {
  id: string;
  capturedAt: string;
  track: string;
  type: string;
  text: string;
  sourceUrl?: string;
  tags?: string[];
  author?: string;
};

function sortDescByDate<T extends { capturedAt?: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const da = new Date(a.capturedAt ?? 0).getTime();
    const db = new Date(b.capturedAt ?? 0).getTime();
    return db - da;
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const track = args.track ?? "gauntlet-ai";

  const sourcesPath = path.resolve("learning-center/data/sources.ndjson");
  const notesPath = path.resolve("learning-center/data/notes.ndjson");

  const allSources = await readNdjson<Source>(sourcesPath);
  const allNotes = await readNdjson<Note>(notesPath);

  const sources = sortDescByDate(allSources.filter((s) => s.track === track));
  const notes = sortDescByDate(allNotes.filter((n) => n.track === track));

  const insightNotes = notes.filter((n) => n.type === "insight").slice(0, 10);
  const decisionNotes = notes.filter((n) => n.type === "decision").slice(0, 10);
  const drillNotes = notes.filter((n) => n.type === "drill").slice(0, 10);
  const openQuestions = notes.filter((n) => n.type === "question").slice(0, 10);

  const sourceRows = sources.slice(0, 25).map((s) => `- [${s.title}](${s.url}) — ${s.type}${s.notes ? `; ${s.notes}` : ""}`);

  const noteRows = (arr: Note[]) =>
    arr.map((n) => `- ${n.text}${n.sourceUrl ? ` ([source](${n.sourceUrl}))` : ""}`);

  const content = [
    `# Context Bundle: ${track}`,
    "",
    `Generated: ${new Date().toISOString()}`,
    "",
    "## Snapshot",
    `- Sources: ${sources.length}`,
    `- Notes: ${notes.length}`,
    "",
    "## Recent Sources",
    ...(sourceRows.length ? sourceRows : ["- none"]),
    "",
    "## Core Insights",
    ...(noteRows(insightNotes).length ? noteRows(insightNotes) : ["- none"]),
    "",
    "## Decisions",
    ...(noteRows(decisionNotes).length ? noteRows(decisionNotes) : ["- none"]),
    "",
    "## Drills",
    ...(noteRows(drillNotes).length ? noteRows(drillNotes) : ["- none"]),
    "",
    "## Open Questions",
    ...(noteRows(openQuestions).length ? noteRows(openQuestions) : ["- none"]),
    "",
  ].join("\n");

  const outPath = path.resolve(`learning-center/tracks/${track}/context.md`);
  await writeFile(outPath, content, "utf8");

  console.log(`✅ context built: ${outPath}`);
}

main().catch((err) => {
  console.error("build-context failed", err);
  process.exit(1);
});
