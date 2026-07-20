"""
Unit tests for the spatialmedia CLI tool.

# Test inputs are generated with
ffmpeg -y -f lavfi -i testsrc -vf scale=320:240 -vcodec libx264 -t 0.05 data/testsrc_320x240_h264.mp4
ffmpeg -y -f lavfi -i testsrc -vf scale=320:240 -vcodec libvpx-vp9 -t 0.05 data/testsrc_320x240_vp9.mp4
ffmpeg -y -f lavfi -i testsrc -vf scale=32:24 -vcodec prores -t 0.05 data/testsrc_32x24_prores.mov

"""

import io
import os
import shutil
import struct
import unittest
from contextlib import redirect_stdout

from spatialmedia import metadata_utils
from spatialmedia.__main__ import main
from spatialmedia.mpeg import mpeg4_container

_OUTPUT_DIR = "test_output"
_FIXTURE_H264 = "data/testsrc_320x240_h264.mp4"


def _ensure_output_dir():
    try:
        os.mkdir(_OUTPUT_DIR)
    except FileExistsError:
        pass


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


def _parse_text(path):
    lines = []
    metadata_utils.parse_metadata(path, lines.append)
    return "\n".join(lines)


def _run_main(args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        main(args)
    return buf.getvalue()


class TestAdd(unittest.TestCase):
    def inject_metadata(self, args):
        self.assertIsNone(main(args))

        contents = []
        metadata_utils.parse_metadata(args[-1], lambda x: contents.append(x))
        try:
            os.remove(args[-1])
        except OSError:
            return ""
        return "\n".join(contents[2:])

    def test_inject_v1_equirect_mono(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--projection",
                "equirectangular",
                "data/testsrc_320x240_h264.mp4",
                f"{_OUTPUT_DIR}/equirect_mono_v1.mp4",
            ]
        )

        self.assertFalse(contents.find("SV3D") >= 0)
        self.assertFalse(contents.find("PRHD") >= 0)
        self.assertFalse(contents.find("EQUI") >= 0)
        self.assertFalse(contents.find("ST3D") >= 0)
        self.assertTrue(contents.find("ProjectionType = equirectangular") > 0)

    def test_inject_v1_rectangular_left_right(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--stereo",
                "left-right",
                "--projection",
                "none",
                "data/testsrc_320x240_h264.mp4",
                f"{_OUTPUT_DIR}/rectangular_left_right_v1.mp4",
            ]
        )

        self.assertFalse(contents.find("SV3D") >= 0)
        self.assertFalse(contents.find("PRHD") >= 0)
        self.assertFalse(contents.find("EQUI") >= 0)
        self.assertFalse(contents.find("ST3D") >= 0)
        self.assertFalse(contents.find("ProjectionType = equirectangular") > 0)
        self.assertTrue(contents.find("ProjectionType = rectangular") > 0)
        self.assertTrue(contents.find("Spherical = false") > 0)

    def test_inject_v2_equirect_mono(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--v2",
                "--projection",
                "equirectangular",
                "data/testsrc_320x240_h264.mp4",
                f"{_OUTPUT_DIR}/equirect_mono.mp4",
            ]
        )
        self.assertTrue(contents.find("SV3D") >= 0)
        self.assertTrue(contents.find("SVHD") >= 0)
        self.assertTrue(contents.find("Spherical Metadata Tool") >= 0)
        self.assertTrue(contents.find("PRHD") >= 0)
        self.assertTrue(contents.find("EQUI") >= 0)
        self.assertFalse(contents.find("ST3D") >= 0)
        self.assertTrue(contents.find("Bounds Top: 0") >= 0)
        self.assertTrue(contents.find("Bounds Bottom: 0") >= 0)
        self.assertTrue(contents.find("Bounds Left: 0") >= 0)
        self.assertTrue(contents.find("Bounds Right: 0") >= 0)

    def test_inject_v2_equirect_mono_with_bounds(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--v2",
                "--bounds",
                "0x1:-2:0x7FFFFFFF:32",
                "--projection",
                "equirectangular",
                "data/testsrc_320x240_h264.mp4",
                f"{_OUTPUT_DIR}/equirect_mono.mp4",
            ]
        )
        self.assertTrue(contents.find("SV3D") >= 0)
        self.assertTrue(contents.find("SVHD") >= 0)
        self.assertTrue(contents.find("Spherical Metadata Tool") >= 0)
        self.assertTrue(contents.find("PRHD") >= 0)
        self.assertTrue(contents.find("EQUI") >= 0)
        self.assertFalse(contents.find("ST3D") >= 0)
        self.assertTrue(contents.find("Bounds Top: 1") >= 0)
        self.assertTrue(contents.find("Bounds Bottom: 0") >= 0)
        self.assertTrue(contents.find("Bounds Left: 2147483647") >= 0)
        self.assertTrue(contents.find("Bounds Right: 32") >= 0)

    def test_inject_v2_equirect_mono_vp9(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--v2",
                "--projection",
                "equirectangular",
                "data/testsrc_320x240_vp9.mp4",
                f"{_OUTPUT_DIR}/equirect_mono_vp9.mp4",
            ]
        )

        self.assertTrue(contents.find("SV3D") >= 0)
        self.assertTrue(contents.find("SVHD") >= 0)
        self.assertTrue(contents.find("Spherical Metadata Tool") >= 0)
        self.assertTrue(contents.find("PRHD") >= 0)
        self.assertTrue(contents.find("EQUI") >= 0)
        self.assertFalse(contents.find("ST3D") >= 0)

    def test_inject_v2_equirect_mono_prores(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--v2",
                "--projection",
                "equirectangular",
                "data/testsrc_32x24_prores.mov",
                f"{_OUTPUT_DIR}/equirect_mono_prores.mov",
            ]
        )
        self.assertTrue(contents.find("SV3D") >= 0)
        self.assertTrue(contents.find("SVHD") >= 0)
        self.assertTrue(contents.find("Spherical Metadata Tool") >= 0)
        self.assertTrue(contents.find("PRHD") >= 0)
        self.assertTrue(contents.find("EQUI") >= 0)
        self.assertFalse(contents.find("ST3D") >= 0)

    def test_inject_v2_rectangular_left_right(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--v2",
                "--stereo",
                "left-right",
                "--projection",
                "none",
                "data/testsrc_320x240_h264.mp4",
                f"{_OUTPUT_DIR}/rectangular_left_right.mp4",
            ]
        )
        self.assertFalse(contents.find("SV3D") >= 0)
        self.assertFalse(contents.find("PRHD") >= 0)
        self.assertFalse(contents.find("EQUI") >= 0)
        self.assertTrue(contents.find("ST3D") >= 0)
        self.assertTrue(contents.find("Stereo Mode: 2") >= 0)

    def test_inject_v2_rectangular_top_bottom(self):
        contents = self.inject_metadata(
            [
                "-i",
                "--v2",
                "--stereo",
                "top-bottom",
                "--projection",
                "none",
                "data/testsrc_320x240_h264.mp4",
                f"{_OUTPUT_DIR}/rectangular_top_bottom.mp4",
            ]
        )

        self.assertFalse(contents.find("SV3D") >= 0)
        self.assertFalse(contents.find("PRHD") >= 0)
        self.assertFalse(contents.find("EQUI") >= 0)
        self.assertTrue(contents.find("ST3D") >= 0)
        self.assertTrue(contents.find("Stereo Mode: 1") >= 0)


