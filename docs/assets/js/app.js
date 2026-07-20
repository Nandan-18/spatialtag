import { injectMetadata, parseMetadata } from "./mp4.js";
import {
  computeVr180Settings,
  formatBytes,
  generateSphericalXml,
} from "./metadata.js";

const $ = (sel) => document.querySelector(sel);

const state = {
  file: null,
  buffer: null,
  metadata: null,
  busy: false,
};

const canvas = $("#starfield");
const ctx = canvas.getContext("2d");
const stars = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  stars.length = 0;
  for (let i = 0; i < 180; i++) {
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      z: Math.random() * 1.5 + 0.2,
      r: Math.random() * 1.4 + 0.3,
    });
  }
}

function drawStars() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const star of stars) {
    star.y += star.z * 0.15;
    if (star.y > canvas.height) {
      star.y = 0;
      star.x = Math.random() * canvas.width;
    }
    const alpha = 0.25 + star.z * 0.35;
    ctx.beginPath();
    ctx.fillStyle = `rgba(130, 220, 255, ${alpha})`;
    ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
    ctx.fill();
  }
  requestAnimationFrame(drawStars);
}

function setStatus(message, tone = "neutral") {
  const el = $("#status");
  el.textContent = message;
  el.dataset.tone = tone;
}

function setBusy(busy) {
  state.busy = busy;
  $("#inject-btn").disabled = busy || !state.file;
  $("#drop-zone").classList.toggle("disabled", busy);
}

function renderLayout(layout) {
  const bar = $("#layout-bar");
  bar.innerHTML = "";
  for (const item of layout) {
    const seg = document.createElement("div");
    seg.className = `layout-seg layout-${item.name.trim()}`;
    seg.style.flexGrow = item.size;
    seg.title = `${item.name.trim()} · ${formatBytes(item.size)}`;
    bar.appendChild(seg);
  }

  const legend = $("#layout-legend");
  legend.innerHTML = layout
    .map(
      (item) =>
        `<span><i class="dot layout-${item.name.trim()}"></i>${item.name.trim()} ${formatBytes(item.size)}</span>`,
    )
    .join("");
}

function renderMetadata(meta) {
  const panel = $("#metadata-panel");
  const tags = $("#metadata-tags");
  tags.innerHTML = "";

  if (!meta) {
    panel.classList.add("empty");
    $("#meta-empty").hidden = false;
    return;
  }

  panel.classList.remove("empty");
  $("#meta-empty").hidden = true;

  const chips = [];
  if (meta.dimensions) {
    chips.push(["Resolution", `${meta.dimensions[0]}×${meta.dimensions[1]}`]);
  }
  chips.push(["moov position", meta.moovLast ? "after mdat ✓" : "before mdat"]);

  if (meta.v1) {
    for (const [key, value] of Object.entries(meta.v1)) {
      chips.push([key, value]);
    }
  } else {
    chips.push(["v1 XML", "none"]);
  }

  if (meta.v2.stereo) chips.push(["v2 stereo", meta.v2.stereo]);
  if (meta.v2.bounds) {
    chips.push([
      "v2 bounds",
      meta.v2.bounds.map((b) => `0x${b.toString(16)}`).join(", "),
    ]);
  }

  for (const [label, value] of chips) {
    const chip = document.createElement("div");
    chip.className = "chip";
    chip.innerHTML = `<span class="chip-label">${label}</span><span class="chip-value">${value}</span>`;
    tags.appendChild(chip);
  }
}

async function handleFile(file) {
  if (!file || state.busy) return;
  if (!/\.(mp4|mov)$/i.test(file.name)) {
    setStatus("Please choose an MP4 or MOV file.", "error");
    return;
  }

  setBusy(true);
  setStatus("Reading file…");

  try {
    const buffer = new Uint8Array(await file.arrayBuffer());
    const metadata = parseMetadata(buffer);
    state.file = file;
    state.buffer = buffer;
    state.metadata = metadata;

    $("#file-name").textContent = file.name;
    $("#file-size").textContent = formatBytes(file.size);
    $("#workspace").classList.remove("hidden");
    $("#controls").classList.remove("disabled");
    renderLayout(metadata.layout);
    renderMetadata(metadata);
    setStatus("Ready — choose options and inject.", "success");
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Could not parse file.", "error");
  } finally {
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
  setStatus("Injecting metadata locally…");

  try {
    const stereo = $("#stereo-mode").value;
    const vr180 = $("#vr180").checked;
    const useV2 = $("#use-v2").checked || vr180;

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
      setStatus(`VR180: ${vr.summary}`, "neutral");
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
    });

    const outName = state.file.name.replace(/(\.[^.]+)?$/, "_spatial$1");
    downloadBlob(new Blob([output], { type: "application/octet-stream" }), outName);

    const reinjected = parseMetadata(output);
    renderMetadata(reinjected);
    setStatus(`Done — downloaded ${outName}`, "success");
    $("#results").classList.remove("hidden");
    $("#results-text").textContent = `Injected ${outName} (${formatBytes(output.length)})`;
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

  zone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => {
    if (input.files[0]) handleFile(input.files[0]);
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
    const file = e.dataTransfer.files[0];
    handleFile(file);
  });
}

function initControls() {
  $("#inject-btn").addEventListener("click", inject);
  $("#vr180").addEventListener("change", (e) => {
    const on = e.target.checked;
    $("#stereo-mode").disabled = on;
    $("#use-v2").checked = on ? true : $("#use-v2").checked;
  });
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();
drawStars();
initDropZone();
initControls();
