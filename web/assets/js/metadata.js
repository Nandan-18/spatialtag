/**
 * Spherical video v1 XML metadata generation and parsing.
 * Mirrors cli/metadata.py constants.
 */

export const SPHERICAL_UUID_BYTES = new Uint8Array([
  0xff, 0xcc, 0x82, 0x63, 0xf8, 0x55, 0x4a, 0x93, 0x88, 0x14, 0x58, 0x7a, 0x02, 0x52, 0x1f, 0xdd,
]);

const SPHERICAL_NS = "http://ns.google.com/videos/1.0/spherical/";

const SPHERICAL_XML_HEADER =
  '<?xml version="1.0"?>' +
  "<rdf:SphericalVideo\n" +
  'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n' +
  'xmlns:GSpherical="http://ns.google.com/videos/1.0/spherical/">';

const SPHERICAL_XML_CORE =
  "<GSpherical:Spherical>true</GSpherical:Spherical>" +
  "<GSpherical:Stitched>true</GSpherical:Stitched>" +
  "<GSpherical:StitchingSoftware>Spherical Metadata Tool</GSpherical:StitchingSoftware>" +
  "<GSpherical:ProjectionType>equirectangular</GSpherical:ProjectionType>";

const SPHERICAL_XML_FOOTER = "</rdf:SphericalVideo>";

const STEREO_FRAGMENTS = {
  "top-bottom": "<GSpherical:StereoMode>top-bottom</GSpherical:StereoMode>",
  "left-right": "<GSpherical:StereoMode>left-right</GSpherical:StereoMode>",
};

const CROP_REGEX = /^(\d+):(\d+):(\d+):(\d+):(\d+):(\d+)$/;

export function generateSphericalXml({ stereo = null, crop = null } = {}) {
  let xml = SPHERICAL_XML_HEADER + SPHERICAL_XML_CORE;
  if (stereo && STEREO_FRAGMENTS[stereo]) {
    xml += STEREO_FRAGMENTS[stereo];
  }
  if (crop) {
    const match = crop.match(CROP_REGEX);
    if (!match) {
      throw new Error(`Invalid crop params: ${crop}`);
    }
    const [, w, h, fw, fh, x, y] = match;
    xml +=
      `<GSpherical:CroppedAreaImageWidthPixels>${w}</GSpherical:CroppedAreaImageWidthPixels>` +
      `<GSpherical:CroppedAreaImageHeightPixels>${h}</GSpherical:CroppedAreaImageHeightPixels>` +
      `<GSpherical:FullPanoWidthPixels>${fw}</GSpherical:FullPanoWidthPixels>` +
      `<GSpherical:FullPanoHeightPixels>${fh}</GSpherical:FullPanoHeightPixels>` +
      `<GSpherical:CroppedAreaLeftPixels>${x}</GSpherical:CroppedAreaLeftPixels>` +
      `<GSpherical:CroppedAreaTopPixels>${y}</GSpherical:CroppedAreaTopPixels>`;
  }
  xml += SPHERICAL_XML_FOOTER;
  return xml;
}

export function parseSphericalXml(xmlText) {
  if (typeof DOMParser !== "undefined") {
    const parser = new DOMParser();
    let doc = parser.parseFromString(xmlText, "application/xml");
    if (doc.querySelector("parsererror")) {
      const idx = xmlText.indexOf("<rdf:SphericalVideo");
      if (idx !== -1) {
        const patched =
          xmlText.slice(0, idx + "<rdf:SphericalVideo".length) +
          ' xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"' +
          xmlText.slice(idx + "<rdf:SphericalVideo".length);
        doc = parser.parseFromString(patched, "application/xml");
      }
    }
    if (!doc.querySelector("parsererror")) {
      const fields = {};
      const tagNames = [
        "Spherical",
        "Stitched",
        "StitchingSoftware",
        "ProjectionType",
        "StereoMode",
        "CroppedAreaImageWidthPixels",
        "CroppedAreaImageHeightPixels",
        "FullPanoWidthPixels",
        "FullPanoHeightPixels",
        "CroppedAreaLeftPixels",
        "CroppedAreaTopPixels",
      ];
      for (const name of tagNames) {
        const el =
          doc.getElementsByTagNameNS(SPHERICAL_NS, name)[0] ||
          doc.getElementsByTagName(`GSpherical:${name}`)[0];
        if (el?.textContent) fields[name] = el.textContent;
      }
      return fields;
    }
  }

  const fields = {};
  const re = /<GSpherical:(\w+)>([^<]*)<\/GSpherical:\1>/g;
  for (const match of xmlText.matchAll(re)) {
    fields[match[1]] = match[2];
  }
  return Object.keys(fields).length ? fields : null;
}

