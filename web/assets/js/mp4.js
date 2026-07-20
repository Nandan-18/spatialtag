/**
 * Minimal MP4/MOV box loader and metadata injector for browser use.
 * Ported from spatial/mpeg for GitHub Pages demo scope.
 */

import {
  SPHERICAL_UUID_BYTES,
  buildSa3dContents,
  generateSphericalXml,
  getExpectedNumAudioChannels,
  getSpatialAudioDescription,
  getSpatialAudioMetadata,
  parseSa3d,
  parseSphericalXml,
  stereoLabel,
} from "./metadata.js";

const SOUND_SAMPLES = new Set([
  "NONE",
  "raw ",
  "twos",
  "sowt",
  "fl32",
  "fl64",
  "in24",
  "in32",
  "ulaw",
  "alaw",
  "lpcm",
  "mp4a",
  "Opus",
]);

const VIDEO_SAMPLES = new Set([
  "NONE",
  "avc1",
  "vp09",
  "av01",
  "hev1",
  "hvc1",
  "dvh1",
  "apcn",
  "apch",
  "apcs",
  "apco",
  "ap4h",
  "ap4x",
]);

const CONTAINERS = new Set([
  "moov",
  "trak",
  "mdia",
  "minf",
  "stbl",
  "stsd",
  "udta",
  "wave",
  "sv3d",
  "proj",
  ...SOUND_SAMPLES,
  ...VIDEO_SAMPLES,
]);

function fourCC(bytes, offset = 0) {
  return String.fromCharCode(bytes[offset], bytes[offset + 1], bytes[offset + 2], bytes[offset + 3]);
}

function readU32(source, offset) {
  return (
    (source[offset] << 24) |
    (source[offset + 1] << 16) |
    (source[offset + 2] << 8) |
    source[offset + 3]
  ) >>> 0;
}

function readU16(source, offset) {
  return (source[offset] << 8) | source[offset + 1];
}

function readU64(source, offset) {
  const hi = BigInt(readU32(source, offset));
  const lo = BigInt(readU32(source, offset + 4));
  return (hi << 32n) + lo;
}

function writeU32(arr, offset, value) {
  arr[offset] = (value >>> 24) & 0xff;
  arr[offset + 1] = (value >>> 16) & 0xff;
  arr[offset + 2] = (value >>> 8) & 0xff;
  arr[offset + 3] = value & 0xff;
}

function writeU64(arr, offset, value) {
  const big = BigInt(value);
  writeU32(arr, offset, Number((big >> 32n) & 0xffffffffn));
  writeU32(arr, offset + 4, Number(big & 0xffffffffn));
}

function writeFourCC(arr, offset, name) {
  for (let i = 0; i < 4; i++) {
    arr[offset + i] = name.charCodeAt(i);
  }
}

function concatChunks(chunks) {
  const total = chunks.reduce((sum, c) => sum + c.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.length;
  }
  return out;
}

class LeafBox {
  constructor(name, position, headerSize, contentSize) {
    this.name = name;
    this.position = position;
    this.headerSize = headerSize;
    this.contentSize = contentSize;
    this.contents = null;
  }

  size() {
    return this.headerSize + this.contentSize;
  }

  contentStart() {
    return this.position + this.headerSize;
  }

  resize() {}

  save(source, outChunks, delta) {
    outChunks.push(this.encodeHeader(this.size()));
    const start = this.contentStart();
    if (this.name === "stco") {
      outChunks.push(copyStco(source, this, delta));
    } else if (this.name === "co64") {
      outChunks.push(copyCo64(source, this, delta));
    } else if (this.contents) {
      outChunks.push(this.contents);
    } else {
      outChunks.push(source.slice(start, start + this.contentSize));
    }
  }

  encodeHeader(size) {
    const header = new Uint8Array(this.headerSize);
    if (this.headerSize === 16) {
      writeU32(header, 0, 1);
      writeFourCC(header, 4, this.name);
      writeU64(header, 8, size);
    } else {
      writeU32(header, 0, size);
      writeFourCC(header, 4, this.name);
    }
    return header;
  }
}

class ContainerBox extends LeafBox {
  constructor(name, position, headerSize, contentSize, padding = 0) {
    super(name, position, headerSize, contentSize);
    this.padding = padding;
    this.contents = [];
  }

  resize() {
    this.contentSize = this.padding;
    for (const child of this.contents) {
      child.resize();
      this.contentSize += child.size();
    }
  }

  remove(tag) {
    this.contents = this.contents.filter((child) => {
      if (child.name === tag) return false;
      if (child instanceof ContainerBox) child.remove(tag);
      return true;
    });
    this.resize();
  }