class TestInPlace(unittest.TestCase):
    def setUp(self):
        _ensure_output_dir()

    def test_inject_inplace_left_right(self):
        target = f"{_OUTPUT_DIR}/inplace_left_right.mp4"
        shutil.copyfile("data/testsrc_320x240_h264.mp4", target)
        before = os.path.getsize(target)
        names_before = [n for _, n, _, _ in _top_level_boxes(target)]
        self.assertEqual(names_before[-1], b"moov")

        self.assertIsNone(
            main(
                [
                    "-i",
                    "--stereo",
                    "left-right",
                    target,
                    target,
                ]
            )
        )

        after = os.path.getsize(target)
        # Grew by metadata only — far less than a full remux copy.
        self.assertGreater(after, before)
        self.assertLess(after - before, 256 * 1024)

        contents = []
        metadata_utils.parse_metadata(target, contents.append)
        text = "\n".join(contents)
        self.assertIn("StereoMode = left-right", text)

    def test_inject_inplace_refuses_moov_before_mdat(self):
        target = f"{_OUTPUT_DIR}/moov_before_mdat.mp4"
        shutil.copyfile("data/testsrc_320x240_h264_moov_first.mp4", target)
        with open(target, "rb") as f:
            original = f.read()

        logs = []
        metadata = metadata_utils.Metadata()
        metadata.video = metadata_utils.generate_spherical_xml(
            "equirectangular", "left-right", None
        )

        def console(msg):
            logs.append(msg)

        result = metadata_utils.inject_metadata(target, target, metadata, console)
        with open(target, "rb") as f:
            after = f.read()
        self.assertEqual(original, after)
        joined = "\n".join(logs) + (result or "")
        self.assertTrue("in-place" in joined.lower() or "mdat" in joined.lower(), msg=joined)

    def test_in_place_flag_and_vr180(self):
        target = f"{_OUTPUT_DIR}/cli_vr180.mp4"
        shutil.copyfile("data/testsrc_320x240_h264.mp4", target)
        self.assertIsNone(main(["-I", "--vr180", target]))
        contents = []
        metadata_utils.parse_metadata(target, contents.append)
        text = "\n".join(contents)
        self.assertIn("StereoMode = left-right", text)
        self.assertIn("SV3D", text)
        self.assertIn("CroppedAreaImageWidthPixels = 160", text)


