// Contract harness: imports the REAL BDW provider module
// (backend/ai-gateway/src/providers/bdw.ts) and exercises it against a live
// shim, exactly as the Next.js application does at runtime.
//
// usage: node bdw_provider_contract.mjs <bdw.ts> <baseUrl> <apiKey>
// Prints one JSON line: {valid, health, content, error}
import { pathToFileURL } from "node:url";

const [, , tsPath, baseUrl, apiKey] = process.argv;
if (!tsPath || !baseUrl || !apiKey) {
  console.error("usage: node bdw_provider_contract.mjs <bdw.ts> <baseUrl> <apiKey>");
  process.exit(2);
}

process.env.BDW_AI_ENABLED = "true";
process.env.BDW_AI_BASE_URL = baseUrl;
process.env.BDW_AI_MODEL = "bdw-career-ai";
process.env.BDW_AI_API_KEY = apiKey;
// CI runs against the deterministic fake gateway at 15 s. Staging (§10.2)
// raises the provider timeout for CPU/vLLM generation without changing the
// provider module itself.
process.env.BDW_AI_TIMEOUT_MS = process.env.P5_CONTRACT_TIMEOUT_MS || "15000";

const mod = await import(pathToFileURL(tsPath).href);
const config = mod.loadBDWConfig();
const result = {
  valid: mod.isBDWConfigValid(config),
  health: await mod.healthCheck(config),
  content: null,
  error: null,
};
try {
  result.content = await mod.callBDWEndpoint(
    config,
    "What is setup time in a flip flop?",
    "You are BDW, a deep-tech career assistant."
  );
} catch (err) {
  result.error = String((err && err.message) || err);
}
console.log(JSON.stringify(result));
