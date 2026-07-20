# Spatial Audio Resources

Reference assets for **ambisonic binaural monitoring**: the same class of HRIR filters used in Google VR Audio, YouTube 360/VR, and related decoders. Use these when building preview tools or monitoring ambisonic mixes in a DAW.

These are **listening/monitoring assets**, not metadata injection code. To tag MP4/MOV files with spatial audio metadata (`SA3D` atoms), use the [browser demo](https://nandan-18.github.io/spatial-media/), the [CLI/GUI](../cli/README.md) (`-a`), or the [Docker web UI](../docker/README.md). See the [Spatial Audio RFC](../web/spec/audio.md) for the box format.

## Directory overview

| Directory | Contents |
|-----------|----------|
| [hrirs/](hrirs/) | Cube-layout HRIR measurements (SADIE KU100–derived); includes an [ambiX](https://github.com/kronihias/ambix) preset |
| [decoder/](decoder/) | Spherical-harmonic HRIR filters for first-order ambisonic binaural decode (Google VR Audio style) |
| [corrections/](corrections/) | EQ compensation when migrating mixes from THRIVE HRTFs to SADIE KU100 |
| [vendor/](vendor/) | Third-party HRIR measurements |

## Raw symmetric cube HRIRs

Binaural measurements (Head Related Impulse Responses) from a **cube loudspeaker** configuration, used in the Google VR Audio first-order ambisonic binaural decoder. Derived from the [SADIE binaural measurements](https://www.york.ac.uk/sadie-project/binaural.html) as individual time-domain FIR filters.

### Specification

| Property | Value |
|----------|-------|
| Subject | 002 (KU100 binaural head) |
| Sample rate | 48 kHz |
| Bit depth | 16 bit |
| Length | 256 samples |
| Fade-in | none |
| Fade-out | half-Hann (16 samples) |
| Symmetry | yes (left hemisphere only) |
| Applied gain | 0 dB |

An ambiX binaural decoder preset (`cube.config`) is included.

**Note:** Using these filters directly (or via the ambiX preset) will **not** match Google VR Audio output unless you also apply phase-matched shelf filters, as described in [Is My Decoder Ambisonic?](http://www.ai.sri.com/ajh/ambisonics/BLaH3.pdf) (Heller, Lee, Benjamin). For a closer match without custom shelf design, use the **symmetric ambisonic binaural decoder** set below.

## Symmetric ambisonic binaural decoder

Spherical harmonic HRIR filters for **first-order ambisonic binaural decode** in Google VR Audio. Apply them to an ambisonic mix and route the convolver outputs to stereo L/R:

![symmetric binaural ambisonic decoder - signal flow diagram](https://cloud.githubusercontent.com/assets/26985965/24811254/2143fb12-1b7a-11e7-99a0-cef55c3f8365.png)

Convolution (`*`) can be done with multichannel convolver plugins such as [LAConvolver](http://audio.lernvall.com/) (macOS) or [Freeverb3](http://www.nongnu.org/freeverb3/) (Windows). The dotted red line with Ø denotes 180° phase inversion.

## Ambisonic correction filters

Filters that compensate for HRTF changes when switching the binaural decoder from **THRIVE** to **SADIE KU100**. Apply them to ambiX tracks so existing mixes retain similar timbre after the decoder change.

**Before correction:** spectral shift when switching decoders:

![decoder output before correction](https://cloud.githubusercontent.com/assets/26985965/24811252/21399d66-1b7a-11e7-953c-2357d6be8f3a.png)

**After correction:** minimized difference:

![decoder output after correction](https://cloud.githubusercontent.com/assets/26985965/24811250/2137f42a-1b7a-11e7-9ff5-e09718293401.png)

Signal flow when applying correction in the DAW:

![ambiX correction filters - signal flow diagram](https://cloud.githubusercontent.com/assets/26985965/24811249/21269c84-1b7a-11e7-8139-91e4fd0d0a20.png)

## FAQs

### Why did you change HRTFs?

Binaural decoding depends on HRTFs, which vary by listener. In listening tests (53 participants, mobile VR, varied content), the **SADIE KU100** set ranked highest on average when individualized HRTFs were unavailable:

![perceived decoder quality](https://cloud.githubusercontent.com/assets/26985965/24811253/213b6628-1b7a-11e7-9079-f7a906e963a0.png)

### Should I monitor with HRTFs when mixing for YouTube 360/VR?

Yes. Use the **symmetric ambisonic binaural decoder** filters and/or preview on YouTube to judge timbre and loudness. Decoder choice affects both coloration and level.

### What is timbral coloration?

HRTFs impose listener-specific spectral coloration. Example frequency responses for THRIVE vs SADIE KU100:

![HRTF coloration](https://cloud.githubusercontent.com/assets/26985965/24811251/2139476c-1b7a-11e7-865b-f37ac10b197f.png)

### Can I retune an existing THRIVE-monitored mix?

Apply the [ambisonic correction filters](#corrections) to your ambiX tracks to align timbre with the SADIE KU100 decoder.

### Expected loudness

Binaural decode level depends on the HRTF set. Google VR Audio targets loudness comparable to a standard M/S stereo decoder. Example measurements (0.5 normalized pink noise, eight directions, [ITU-R BS.1770-4](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-4-201510-I!!PDF-E.pdf)):

| Decoder | Loudness (dB LUFS) | Absolute peak |
|---------|-------------------|---------------|
| M-S stereo | −10.59 | 0.5000 |
| THRIVE | −10.99 | 0.9478 |
| SADIE KU100 | −11.20 | 0.9642 |

Peaks may exceed 0 dBFS even when integrated loudness matches.

### Third-party monitoring tools

Plugins such as [BlueRippleSound O3A View](http://www.blueripplesound.com/products/o3a-view-vst), [Noisemakers AmbiHead](http://www.noisemakers.fr/ambi-head/), and [SoundParticles](http://soundparticles.com/) implement binaural preview using HRTFs from this repository, aligned with YouTube 360/VR playback.

## Repository note on binary assets

HRIR and filter assets in this tree are small enough for regular git. If you add large measurement sets later, prefer [Git LFS](https://git-lfs.com/) or release artifacts instead of committing multi‑hundred‑MB blobs to main history.
