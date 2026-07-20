#!/usr/bin/env node
/** Quick smoke test for browser mp4 inject logic (run from web/). */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { injectMetadata, parseMetadata } from "./assets/js/mp4.js";
import {
  buildSa3dContents,
  getSpatialAudioMetadata,
  parseSa3d,
} from "./assets/js/metadata.js";

const webDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(webDir, "..");
const fixture = path.join(root, "tests/fixtures/h264.mp4");
const fixture4ch = path.join(root, "tests/fixtures/h264-4ch.mp4");
const out = path.join(root, "tests/output/demo_inject.mp4");
const outAudio = path.join(root, "tests/output/demo_inject_audio.mp4");

function testSa3dRoundtrip() {
  const meta = getSpatialAudioMetadata(1, false);
  const body = buildSa3dContents(meta, 4);
  const parsed = parseSa3d(body);
  if (parsed.ambisonicOrder !== 1 || parsed.numChannels !== 4) {
    throw new Error("SA3D roundtrip failed");
  }
  console.log("SA3D roundtrip OK");
}

function testVideoInject() {
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
    throw new Error("v1 inject failed");
  }
  if (after.v2.stereo !== "left-right") {
    throw new Error("v2 inject failed");
  }
  console.log("Video inject OK");
}

function testSpatialAudioInject() {
  if (!fs.existsSync(fixture4ch)) {
    console.log("Skip 4ch inject test: tests/fixtures/h264-4ch.mp4 not found");
    return;
  }

  const source = new Uint8Array(fs.readFileSync(fixture4ch));
  const before = parseMetadata(source);
  console.log("4ch before:", before.numAudioChannels, before.spatialAudioSupported);

  if (!before.spatialAudioSupported) {
    throw new Error("4ch fixture is not a supported spatial audio layout");
  }

  const output = injectMetadata(source, {
    v1: false,
    v2: false,
    spatialAudio: true,
  });

  fs.writeFileSync(outAudio, output);
  const after = parseMetadata(output);
  console.log("4ch after SA3D:", after.audio);

  if (!after.audio || after.audio.ambisonicOrder !== 1) {
    throw new Error("SA3D inject failed");
  }
  console.log("Spatial audio inject OK");
}

testSa3dRoundtrip();
testVideoInject();
testSpatialAudioInject();
console.log("OK");
