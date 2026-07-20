# In-Place Metadata Inject Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow same-path metadata inject by rewriting only the trailing `moov` box when `mdat` offsets are unchanged, without a full-file copy.

**Architecture:** Extend `Mpeg4Container` with `mdat_delta()` and `save_moov_inplace()`. Branch in `inject_metadata` / `inject_mpeg4_inplace` when input equals output: apply existing inject helpers, refuse if `delta != 0` or `moov` is not last, otherwise serialize `moov` into a memory buffer then overwrite the file tail. Keep two-path inject unchanged.

**Tech Stack:** Python 3, stdlib `unittest` / `io.BytesIO`, existing `spatialmedia.mpeg` box tree.

## Global Constraints

- Same-path inject is the in-place signal; no new CLI flag in v1.
- Fail closed when `mdat` would move (`delta != 0`); never fall back to a full copy.
- Fail if `moov` is not the last top-level box (cannot safely truncate/extend the tail).
- Serialize `moov` to a buffer before writing so leaf reads are not corrupted by overwriting the on-disk `moov`.
- Do not commit unless the user explicitly asks.
- Existing two-path CLI and tests must keep working.

## File Structure

| File | Role |
|------|------|
| `spatialmedia/mpeg/mpeg4_container.py` | `mdat_delta()`, `save_moov_inplace()`; refactor `save()` to use `mdat_delta()` |
| `spatialmedia/metadata_utils.py` | Allow same path; add `inject_mpeg4_inplace()`; share apply-metadata steps |
| `spatialmedia/README.md` | Document same-path in-place inject and layout limitation |
| `spatialmedia_test.py` | In-place success + unsupported-layout error tests |

---

### Task 1: Failing tests for in-place inject

**Files:**
- Modify: `spatialmedia_test.py`
- Test: `spatialmedia_test.py`

**Interfaces:**
- Consumes: CLI `main(args)` (existing); fixtures under `data/`
- Produces: `TestInPlace` cases that expect same-path inject to succeed on fixtures and fail on moov-before-mdat copies

- [ ] **Step 1: Add helpers and failing tests to `spatialmedia_test.py`**

Append (keep existing `TestAdd` intact):

```python
import shutil
import struct


def _top_level_boxes(path):
    size = os.path.getsize(path)
    boxes = []
    with open(path, "rb") as f:
        pos = 0
        while pos < size:
            f.seek(pos)
            header = f.read(8)
            if len(header) < 8:
                break
            box_size, name = struct.unpack(">I4s", header)
            header_size = 8
            if box_size == 1:
                box_size = struct.unpack(">Q", f.read(8))[0]
                header_size = 16
            elif box_size == 0:
                box_size = size - pos
            boxes.append((pos, name, box_size, header_size))
            pos += box_size
    return boxes


def _reorder_moov_before_mdat(src, dst):
    """Write ftyp, then moov, then remaining boxes (e.g. free/mdat).

    Produces a layout where growing moov would shift mdat. Playback
    offsets may be wrong; used only to assert in-place inject refuses.
    """
    boxes = _top_level_boxes(src)
    by_name = {name: (pos, size, hs) for pos, name, size, hs in boxes}
    order = []
    for name in (b"ftyp", b"moov"):
        if name in by_name:
            order.append(name)
    for pos, name, size, hs in boxes:
        if name not in (b"ftyp", b"moov"):
            order.append(name)
    with open(src, "rb") as in_fh, open(dst, "wb") as out_fh:
        for name in order:
            pos, size, hs = by_name[name]
            in_fh.seek(pos)
            out_fh.write(in_fh.read(size))


class TestInPlace(unittest.TestCase):

    def setUp(self):
        try:
            os.mkdir(_OUTPUT_DIR)
        except FileExistsError:
            pass

    def test_inject_inplace_left_right(self):
        target = f"{_OUTPUT_DIR}/inplace_left_right.mp4"
        shutil.copyfile("data/testsrc_320x240_h264.mp4", target)
        before = os.path.getsize(target)
        names_before = [n for _, n, _, _ in _top_level_boxes(target)]
        self.assertEqual(names_before[-1], b"moov")

        self.assertIsNone(main([
            "-i", "--stereo", "left-right",
            target, target,
        ]))

        after = os.path.getsize(target)
        # Grew by metadata only — far less than a full remux copy.
        self.assertGreater(after, before)
        self.assertLess(after - before, 256 * 1024)

        contents = []
        metadata_utils.parse_metadata(target, contents.append)
        text = "\n".join(contents)
        self.assertTrue(text.find("StereoMode = left-right") > 0
                        or text.find("Stereo Mode: 2") >= 0
                        or text.find("left-right") >= 0)

    def test_inject_inplace_refuses_moov_before_mdat(self):
        target = f"{_OUTPUT_DIR}/moov_before_mdat.mp4"
        _reorder_moov_before_mdat("data/testsrc_320x240_h264.mp4", target)
        with open(target, "rb") as f:
            original = f.read()

        logs = []
        # Capture console via main path: inject_metadata prints errors.
        # Call inject_metadata directly for assertion on return/logs.
        metadata = metadata_utils.Metadata()
        metadata.video = metadata_utils.generate_spherical_xml(
            "equirectangular", "left-right", None)

        def console(msg):
            logs.append(msg)

        result = metadata_utils.inject_metadata(target, target, metadata, console)
        with open(target, "rb") as f:
            after = f.read()
        self.assertEqual(original, after)
        joined = "\n".join(logs) + (result or "")
        self.assertTrue(
            "in-place" in joined.lower() or "mdat" in joined.lower(),
            msg=joined)
```