class TestHelpers(unittest.TestCase):
    def test_get_video_dimensions(self):
        self.assertEqual(metadata_utils.get_video_dimensions(_FIXTURE_H264), (320, 240))

    def test_get_video_dimensions_missing_file(self):
        self.assertIsNone(metadata_utils.get_video_dimensions("data/does_not_exist.mp4"))

    def test_generate_spherical_xml_with_crop(self):
        xml = metadata_utils.generate_spherical_xml(
            "equirectangular", "left-right", "160:240:320:240:80:0"
        )
        self.assertIn("CroppedAreaImageWidthPixels>160", xml)
        self.assertIn("FullPanoWidthPixels>320", xml)
        self.assertIn("StereoMode>left-right", xml)


class TestCliValidation(unittest.TestCase):
    def setUp(self):
        _ensure_output_dir()

    def test_in_place_requires_single_file(self):
        out = _run_main(
            [
                "-I",
                "--stereo",
                "left-right",
                _FIXTURE_H264,
                f"{_OUTPUT_DIR}/extra.mp4",
            ]
        )
        self.assertIn("exactly one file", out)

    def test_inject_and_in_place_mutually_exclusive(self):
        out = _run_main(
            [
                "-i",
                "-I",
                _FIXTURE_H264,
                f"{_OUTPUT_DIR}/both.mp4",
            ]
        )
        self.assertIn("not both", out)

    def test_vr180_on_missing_file(self):
        out = _run_main(["-I", "--vr180", "data/no_such_file.mp4"])
        self.assertIn("Could not read video dimensions", out)