  add(child) {
    this.contents.push(child);
    this.resize();
  }

  save(source, outChunks, delta) {
    outChunks.push(this.encodeHeader(this.size()));
    if (this.padding > 0) {
      const start = this.contentStart();
      outChunks.push(source.slice(start, start + this.padding));
    }
    for (const child of this.contents) {
      child.save(source, outChunks, delta);
    }
  }
}

function copyIndex(source, box, delta, entryBytes, readFn, writeFn) {
  const start = box.contentStart();
  const versionFlags = readU32(source, start);
  const count = readU32(source, start + 4);
  const chunks = [new Uint8Array(8)];
  writeU32(chunks[0], 0, versionFlags);
  writeU32(chunks[0], 4, count);
  let pos = start + 8;
  const bigDelta = BigInt(delta);
  for (let i = 0; i < count; i++) {
    const entry = new Uint8Array(entryBytes);
    const raw = readFn(source, pos);
    const value = typeof raw === "bigint" ? raw + bigDelta : raw + delta;
    if (typeof value === "number" && !Number.isSafeInteger(value)) {
      throw new Error("Chunk offset exceeds JavaScript safe integer range");
    }
    writeFn(entry, 0, value);
    chunks.push(entry);
    pos += entryBytes;
  }
  return concatChunks(chunks);
}

function copyStco(source, box, delta) {
  return copyIndex(
    source,
    box,
    delta,
    4,
    readU32,
    (arr, off, val) => writeU32(arr, off, val),
  );
}

function copyCo64(source, box, delta) {
  return copyIndex(
    source,
    box,
    delta,
    8,
    readU64,
    (arr, off, val) => writeU64(arr, off, val),
  );
}

function containerPadding(name, source, contentStart) {
  if (name === "stsd") return 8;
  if (SOUND_SAMPLES.has(name)) {
    const version = readU16(source, contentStart + 8);
    if (version === 0) return 28;
    if (version === 1) return 44;
    if (version === 2) return 64;
    return 28;
  }
  if (VIDEO_SAMPLES.has(name)) return 78;
  return 0;
}

function loadBox(source, position, end) {
  let headerSize = 8;
  let size = readU32(source, position);
  let name = fourCC(source, position + 4);

  let isLeaf = !CONTAINERS.has(name);
  if (name === "mp4a" && size === 12) isLeaf = true;

  if (size === 1) {
    size = Number(readU64(source, position + 8));
    headerSize = 16;
  }
  if (size < 8 || position + size > end) {
    throw new Error(`Invalid box ${name} at ${position}`);
  }

  const contentSize = size - headerSize;
  if (isLeaf) {
    const box = new LeafBox(name, position, headerSize, contentSize);
    if (name === "uuid" || name === "SA3D" || name === "esds") {
      const start = box.contentStart();
      box.contents = source.slice(start, start + contentSize);
    }
    return box;
  }

  const padding = containerPadding(name, source, position + headerSize);
  const container = new ContainerBox(name, position, headerSize, contentSize, padding);
  const innerStart = position + headerSize + padding;
  const innerEnd = position + size;
  let cursor = innerStart;
  while (cursor + 8 <= innerEnd) {
    const child = loadBox(source, cursor, innerEnd);
    container.contents.push(child);
    cursor = child.position + child.size();
  }
  return container;
}

function loadTopLevel(source) {
  const end = source.byteLength;
  const boxes = [];
  let pos = 0;
  while (pos + 8 <= end) {
    const box = loadBox(source, pos, end);
    boxes.push(box);
    pos = box.position + box.size();
  }
  return boxes;
}