If `StereoMode` string from parse differs, adjust the assertion after the first successful run to match actual `parse_metadata` output (see existing tests for the v1 XML path).

- [ ] **Step 2: Run the new tests — expect failure**

Run:

```bash
python3 spatialmedia_test.py TestInPlace -v
```

Expected: FAIL because same-path inject still returns `"Input and output cannot be the same"` / does not rewrite in place.

---

### Task 2: `Mpeg4Container` in-place helpers

**Files:**
- Modify: `spatialmedia/mpeg/mpeg4_container.py`

**Interfaces:**
- Consumes: existing `resize()`, `moov_box`, `contents`, `first_mdat_position`, box `save(in_fh, out_fh, delta)`
- Produces:
  - `Mpeg4Container.mdat_delta(self) -> int`
  - `Mpeg4Container.save_moov_inplace(self, fh) -> None` (raises `ValueError` if unsafe)

- [ ] **Step 1: Add `mdat_delta` and refactor `save`**

In `spatialmedia/mpeg/mpeg4_container.py`, add `import io` is not needed here if buffer lives in `save_moov_inplace` only — add `import io` for that method.

Replace the delta computation inside `save` with a call to `mdat_delta`:

```python
def mdat_delta(self):
    """Return how much the first mdat content offset would move after resize."""
    self.resize()
    new_position = 0
    for element in self.contents:
        if element.name == constants.TAG_MDAT:
            new_position += element.header_size
            break
        new_position += element.size()
    return new_position - self.first_mdat_position

def save(self, in_fh, out_fh):
    """Save mpeg4 file content to file."""
    delta = self.mdat_delta()
    for element in self.contents:
        element.save(in_fh, out_fh, delta)
```

- [ ] **Step 2: Add `save_moov_inplace`**

```python
def save_moov_inplace(self, fh):
    """Overwrite the on-disk moov box in place.

    Args:
      fh: file handle opened r+b on the original file. Must still contain
          the original moov bytes for any leaf reads during serialization.

    Raises:
      ValueError: if mdat would move, or moov is not the last top-level box.
    """
    if not self.contents or self.contents[-1] is not self.moov_box:
        raise ValueError(
            "In-place inject requires moov to be the last top-level box.")
    delta = self.mdat_delta()
    if delta != 0:
        raise ValueError(
            "In-place inject requires mdat offsets to stay unchanged "
            "(typically moov after mdat). Use a separate output path.")

    moov_pos = self.moov_box.position
    buf = io.BytesIO()
    self.moov_box.save(fh, buf, 0)
    moov_bytes = buf.getvalue()
    fh.seek(moov_pos)
    fh.write(moov_bytes)
    fh.truncate(moov_pos + len(moov_bytes))
    fh.flush()
```

Add `import io` at the top of `mpeg4_container.py`.

- [ ] **Step 3: Quick sanity check (optional)**

```bash
python3 -c "from spatialmedia.mpeg.mpeg4_container import Mpeg4Container; import inspect; print('mdat_delta' in dir(Mpeg4Container))"
```

Expected: prints `True`.

---

### Task 3: Wire in-place inject in `metadata_utils`

**Files:**
- Modify: `spatialmedia/metadata_utils.py` (`inject_mpeg4`, `inject_metadata`; add `inject_mpeg4_inplace` and shared `_apply_metadata_to_mpeg4`)

**Interfaces:**
- Consumes: `mpeg.load`, `mpeg4_add_spherical_xml_v1`, `mpeg4_add_spherical_v2`, `mpeg4_add_audio_metadata`, `Mpeg4Container.save_moov_inplace`
- Produces: `inject_metadata` allows `src == dest`; `inject_mpeg4_inplace(path, metadata, console)`

