# In-place spatial metadata inject

## Goal

Allow the Spatial Media Metadata Injector to overwrite an MP4/MOV file in place when injecting metadata, without writing a second full copy of the media data. This is required for large files on disks that cannot hold ~2× the file size.

## Non-goals

- In-place rewriting when `mdat` must move (would require shifting multi‑GB media)
- Automatic fallback to a full-file copy when in-place is impossible
- GUI or Docker web UI changes in the first iteration
- Creating backup copies of the original file

## Background

Today `inject_metadata` requires distinct input and output paths and always rewrites the entire file via `Mpeg4Container.save`, which copies `mdat` byte-for-byte. That needs roughly another full file of free space.

MP4 layout for many large files (including typical camera/export outputs) is:

```
ftyp | mdat (media) | moov (metadata index)
```

Injecting spherical / stereo / spatial-audio atoms grows `moov` only. Because `mdat` sits before `moov`, its file offsets do not change (`delta == 0`), so chunk offset tables (`stco` / `co64`) do not need updating. Only the trailing `moov` region must be rewritten and the file truncated or extended by a few KB–MB.

## Behavior

### CLI

- Allow input and output to be the same path when using `-i` / `--inject`.
- Example:

  ```bash
  python spatialmedia -i --stereo=left-right video.mp4 video.mp4
  ```

- No new flag is required for the first version; same-path is the in-place signal.
- Existing two-file inject behavior is unchanged when paths differ.

### In-place path (same input/output)

1. Open and parse the file (existing `mpeg.load` / inject helpers).
2. Apply metadata into the in-memory box tree (existing `mpeg4_add_spherical_*` / audio helpers).
3. `resize()` the container and compute `delta` the same way `Mpeg4Container.save` does: difference between the new first-`mdat` content position and the original.
4. If `delta != 0`: abort with a clear error, e.g. that in-place inject requires `moov` after `mdat` (or equivalent layout where media offsets are unchanged), and that a separate output path is required.
5. If `delta == 0`:
   - Open the file read/write (`r+b`).
   - Seek to the original top-level `moov` box position.
   - Serialize only the (possibly grown) `moov` box to that position, reading any still-on-disk leaf contents from the same file handle as needed.
   - Set the file length to `moov_position + new_moov_size` (extend or truncate).
6. Print saved settings / parse confirmation as today.

### Separate-output path (different paths)

Unchanged: full rewrite via existing `save(in_fh, out_fh)`.

## Implementation sketch

- `metadata_utils.inject_metadata`: remove/relax the same-path rejection; branch to `inject_mpeg4_inplace` when `infile == outfile`.
- `inject_mpeg4_inplace`: after building metadata on the loaded tree, compute `delta`; on success write `moov` in place.
- Prefer reusing existing box `save(in_fh, out_fh, delta=0)` against an `r+b` handle positioned at the old `moov` offset, rather than inventing a second serializer.
- Do not rewrite `ftyp` or `mdat` when `delta == 0`.

## Safety

- Fail closed when `delta != 0` (no silent full copy).
- Fail if the file cannot be opened for write.
- Write the complete new `moov` before truncating when the new `moov` is smaller than the old one (write first at the same offset, then `truncate`).
- Interruption during the `moov` rewrite can leave a corrupt trailer; acceptable for v1 given the tiny rewrite window vs. a multi-hour full copy. Document this in the CLI error/help text briefly.

## Testing

- Unit/integration: copy a small fixture with `moov`-after-`mdat` layout (or remux a test asset if fixtures are `moov`-first), inject in place, assert metadata present and file size change is only on the order of metadata growth.
- Assert same-path inject with `moov`-before-`mdat` (if easy to produce) returns an error and leaves the original bytes unchanged.
- Existing two-path tests remain green.

## Success criteria

- Same-path inject works on `ftyp`/`mdat`/`moov` files without needing free space ≈ file size.
- Different-path inject behavior unchanged.
- Unsupported layouts fail with an actionable message instead of attempting a full rewrite.