export function computeVr180Settings(width, height) {
  if (width < 2 || height < 1) {
    throw new Error(`Invalid video dimensions: ${width}x${height}`);
  }
  const eyeW = Math.floor(width / 2);
  const eyeH = height;
  return {
    stereo: "left-right",
    crop: `${eyeW}:${eyeH}:${eyeW * 2}:${eyeH}:${Math.floor(eyeW / 2)}:0`,
    bounds: [0, 0, 0x40000000, 0x40000000],
    summary: `${width}x${height} SBS → eye ${eyeW}x${eyeH}`,
  };
}

export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function stereoLabel(mode) {
  if (mode === 1) return "top-bottom";
  if (mode === 2) return "left-right";
  return "mono";
}

// --- Spatial audio (SA3D) --- mirrors cli/metadata.py ---

const MAX_SUPPORTED_AMBIX_ORDER = 1;

const AMBISONIC_TYPE_NAMES = { 0: "periphonic" };
const AMBISONIC_ORDERING_NAMES = { 0: "ACN" };
const AMBISONIC_NORMALIZATION_NAMES = { 0: "SN3D" };

function readU32Local(bytes, offset) {
  return (
    (bytes[offset] << 24) |
    (bytes[offset + 1] << 16) |
    (bytes[offset + 2] << 8) |
    bytes[offset + 3]
  ) >>> 0;
}

function writeU32Local(bytes, offset, value) {
  bytes[offset] = (value >>> 24) & 0xff;
  bytes[offset + 1] = (value >>> 16) & 0xff;
  bytes[offset + 2] = (value >>> 8) & 0xff;
  bytes[offset + 3] = value & 0xff;
}

export function getExpectedNumAudioChannels(ambisonicType, order, headLockedStereo) {
  const headLocked = headLockedStereo ? 2 : 0;
  if (ambisonicType === "periphonic") {
    return (order + 1) ** 2 + headLocked;
  }
  return -1;
}

export function getSpatialAudioDescription(numChannels) {
  for (let order = 1; order <= MAX_SUPPORTED_AMBIX_ORDER; order++) {
    if ((order + 1) ** 2 === numChannels) {
      return { order, isSupported: true, hasHeadLockedStereo: false };
    }
    if ((order + 1) ** 2 + 2 === numChannels) {
      return { order, isSupported: true, hasHeadLockedStereo: true };
    }
  }
  return { order: -1, isSupported: false, hasHeadLockedStereo: false };
}

export function getSpatialAudioMetadata(order, headLockedStereo) {
  const numChannels = getExpectedNumAudioChannels("periphonic", order, headLockedStereo);
  return {
    ambisonic_type: "periphonic",
    ambisonic_order: order,
    head_locked_stereo: headLockedStereo,
    ambisonic_channel_ordering: "ACN",
    ambisonic_normalization: "SN3D",
    channel_map: Array.from({ length: numChannels }, (_, i) => i),
  };
}

export function parseSa3d(contents, source, contentStart = 0) {
  const bytes = contents ?? source.slice(contentStart, contentStart + 256);
  if (!bytes || bytes.length < 12) return null;

  const version = bytes[0];
  const typeByte = bytes[1];
  const headLockedStereo = (typeByte & 0x80) !== 0;
  const ambisonicType = typeByte & 0x7f;
  const ambisonicOrder = readU32Local(bytes, 2);
  const channelOrdering = bytes[6];
  const normalization = bytes[7];
  const numChannels = readU32Local(bytes, 8);
  const channelMap = [];
  for (let i = 0; i < numChannels; i++) {
    channelMap.push(readU32Local(bytes, 12 + i * 4));
  }

  return {
    version,
    ambisonicType,
    typeName: AMBISONIC_TYPE_NAMES[ambisonicType] ?? String(ambisonicType),
    headLockedStereo,
    ambisonicOrder,
    channelOrdering,
    orderingName: AMBISONIC_ORDERING_NAMES[channelOrdering] ?? String(channelOrdering),
    normalization,
    normalizationName: AMBISONIC_NORMALIZATION_NAMES[normalization] ?? String(normalization),
    numChannels,
    channelMap,
  };
}

export function formatSa3dSummary(sa3d) {
  if (!sa3d) return "none";
  return (
    `${sa3d.normalizationName}, ${sa3d.orderingName}, ${sa3d.typeName}, ` +
    `Order ${sa3d.ambisonicOrder}, ${sa3d.numChannels} channel(s), ` +
    `Map: [${sa3d.channelMap.join(", ")}]`
  );
}

export function buildSa3dContents(metadata, numChannels) {
  const body = new Uint8Array(12 + numChannels * 4);
  body[0] = 0; // version
  let typeByte = 0; // periphonic
  if (metadata.head_locked_stereo) typeByte |= 0x80;
  body[1] = typeByte;
  writeU32Local(body, 2, metadata.ambisonic_order);
  body[6] = 0; // ACN
  body[7] = 0; // SN3D
  writeU32Local(body, 8, numChannels);
  for (let i = 0; i < numChannels; i++) {
    writeU32Local(body, 12 + i * 4, metadata.channel_map[i] ?? i);
  }
  return body;
}