class TestMetadataConflictClearing(unittest.TestCase):
    def setUp(self):
        _ensure_output_dir()

    def test_v2_inject_clears_v1_tags(self):
        target = f"{_OUTPUT_DIR}/v2_clears_v1.mp4"
        shutil.copyfile(_FIXTURE_H264, target)
        self.assertIsNone(
            main(
                [
                    "-i",
                    "--projection",
                    "equirectangular",
                    target,
                    f"{_OUTPUT_DIR}/v1_step.mp4",
                ]
            )
        )
        shutil.copyfile(f"{_OUTPUT_DIR}/v1_step.mp4", target)

        self.assertIsNone(
            main(
                [
                    "-i",
                    "-2",
                    "--stereo",
                    "left-right",
                    target,
                    target,
                ]
            )
        )
        text = _parse_text(target)
        self.assertIn("ST3D", text)
        self.assertIn("SV3D", text)
        self.assertNotIn("ProjectionType = equirectangular", text)

    def test_v1_inject_clears_v2_tags(self):
        target = f"{_OUTPUT_DIR}/v1_clears_v2.mp4"
        shutil.copyfile(_FIXTURE_H264, target)
        self.assertIsNone(
            main(
                [
                    "-i",
                    "-2",
                    "--stereo",
                    "left-right",
                    target,
                    f"{_OUTPUT_DIR}/v2_step.mp4",
                ]
            )
        )
        shutil.copyfile(f"{_OUTPUT_DIR}/v2_step.mp4", target)

        self.assertIsNone(
            main(
                [
                    "-i",
                    "--stereo",
                    "left-right",
                    target,
                    target,
                ]
            )
        )
        text = _parse_text(target)
        self.assertIn("StereoMode = left-right", text)
        self.assertNotIn("ST3D", text)
        self.assertNotIn("SV3D", text)


class TestMpeg4Container(unittest.TestCase):
    def test_mdat_delta_zero_for_moov_last_fixture(self):
        with open(_FIXTURE_H264, "rb") as fh:
            mpeg4 = mpeg4_container.load(fh)
        self.assertEqual(mpeg4.mdat_delta(), 0)
        self.assertEqual(_top_level_boxes(_FIXTURE_H264)[-1][1], b"moov")

    def test_moov_first_fixture_is_unsupported_for_inplace(self):
        names = [n for _, n, _, _ in _top_level_boxes("data/testsrc_320x240_h264_moov_first.mp4")]
        self.assertEqual(names[:2], [b"ftyp", b"moov"])
        self.assertNotEqual(names[-1], b"moov")

    def test_save_moov_inplace_roundtrip(self):
        target = f"{_OUTPUT_DIR}/container_inplace.mp4"
        shutil.copyfile(_FIXTURE_H264, target)
        before = os.path.getsize(target)

        metadata = metadata_utils.Metadata("equirectangular", "left-right", None)
        metadata.video = metadata_utils.generate_spherical_xml(
            "equirectangular", "left-right", None
        )

        logs = []
        metadata_utils.inject_metadata(target, target, metadata, logs.append)

        after = os.path.getsize(target)
        self.assertGreater(after, before)
        self.assertLess(after - before, 256 * 1024)
        self.assertIn("StereoMode = left-right", _parse_text(target))

    def test_save_moov_inplace_raises_for_moov_first(self):
        with open("data/testsrc_320x240_h264_moov_first.mp4", "r+b") as fh:
            mpeg4 = mpeg4_container.load(fh)
            with self.assertRaises(ValueError) as ctx:
                mpeg4.save_moov_inplace(fh)
        msg = str(ctx.exception).lower()
        self.assertTrue("last top-level box" in msg or "mdat" in msg, msg=msg)


class TestTwoPathInject(unittest.TestCase):
    def setUp(self):
        _ensure_output_dir()

    def test_separate_output_leaves_source_unchanged(self):
        source = f"{_OUTPUT_DIR}/source_unchanged.mp4"
        output = f"{_OUTPUT_DIR}/source_unchanged_out.mp4"
        shutil.copyfile(_FIXTURE_H264, source)
        original = os.path.getsize(source)

        self.assertIsNone(
            main(
                [
                    "-i",
                    "--stereo",
                    "left-right",
                    source,
                    output,
                ]
            )
        )

        self.assertEqual(os.path.getsize(source), original)
        self.assertTrue(os.path.exists(output))
        self.assertNotEqual(os.path.getsize(output), original)
        self.assertIn("StereoMode = left-right", _parse_text(output))


if __name__ == "__main__":
    _ensure_output_dir()
    unittest.main()
