import { AuthStorage, ModelRegistry } from "@mariozechner/pi-coding-agent";

async function run() {
  try {
    const auth = AuthStorage.create();
    const registry = new ModelRegistry(auth);
    const models = await registry.getAvailable();
    
    console.log("--- ALL MODELS ---");
    models.forEach(m => {
      console.log(`${m.provider}/${m.id}`);
    });
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

run();
