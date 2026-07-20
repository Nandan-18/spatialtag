/**
 * Spherical video v1 XML metadata generation and parsing.
 * Mirrors spatialmedia/metadata_utils.py constants.
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