- [ ] **Step 1: Extract shared apply-metadata helper**

Add near `inject_mpeg4`:

```python
def _apply_metadata_to_mpeg4(mpeg4_file, in_fh, metadata, console):
    if metadata.video and not mpeg4_add_spherical_xml_v1(
            mpeg4_file, in_fh, metadata.video):
        console("Error failed to insert spherical data")
        return False

    if ((metadata.projection or metadata.stereo_mode)
        and not mpeg4_add_spherical_v2(
            mpeg4_file, in_fh, metadata.projection,
            metadata.stereo_mode, metadata.bounds)):
        console("Error failed to insert spherical data v2")
        return False

    if metadata.audio:
        if not mpeg4_add_audio_metadata(
                mpeg4_file, in_fh, metadata.audio, console):
            console("Error failed to insert spatial audio data")
            return False
    return True
```

Refactor `inject_mpeg4` to call `_apply_metadata_to_mpeg4` before `save`.

- [ ] **Step 2: Implement `inject_mpeg4_inplace`**

```python
def inject_mpeg4_inplace(input_file, metadata, console):
    try:
        fh = open(input_file, "r+b")
    except Exception:
        console("Error file: \"" + input_file + "\" does not exist or do not have "
                "permission.")
        return

    with fh:
        mpeg4_file = mpeg.load(fh)
        if mpeg4_file is None:
            console("Error file could not be opened.")
            return

        if not _apply_metadata_to_mpeg4(mpeg4_file, fh, metadata, console):
            return

        console("Saved file settings")
        parse_spherical_mpeg4(mpeg4_file, fh, console)

        try:
            mpeg4_file.save_moov_inplace(fh)
        except ValueError as exc:
            console(str(exc))
            return
```

- [ ] **Step 3: Update `inject_metadata` to branch on same path**

Replace the same-path rejection block with:

```python
def inject_metadata(src, dest, metadata, console):
    infile = os.path.abspath(src)
    outfile = os.path.abspath(dest)

    try:
        in_fh = open(infile, "rb")
        in_fh.close()
    except Exception:
        console("Error: " + infile +
                " does not exist or we do not have permission")
        return

    console("Processing: " + infile)

    extension = os.path.splitext(infile)[1].lower()

    if extension not in MPEG_FILE_EXTENSIONS:
        console("Unknown file type")
        return

    if infile == outfile:
        inject_mpeg4_inplace(infile, metadata, console)
        return

    inject_mpeg4(infile, outfile, metadata, console)
```

- [ ] **Step 4: Run new tests — expect pass**

```bash
python3 spatialmedia_test.py TestInPlace -v
```

Expected: both `TestInPlace` tests PASS.

- [ ] **Step 5: Run full suite — expect pass**

```bash
python3 spatialmedia_test.py -v
```

Expected: all tests PASS.

---

### Task 4: Document in-place usage

**Files:**
- Modify: `spatialmedia/README.md`

**Interfaces:**
- Consumes: behavior from Tasks 2–3
- Produces: README section describing same-path inject and limitation

- [ ] **Step 1: Update Inject docs**

In the Inject section of `spatialmedia/README.md`, after the existing inject command, add:

```markdown
#### In-place inject

Input and output may be the same path. The tool rewrites only the trailing
`moov` metadata box when media offsets would not change (typically when
`moov` follows `mdat`). This avoids making a full second copy of large files.

    python spatialmedia -i [--stereo=...] <file> <file>

If the file layout would require moving `mdat` (for example `moov` before
`mdat`), in-place inject is refused and a separate output path must be used.
```

- [ ] **Step 2: Done**

No further code changes.

---

## Spec coverage

| Spec requirement | Task |
|------------------|------|
| Same-path CLI inject | Task 3 |
| `delta == 0` rewrite moov only | Tasks 2–3 |
| Refuse when `delta != 0` | Tasks 2–3 + test in Task 1 |
| No full-copy fallback | Task 3 |
| Buffer before overwrite | Task 2 `save_moov_inplace` |
| Two-path unchanged | Task 3 branch + full suite |
| Tests for success + refuse | Task 1 |
| Docs | Task 4 |

## Self-review notes

- No placeholders left in steps.
- `save_moov_inplace` uses `io.BytesIO` so leaf `tag_copy` reads see original bytes.
- Extra guard: `moov` must be last top-level box (implies safe truncate); aligns with spec’s “set file length to moov_position + new_moov_size”.
- Commit steps omitted per repo user preference (commit only when asked).
