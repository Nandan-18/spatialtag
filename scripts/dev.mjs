#!/usr/bin/env node
/**
 * Local dev server: build site/, serve on :8888, rebuild on source changes.
 *
 * Usage: pnpm dev
 *        npm run dev
 */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import chokidar from "chokidar";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = process.env.PORT ?? "8888";

function runBuild() {
  return new Promise((resolve, reject) => {
    const child = spawn("python3", ["scripts/build_pages_site.py", "--output", "site"], {
      cwd: root,
      stdio: "inherit",
    });
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`site build failed (exit ${code})`));
    });
  });
}

function startServer() {
  const bin = path.join(root, "node_modules", ".bin", "serve");
  const child = spawn(bin, ["site", "-l", port, "--no-port-switching"], {
    cwd: root,
    stdio: "inherit",
  });
  child.on("error", (err) => {
    console.error(err);
    console.error("\nRun pnpm install first.\n");
    process.exit(1);
  });
  return child;
}

const watchGlobs = [
  path.join(root, "docs"),
  path.join(root, "scripts", "build_pages_site.py"),
  path.join(root, "README.md"),
  path.join(root, "spatialmedia", "README.md"),
  path.join(root, "docker", "README.md"),
  path.join(root, "spatial-audio", "README.md"),
];

let rebuildTimer;
let rebuilding = false;

function scheduleRebuild(label) {
  clearTimeout(rebuildTimer);
  rebuildTimer = setTimeout(async () => {
    if (rebuilding) return;
    rebuilding = true;
    console.log(`\nRebuilding (${label})…`);
    try {
      await runBuild();
      console.log("Rebuild complete. Refresh the browser.\n");
    } catch (err) {
      console.error(err.message);
    } finally {
      rebuilding = false;
    }
  }, 400);
}

console.log("Building site…");
await runBuild();

const server = startServer();
console.log(`\n  Local preview: http://localhost:${port}\n  Watching for changes. Press Ctrl+C to stop.\n`);

chokidar
  .watch(watchGlobs, { ignoreInitial: true, awaitWriteFinish: { stabilityThreshold: 200 } })
  .on("all", (_event, filePath) => scheduleRebuild(path.basename(filePath)));

const shutdown = () => {
  server.kill("SIGTERM");
  process.exit(0);
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
