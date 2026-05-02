import fs from "node:fs";

type Project = {
  id: string;
  name: string;
  path: string;
  riskLevel: "low" | "medium" | "high";
  commands: Record<string, string>;
  gates?: {
    requireEvalPass?: boolean;
    requireHumanApprovalForDeploy?: boolean;
  };
};

type Manifest = {
  version: number;
  updatedAt: string;
  projects: Project[];
};

const manifestPath = "/home/ubuntu/pi-telegram-bot/factory/projects.manifest.json";

if (!fs.existsSync(manifestPath)) {
  console.error(`manifest missing: ${manifestPath}`);
  process.exit(1);
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8")) as Manifest;

console.log(`Factory manifest v${manifest.version} (${manifest.updatedAt})`);
console.log(`Projects: ${manifest.projects.length}`);
console.log("");

for (const p of manifest.projects) {
  const gates = p.gates ?? {};
  console.log(`- ${p.id} :: ${p.name}`);
  console.log(`  path: ${p.path}`);
  console.log(`  risk: ${p.riskLevel}`);
  console.log(`  build: ${p.commands.build ?? "n/a"}`);
  console.log(`  eval: ${p.commands.eval ?? "n/a"}`);
  console.log(`  deploy: ${p.commands.deploy ?? "n/a"}`);
  console.log(`  gate.evalPass: ${gates.requireEvalPass ? "required" : "optional"}`);
  console.log(`  gate.humanApprovalDeploy: ${gates.requireHumanApprovalForDeploy ? "required" : "optional"}`);
  console.log("");
}
