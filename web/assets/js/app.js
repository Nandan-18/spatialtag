import { injectMetadata, parseMetadata } from "./mp4.js";
import {
  computeVr180Settings,
  formatBytes,
  formatSa3dSummary,
  generateSphericalXml,
} from "./metadata.js";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const state = { file: null, buffer: null, metadata: null, busy: false };

const LAYOUT_LABELS = {
  ftyp: "File type",
  mdat: "Media data",
  moov: "Metadata",
  free: "Free space",
};

function setStatus(message, tone = "neutral") {
  const el = $("#status");
  if (!el) return;
  el.textContent = message;
  el.dataset.tone = tone;
}

function setWorkflowStep(step) {
  const steps = { load: 1, inspect: 2, inject: 3 };
  const active = steps[step] ?? 1;
  $$(".demo-rail-step").forEach((el) => {
    const n = steps[el.dataset.step] ?? 0;
    el.classList.toggle("is-active", n === active);
    el.classList.toggle("is-done", n < active);
  });
}

function setLoadProgress(visible, text = "Reading file…") {
  const bar = $("#load-progress");
  const label = $("#load-progress-text");
  if (bar) bar.classList.toggle("hidden", !visible);
  if (label) label.textContent = text;
}

function setBusy(busy) {
  state.busy = busy;
  const btn = $("#inject-btn");
  const zone = $("#drop-zone");
  const spinner = $(".inject-btn-spinner");
  if (btn) btn.disabled = busy || !state.file;
  if (zone) zone.classList.toggle("disabled", busy);
  if (spinner) spinner.classList.toggle("hidden", !busy);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function metaGroup(title, chipClass, chipText, rows) {
  const group = document.createElement("div");
  group.className = "meta-group";
  const rowsHtml = rows
    .map(
      ([label, value, valueClass = ""]) =>
        `<div class="meta-row"><span class="meta-row-label">${escapeHtml(label)}</span>` +
        `<span class="meta-row-value ${escapeHtml(valueClass)}">${escapeHtml(value)}</span></div>`,
    )
    .join("");
  group.innerHTML =
    `<div class="meta-group-head">` +
    `<h4 class="meta-group-title">${escapeHtml(title)}</h4>` +
    (chipText
      ? `<span class="meta-chip ${escapeHtml(chipClass)}">${escapeHtml(chipText)}</span>`
      : "") +
    `</div><div class="meta-rows">${rowsHtml}</div>`;
  return group;
}

function renderLayout(layout) {
  const bar = $("#layout-bar");
  if (!bar) return;
  bar.innerHTML = "";
  const total = layout.reduce((sum, item) => sum + item.size, 0) || 1;

  for (const item of layout) {
    const name = item.name.trim();
    const seg = document.createElement("div");
    seg.className = `layout-seg layout-${name}`;
    seg.style.flexGrow = item.size;
    seg.title = `${LAYOUT_LABELS[name] ?? name} · ${formatBytes(item.size)} · ${((item.size / total) * 100).toFixed(1)}%`;
    const label = document.createElement("span");
    label.textContent = name;
    seg.appendChild(label);
    bar.appendChild(seg);
  }

  const legend = $("#layout-legend");
  if (!legend) return;
  legend.innerHTML = layout
    .map((item) => {
      const name = item.name.trim();
      const pct = ((item.size / total) * 100).toFixed(1);
      const label = LAYOUT_LABELS[name] ?? name;
      return `<span><i class="dot layout-${escapeHtml(name)}"></i>${escapeHtml(label)} ${escapeHtml(formatBytes(item.size))} (${pct}%)</span>`;
    })
    .join("");
}

function updateMoovBadge(moovLast) {
  const badge = $("#moov-badge");
  if (!badge) return;
  if (moovLast) {
    badge.textContent = "moov after mdat";
    badge.className = "moov-badge is-good";
    badge.title = "Typical streaming layout; metadata sits at the end of the file.";
  } else {
    badge.textContent = "moov before mdat";
    badge.className = "moov-badge is-warn";
    badge.title = "Metadata appears before media data in this file.";
  }
}

function updateMetaStatus(meta) {
  const status = $("#meta-status");
  if (!status) return;
  const hasV1 = Boolean(meta?.v1);
  const hasV2 = Boolean(meta?.v2?.stereo || meta?.v2?.bounds);
  const hasAudio = Boolean(meta?.audio);
  const parts = [];
  if (hasV1 || hasV2) {
    parts.push(hasV1 && hasV2 ? "video v1+v2" : hasV1 ? "video v1" : "video v2");
  }
  if (hasAudio) parts.push("SA3D");
  if (parts.length) {
    status.textContent = parts.join(" + ");
    status.className = "meta-status meta-status-found";
  } else if (meta?.numAudioChannels) {
    status.textContent = `${meta.numAudioChannels}ch audio, no tags`;
    status.className = "meta-status meta-status-none";
  } else {
    status.textContent = "No immersive tags";
    status.className = "meta-status meta-status-none";
  }
}

function updateSpatialAudioControl(meta) {
  const toggle = $("#spatial-audio");
  const card = $("#spatial-audio-card");
  const hint = $("#spatial-audio-hint");
  if (!toggle || !card) return;

  const supported = Boolean(meta?.spatialAudioSupported);
  toggle.disabled = !supported;
  card.classList.toggle("is-disabled", !supported);

  if (!meta) {
    toggle.checked = false;
    if (hint) hint.textContent = "Requires compatible ambiX ACN/SN3D track";
    return;
  }

  if (meta.audio) toggle.checked = true;
  else toggle.checked = supported;

  if (hint) {
    if (supported) {
      const desc = meta.spatialAudioDescription;
      hint.textContent = desc.hasHeadLockedStereo
        ? `${meta.numAudioChannels} channels (ambiX + head-locked stereo)`
        : `${meta.numAudioChannels} channels (first-order ambiX)`;
    } else if (meta.numAudioChannels) {
      hint.textContent = `${meta.numAudioChannels} channel(s): not a supported ambiX layout`;
    } else {
      hint.textContent = "No audio track detected";
    }
  }
}

function renderMetadata(meta) {
  const panel = $("#metadata-panel");
  const tags = $("#metadata-tags");
  if (!panel || !tags) return;
  tags.innerHTML = "";

  if (!meta) {
    panel.classList.add("empty");
    updateMetaStatus(null);
    return;
  }

  panel.classList.remove("empty");
  updateMetaStatus(meta);

  const fileRows = [];
  if (meta.dimensions) {
    fileRows.push(["Resolution", `${meta.dimensions[0]}×${meta.dimensions[1]}`]);
  }
  fileRows.push([
    "moov position",
    meta.moovLast ? "after mdat" : "before mdat",
    meta.moovLast ? "is-good" : "",
  ]);
  tags.appendChild(metaGroup("File", "", "", fileRows));

  if (meta.v1) {
    const v1Rows = Object.entries(meta.v1).map(([key, value]) => [key, value]);
    tags.appendChild(metaGroup("Spherical v1", "meta-chip-v1", "XML", v1Rows));
  } else {
    tags.appendChild(
      metaGroup("Spherical v1", "meta-chip-warn", "missing", [["Status", "No v1 XML in file"]]),
    );
  }

  const v2Rows = [];
  if (meta.v2.stereo) v2Rows.push(["ST3D stereo", meta.v2.stereo]);
  if (meta.v2.bounds) {
    v2Rows.push(["SV3D bounds", meta.v2.bounds.map((b) => `0x${b.toString(16)}`).join(", ")]);
  }
  if (v2Rows.length) {
    tags.appendChild(metaGroup("Spherical v2", "meta-chip-v2", "atoms", v2Rows));
  } else {
    tags.appendChild(
      metaGroup("Spherical v2", "meta-chip-warn", "missing", [["Status", "No ST3D / SV3D atoms"]]),
    );
  }

  const audioRows = [];
  if (meta.numAudioChannels) {
    audioRows.push(["Audio channels", String(meta.numAudioChannels)]);
  }
  if (meta.numAudioTracks > 1) {
    audioRows.push(["Audio tracks", String(meta.numAudioTracks), ""]);
  }
  if (meta.audio) {
    audioRows.push(["Summary", formatSa3dSummary(meta.audio)]);
    audioRows.push(["Ambisonic order", String(meta.audio.ambisonicOrder)]);
    audioRows.push(["Normalization", meta.audio.normalizationName]);
    audioRows.push(["Channel ordering", meta.audio.orderingName]);
    if (meta.audio.headLockedStereo) {
      audioRows.push(["Head-locked stereo", "yes", "is-good"]);
    }
    tags.appendChild(metaGroup("Spatial audio", "meta-chip-audio", "SA3D", audioRows));
  } else if (meta.numAudioChannels) {
    audioRows.push([
      "Status",
      meta.spatialAudioSupported ? "Supported layout, no SA3D yet" : "Unsupported channel layout",
    ]);
    tags.appendChild(
      metaGroup("Spatial audio", "meta-chip-warn", "missing", audioRows),
    );
  } else {
    tags.appendChild(
      metaGroup("Spatial audio", "meta-chip-warn", "n/a", [["Status", "No audio track in file"]]),
    );
  }

  updateSpatialAudioControl(meta);
}

function stereoLabel(mode) {
  if (mode === "left-right") return "side-by-side";
  if (mode === "top-bottom") return "over-under";
  return "mono";
}

function updateInjectPreview() {
  const list = $("#inject-preview-list");
  if (!list) return;

  const vr180 = $("#vr180")?.checked ?? false;
  const useV2 = ($("#use-v2")?.checked ?? true) || vr180;
  const stereo = $("#stereo-mode")?.value ?? "left-right";
  const items = [];

  if (vr180) {
    items.push("VR180 forward view (180°)");
    if (state.metadata?.dimensions) {
      const [w, h] = state.metadata.dimensions;
      const vr = computeVr180Settings(w, h);
      items.push(`Auto crop: ${vr.crop}`);
      items.push(`Bounds: 0x40000000 per eye`);
    }
  } else {
    items.push("Equirectangular 360° projection");
    items.push(`Stereo: ${stereoLabel(stereo)}`);
  }

  if (useV2) {
    items.push("v2 <code>SV3D</code> / <code>ST3D</code> atoms");
  }
  items.push("v1 spherical XML in UUID box");

  if ($("#spatial-audio")?.checked) {
    items.push("Spatial audio <code>SA3D</code> atom (ACN/SN3D)");
  }

  list.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
}

function resetWorkspace() {
  state.file = null;
  state.buffer = null;
  state.metadata = null;
  $("#workspace")?.classList.add("hidden");
  $("#replace-file")?.classList.add("hidden");
  $("#controls")?.classList.add("is-disabled");
  $("#metadata-panel")?.classList.add("empty");
  $("#metadata-tags").innerHTML = "";
  $("#results")?.classList.add("hidden");
  $("#file-input").value = "";
  const saToggle = $("#spatial-audio");
  if (saToggle) {
    saToggle.checked = false;
    saToggle.disabled = true;
  }
  $("#spatial-audio-card")?.classList.add("is-disabled");
  updateMetaStatus(null);
  setWorkflowStep("load");
  setStatus("Choose a file to begin.");
  updateInjectPreview();
}

async function handleFile(file) {
  if (!file || state.busy) return;
  if (!/\.(mp4|mov)$/i.test(file.name)) {
    setStatus("Please choose an MP4 or MOV file.", "error");
    return;
  }

  const maxBytes = 2 * 1024 * 1024 * 1024;
  if (file.size > maxBytes) {
    setStatus(
      `File is too large for the browser demo (${formatBytes(file.size)}). Use the SpatialTag CLI for files over 2 GB.`,
      "error",
    );
    return;
  }

  setBusy(true);
  setLoadProgress(true, "Reading file…");
  setStatus("Reading file…");

  try {
    const buffer = new Uint8Array(await file.arrayBuffer());
    setLoadProgress(true, "Parsing container…");
    const metadata = parseMetadata(buffer);
    state.file = file;
    state.buffer = buffer;
    state.metadata = metadata;

    const ext = file.name.split(".").pop()?.toUpperCase() ?? "MP4";
    const nameEl = $("#file-name");
    const sizeEl = $("#file-size");
    const badgeEl = $("#file-badge");
    if (nameEl) nameEl.textContent = file.name;
    if (sizeEl) sizeEl.textContent = formatBytes(file.size);
    if (badgeEl) badgeEl.textContent = ext;

    $("#workspace")?.classList.remove("hidden");
    $("#replace-file")?.classList.remove("hidden");
    $("#controls")?.classList.remove("is-disabled");
    renderLayout(metadata.layout);
    updateMoovBadge(metadata.moovLast);
    renderMetadata(metadata);
    updateInjectPreview();
    setWorkflowStep("inspect");
    setStatus("Inspect tags below, then inject when ready.", "success");
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Could not parse file.", "error");
    setWorkflowStep("load");
  } finally {
    setLoadProgress(false);
    setBusy(false);
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function inject() {
  if (!state.buffer || state.busy) return;

  setBusy(true);
  setStatus("Injecting metadata…");

  try {
    const stereo = $("#stereo-mode")?.value ?? "left-right";
    const vr180 = $("#vr180")?.checked ?? false;
    const useV2 = ($("#use-v2")?.checked ?? true) || vr180;

    let stereoMode = stereo === "none" ? null : stereo;
    let crop = null;
    let bounds = [0, 0, 0, 0];
    let xml = null;

    if (vr180) {
      const dims = state.metadata?.dimensions;
      if (!dims) throw new Error("Could not read video dimensions for VR180.");
      const vr = computeVr180Settings(dims[0], dims[1]);
      stereoMode = vr.stereo;
      crop = vr.crop;
      bounds = vr.bounds;
      xml = generateSphericalXml({ stereo: stereoMode, crop });
    } else if (stereoMode) {
      xml = generateSphericalXml({ stereo: stereoMode });
    } else {
      xml = generateSphericalXml();
    }

    const output = injectMetadata(state.buffer, {
      v1: true,
      v2: useV2,
      xml,
      stereo: stereoMode,
      crop,
      bounds,
      spatialAudio: $("#spatial-audio")?.checked ?? false,
    });

    const outName = state.file.name.replace(/(\.[^.]+)?$/, "_spatial$1");
    downloadBlob(new Blob([output], { type: "application/octet-stream" }), outName);

    state.buffer = output;
    const updated = parseMetadata(output);
    state.metadata = updated;
    renderMetadata(updated);
    updateMoovBadge(updated.moovLast);

    setStatus(`Exported ${outName}`, "success");
    const results = $("#results");
    const resultName = $("#result-name");
    const resultSize = $("#result-size");
    if (resultName) resultName.textContent = outName;
    if (resultSize) resultSize.textContent = formatBytes(output.length);
    if (results) results.classList.remove("hidden");
    setWorkflowStep("inject");
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Inject failed.", "error");
  } finally {
    setBusy(false);
  }
}

function initDropZone() {
  const zone = $("#drop-zone");
  const input = $("#file-input");
  if (!zone || !input) return;

  zone.addEventListener("click", () => input.click());
  zone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      input.click();
    }
  });
  input.addEventListener("change", () => {
    if (input.files?.[0]) handleFile(input.files[0]);
  });

  ["dragenter", "dragover"].forEach((evt) => {
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.add("hover");
    });
  });
  ["dragleave", "drop"].forEach((evt) => {
    zone.addEventListener(evt, (e) => {
      e.preventDefault();
      zone.classList.remove("hover");
    });
  });
  zone.addEventListener("drop", (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) handleFile(file);
  });
}

function initControls() {
  $("#inject-btn")?.addEventListener("click", inject);
  $("#replace-file")?.addEventListener("click", resetWorkspace);

  $$(".seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if ($("#vr180")?.checked) return;
      $$(".seg-btn").forEach((b) => b.classList.remove("is-selected"));
      btn.classList.add("is-selected");
      const hidden = $("#stereo-mode");
      if (hidden) hidden.value = btn.dataset.stereo ?? "none";
      updateInjectPreview();
    });
  });

  $("#vr180")?.addEventListener("change", (e) => {
    const on = e.target.checked;
    $$(".seg-btn").forEach((b) => {
      b.disabled = on;
      b.style.opacity = on ? "0.45" : "1";
    });
    if (on) {
      const v2 = $("#use-v2");
      if (v2) v2.checked = true;
    }
    updateInjectPreview();
  });

  $("#use-v2")?.addEventListener("change", updateInjectPreview);
  $("#spatial-audio")?.addEventListener("change", updateInjectPreview);
}

initDropZone();
initControls();
updateInjectPreview();
setWorkflowStep("load");