function bytesEqual(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

function isVideoTrack(source, trak) {
  for (const child of trak.contents) {
    if (child.name !== "mdia") continue;
    for (const mdiaChild of child.contents) {
      if (mdiaChild.name !== "hdlr") continue;
      const handler = fourCC(source, mdiaChild.contentStart() + 8);
      if (handler === "vide") return true;
    }
  }
  return false;
}

function isAudioTrack(source, trak) {
  for (const child of trak.contents) {
    if (child.name !== "mdia") continue;
    for (const mdiaChild of child.contents) {
      if (mdiaChild.name !== "hdlr") continue;
      const handler = fourCC(source, mdiaChild.contentStart() + 8);
      if (handler === "soun") return true;
    }
  }
  return false;
}

function readDescriptorLength(source, offset) {
  let length = 0;
  let pos = offset;
  for (let i = 0; i < 4; i++) {
    const sizeByte = source[pos++];
    length = (length << 7) | (sizeByte & 0x7f);
    if ((sizeByte & 0x80) === 0) break;
  }
  return { length, pos };
}

function getAacNumChannels(sampleBox, source) {
  const walkBox = (box) => {
    if (box.name === "esds") {
      const start = box.contentStart() + 4;
      if (source[start] !== 0x03) return -1;
      let pos = start + 1;
      pos = readDescriptorLength(source, pos).pos;
      pos += 3;
      if (source[pos] !== 0x04) return -1;
      pos += 1;
      pos = readDescriptorLength(source, pos).pos;
      pos += 13;
      if (source[pos] !== 0x05) return -1;
      pos += 1;
      pos = readDescriptorLength(source, pos).pos;
      const descriptor = (source[pos] << 8) | source[pos + 1];
      return (descriptor & 0x78) >> 3;
    }
    if (box instanceof ContainerBox) {
      for (const child of box.contents) {
        const channels = walkBox(child);
        if (channels > 0) return channels;
      }
    }
    return -1;
  };
  return walkBox(sampleBox);
}

function getSampleDescriptionNumChannels(sampleBox, source) {
  const start = sampleBox.contentStart() + 8;
  const version = readU16(source, start);
  if (version === 0) {
    return readU16(source, start + 8);
  }
  if (version === 1) {
    return readU16(source, start + 8);
  }
  if (version === 2) {
    return readU32(source, start + 32);
  }
  return -1;
}

function getNumAudioChannels(stsd, source) {
  for (const sample of stsd.contents) {
    if (sample.name === "mp4a") {
      const aac = getAacNumChannels(sample, source);
      if (aac > 0) return aac;
      return getSampleDescriptionNumChannels(sample, source);
    }
    if (SOUND_SAMPLES.has(sample.name)) {
      return getSampleDescriptionNumChannels(sample, source);
    }
  }
  return 0;
}

function countAudioTracks(source, moov) {
  let count = 0;
  for (const trak of moov.contents) {
    if (trak.name === "trak" && isAudioTrack(source, trak)) count += 1;
  }
  return count;
}

function findAudioSampleDescription(source, moov) {
  for (const trak of moov.contents) {
    if (trak.name !== "trak" || !isAudioTrack(source, trak)) continue;
    for (const mdia of trak.contents) {
      if (mdia.name !== "mdia") continue;
      for (const minf of mdia.contents) {
        if (minf.name !== "minf") continue;
        for (const stbl of minf.contents) {
          if (stbl.name !== "stbl") continue;
          for (const stsd of stbl.contents) {
            if (stsd.name !== "stsd") continue;
            for (const sample of stsd.contents) {
              if (sample.name === "mp4a" || SOUND_SAMPLES.has(sample.name)) {
                return { stsd, sample, channels: getNumAudioChannels(stsd, source) };
              }
            }
          }
        }
      }
    }
  }
  return null;
}

function createSa3dBox(metadata, numChannels) {
  const body = buildSa3dContents(metadata, numChannels);
  const box = new LeafBox("SA3D", 0, 8, body.length);
  box.contents = body;
  return box;
}

function readTkhdDimensions(source, trak) {
  for (const child of trak.contents) {
    if (child.name !== "tkhd") continue;
    const offset = child.position + child.size() - 8;
    const widthFixed = readU32(source, offset);
    const heightFixed = readU32(source, offset + 4);
    return [Math.floor(widthFixed / 65536), Math.floor(heightFixed / 65536)];
  }
  return null;
}

function createUuidBox(xmlText) {
  const payload = new TextEncoder().encode(xmlText);
  const contents = new Uint8Array(SPHERICAL_UUID_BYTES.length + payload.length);
  contents.set(SPHERICAL_UUID_BYTES, 0);
  contents.set(payload, SPHERICAL_UUID_BYTES.length);
  const box = new LeafBox("uuid", 0, 8, contents.length);
  box.contents = contents;
  return box;
}

function createSt3dBox(stereoMode) {
  const modeMap = { "top-bottom": 1, "left-right": 2 };
  const body = new Uint8Array(5);
  writeU32(body, 0, 0);
  body[4] = modeMap[stereoMode] ?? 0;
  const box = new LeafBox("st3d", 0, 8, 5);
  box.contents = body;
  return box;
}

function createSvhdBox() {
  const text = new TextEncoder().encode("SpatialTag\0");
  const body = new Uint8Array(4 + text.length);
  writeU32(body, 0, 0);
  body.set(text, 4);
  const box = new LeafBox("svhd", 0, 8, body.length);
  box.contents = body;
  return box;
}

function createPrhdBox() {
  const body = new Uint8Array(16);
  writeU32(body, 0, 0);
  const box = new LeafBox("prhd", 0, 8, 16);
  box.contents = body;
  return box;
}

function createEquiBox(bounds) {
  const body = new Uint8Array(20);
  writeU32(body, 0, 0);
  writeU32(body, 4, bounds[0] ?? 0);
  writeU32(body, 8, bounds[1] ?? 0);
  writeU32(body, 12, bounds[2] ?? 0);
  writeU32(body, 16, bounds[3] ?? 0);
  const box = new LeafBox("equi", 0, 8, 20);
  box.contents = body;
  return box;
}

function createSv3dBox(bounds) {
  const sv3d = new ContainerBox("sv3d", 0, 8, 0, 0);
  sv3d.add(createSvhdBox());
  const proj = new ContainerBox("proj", 0, 8, 0, 0);
  proj.add(createPrhdBox());
  proj.add(createEquiBox(bounds));
  sv3d.add(proj);
  sv3d.resize();
  return sv3d;
}

function injectV1(moov, source, xmlText) {
  let added = false;
  for (const trak of moov.contents) {
    if (trak.name !== "trak" || !isVideoTrack(source, trak)) continue;
    trak.remove("uuid");
    trak.add(createUuidBox(xmlText));
    added = true;
  }
  return added;
}

function injectSpatialAudio(moov, source, audioMetadata) {
  const audio = findAudioSampleDescription(source, moov);
  if (!audio) throw new Error("No audio track found for spatial audio metadata.");

  const expected = getExpectedNumAudioChannels(
    audioMetadata.ambisonic_type,
    audioMetadata.ambisonic_order,
    audioMetadata.head_locked_stereo,
  );
  if (audio.channels !== expected) {
    const hls = audioMetadata.head_locked_stereo ? " with head-locked stereo" : "";
    throw new Error(
      `Found ${audio.channels} audio channel(s). Expected ${expected} for ` +
        `${audioMetadata.ambisonic_type} ambisonics of order ${audioMetadata.ambisonic_order}${hls}.`,
    );
  }

  audio.sample.remove("SA3D");
  audio.sample.add(createSa3dBox(audioMetadata, audio.channels));
  return true;
}

function injectV2(moov, source, stereoMode, bounds) {
  for (const trak of moov.contents) {
    if (trak.name !== "trak" || !isVideoTrack(source, trak)) continue;
    for (const mdia of trak.contents) {
      if (mdia.name !== "mdia") continue;
      for (const minf of mdia.contents) {
        if (minf.name !== "minf") continue;
        for (const stbl of minf.contents) {
          if (stbl.name !== "stbl") continue;
          for (const stsd of stbl.contents) {
            if (stsd.name !== "stsd") continue;
            for (const sample of stsd.contents) {
              if (!VIDEO_SAMPLES.has(sample.name)) continue;
              sample.remove("st3d");
              sample.remove("sv3d");
              if (stereoMode) sample.add(createSt3dBox(stereoMode));
              sample.add(createSv3dBox(bounds));
              return true;
            }
          }
        }
      }
    }
  }
  return false;
}

function clearV2(moov) {
  for (const trak of moov.contents) {
    if (trak.name !== "trak") continue;
    walk(trak, (box) => {
      if (box.name === "stsd") {
        for (const sample of box.contents) {
          if (VIDEO_SAMPLES.has(sample.name)) {
            sample.remove("st3d");
            sample.remove("sv3d");
          }
        }
      }
    });
  }
}

function walk(box, fn) {
  fn(box);
  if (box instanceof ContainerBox) {
    for (const child of box.contents) walk(child, fn);
  }
}

function findMoov(boxes) {
  return boxes.find((b) => b.name === "moov") ?? null;
}

function layoutSummary(boxes) {
  return boxes.map((b) => ({
    name: b.name,
    size: b.size(),
    percent: b.size() / boxes.reduce((s, x) => s + x.size(), 0),
  }));
}

function parseMetadata(source) {
  const boxes = loadTopLevel(source);
  const moov = findMoov(boxes);
  if (!moov) throw new Error("No moov box found.");

  const result = {
    layout: layoutSummary(boxes),
    moovLast: boxes[boxes.length - 1]?.name === "moov",
    tracks: [],
    dimensions: null,
    v1: null,
    v2: { stereo: null, bounds: null },
    audio: null,
    numAudioChannels: 0,
    numAudioTracks: countAudioTracks(source, moov),
    spatialAudioSupported: false,
  };

  let trackNum = 0;
  for (const trak of moov.contents) {
    if (trak.name !== "trak") continue;
    const track = {
      id: trackNum++,
      video: isVideoTrack(source, trak),
      audio: isAudioTrack(source, trak),
      v1: null,
      v2: {},
      sa3d: null,
    };
    if (track.video) {
      result.dimensions = readTkhdDimensions(source, trak);
    }
    for (const child of trak.contents) {
      if (child.name === "uuid" && child.contents) {
        if (bytesEqual(child.contents.slice(0, 16), SPHERICAL_UUID_BYTES)) {
          const xml = new TextDecoder().decode(child.contents.slice(16));
          track.v1 = parseSphericalXml(xml);
          result.v1 = track.v1;
        }
      }
      if (child.name === "mdia") {
        walk(child, (box) => {
          if (box.name === "st3d") {
            const start = box.contentStart();
            const mode = box.contents ? box.contents[4] : source[start + 4];
            track.v2.stereo = stereoLabel(mode);
            result.v2.stereo = track.v2.stereo;
          }
          if (box.name === "equi") {
            const start = box.contentStart();
            const read = (off) => (box.contents ? readU32(box.contents, off) : readU32(source, start + off));
            track.v2.bounds = [read(4), read(8), read(12), read(16)];
            result.v2.bounds = track.v2.bounds;
          }
          if (box.name === "SA3D") {
            const sa3d = parseSa3d(box.contents, source, box.contentStart());
            track.sa3d = sa3d;
            result.audio = sa3d;
          }
        });
      }
    }
    result.tracks.push(track);
  }

  const audioInfo = findAudioSampleDescription(source, moov);
  if (audioInfo) {
    result.numAudioChannels = audioInfo.channels;
    const desc = getSpatialAudioDescription(audioInfo.channels);
    result.spatialAudioSupported = desc.isSupported;
    result.spatialAudioDescription = desc;
  }

  return result;
}

function mdatDelta(boxes, moov, firstMdatPos) {
  moov.resize();
  let newPos = 0;
  for (const box of boxes) {
    if (box.name === "mdat") {
      newPos += box.headerSize;
      break;
    }
    newPos += box.size();
  }
  return newPos - firstMdatPos;
}

function saveBoxes(source, boxes) {
  const mdatBox = boxes.find((b) => b.name === "mdat");
  const moov = findMoov(boxes);
  if (!mdatBox || !moov) throw new Error("Missing mdat or moov.");

  const firstMdatPos = mdatBox.position + mdatBox.headerSize;
  const delta = mdatDelta(boxes, moov, firstMdatPos);
  const chunks = [];
  for (const box of boxes) {
    box.save(source, chunks, delta);
  }
  return concatChunks(chunks);
}

export function injectMetadata(source, options) {
  const boxes = loadTopLevel(source);
  const moov = findMoov(boxes);
  if (!moov) throw new Error("No moov box found.");

  const useV1 = options.v1 !== false;
  const useV2 = Boolean(options.v2);

  if (useV1 && !useV2) clearV2(moov);
  if (useV2 && !useV1) moov.remove("uuid");

  if (useV1) {
    const xml = options.xml ?? generateSphericalXml({ stereo: options.stereo, crop: options.crop });
    if (!injectV1(moov, source, xml)) {
      throw new Error("No video track found for v1 metadata.");
    }
  }

  if (useV2) {
    if (!injectV2(moov, source, options.stereo, options.bounds ?? [0, 0, 0, 0])) {
      throw new Error("No video sample description found for v2 metadata.");
    }
  }

  if (options.spatialAudio) {
    if (countAudioTracks(source, moov) > 1) {
      throw new Error("Expected 1 audio track. Multiple audio tracks are not supported.");
    }
    const parsed = parseMetadata(source);
    const desc = parsed.spatialAudioDescription;
    if (!desc?.isSupported) {
      throw new Error(
        parsed.numAudioChannels
          ? `Audio has ${parsed.numAudioChannels} channel(s) and is not a supported spatial audio format.`
          : "No compatible audio track found for spatial audio metadata.",
      );
    }
    const audioMetadata = getSpatialAudioMetadata(desc.order, desc.hasHeadLockedStereo);
    if (!injectSpatialAudio(moov, source, audioMetadata)) {
      throw new Error("Failed to inject spatial audio metadata.");
    }
  }

  moov.resize();
  return saveBoxes(source, boxes);
}

export { parseMetadata, loadTopLevel, formatLayoutName };

function formatLayoutName(name) {
  const labels = { ftyp: "File type", mdat: "Media data", moov: "Metadata", free: "Free space" };
  return labels[name] ?? name;
}
