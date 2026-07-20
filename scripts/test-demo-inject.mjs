#!/usr/bin/env node
/** Quick smoke test for browser mp4 inject logic (run from repo root). */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { injectMetadata, parseMetadata } from "../docs/assets/js/mp4.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixture = path.join(__dirname, "../data/testsrc_320x240_h264.mp4");
const out = path.join(__dirname, "../test_output/demo_inject.mp4");

const source = new Uint8Array(fs.readFileSync(fixture));
const before = parseMetadata(source);
console.log("Before:", before.v1, before.v2);

const output = injectMetadata(source, {
  v1: true,
  v2: true,
  stereo: "left-right",
  bounds: [0, 0, 0, 0],
});

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, output);

const after = parseMetadata(output);
console.log("After v1:", after.v1);
console.log("After v2 stereo:", after.v2.stereo);
console.log("Wrote", out, `(${output.length} bytes)`);

if (!after.v1?.Spherical || after.v1.Spherical !== "true") {
  process.exit(1);
}
if (after.v2.stereo !== "left-right") {
  process.exit(1);
}
console.log("OK");
