"""
Unit tests for the spatialmedia CLI tool.

# Test inputs are generated with
ffmpeg -y -f lavfi -i testsrc -vf scale=320:240 -vcodec libx264 -t 0.05 data/testsrc_320x240_h264.mp4
ffmpeg -y -f lavfi -i testsrc -vf scale=320:240 -vcodec libvpx-vp9 -t 0.05 data/testsrc_320x240_vp9.mp4
ffmpeg -y -f lavfi -i testsrc -vf scale=32:24 -vcodec prores -t 0.05 data/testsrc_32x24_prores.mov

"""
import unittest
import os
import shutil
import struct

from spatialmedia.__main__ import main
from spatialmedia import metadata_utils

_OUTPUT_DIR = 'test_output'


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

def append_contents(contents):
    def append(x):
        contents = contents + x
    return append

class TestAdd(unittest.TestCase):

    def inject_metadata(self, args):
        self.assertIsNone(main(args))

        contents = []
        metadata_utils.parse_metadata(args[-1],
                                      lambda x: contents.append(x))
        try:
            os.remove(args[-1])
        except:
            return ''
        return '\n'.join(contents[2:])

    def test_inject_v1_equirect_mono(self):
        contents = self.inject_metadata(['-i',
                                         '--projection', 'equirectangular',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono_v1.mp4'])

        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find("ProjectionType = equirectangular") > 0)

    def test_inject_v1_rectangular_left_right(self):
        contents = self.inject_metadata(['-i',
                                         '--stereo', 'left-right',
                                         '--projection', 'none',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/rectangular_left_right_v1.mp4'])

        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertFalse(contents.find("ProjectionType = equirectangular") > 0)
        self.assertTrue(contents.find("ProjectionType = rectangular") > 0)
        self.assertTrue(contents.find("Spherical = false") > 0)

    def test_inject_v2_equirect_mono(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--projection', 'equirectangular',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono.mp4'])
        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('SVHD') >= 0)
        self.assertTrue(
            contents.find('Spherical Metadata Tool') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Bounds Top: 0') >= 0)
        self.assertTrue(contents.find('Bounds Bottom: 0') >= 0)
        self.assertTrue(contents.find('Bounds Left: 0') >= 0)
        self.assertTrue(contents.find('Bounds Right: 0') >= 0)

    def test_inject_v2_equirect_mono_with_bounds(self):
        contents = self.inject_metadata(['-i',
                                         '--v2',
                                         '--bounds', '0x1:-2:0x7FFFFFFF:32',
                                         '--projection', 'equirectangular',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono.mp4'])
        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('SVHD') >= 0)
        self.assertTrue(
            contents.find('Spherical Metadata Tool') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Bounds Top: 1') >= 0)
        self.assertTrue(contents.find('Bounds Bottom: 0') >= 0)
        self.assertTrue(contents.find('Bounds Left: 2147483647') >= 0)
        self.assertTrue(contents.find('Bounds Right: 32') >= 0)

    def test_inject_v2_equirect_mono_vp9(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--projection', 'equirectangular',
                                         'data/testsrc_320x240_vp9.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono_vp9.mp4'])

        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('SVHD') >= 0)
        self.assertTrue(
            contents.find('Spherical Metadata Tool') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)

    def test_inject_v2_equirect_mono_prores(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--projection', 'equirectangular',
                                         'data/testsrc_32x24_prores.mov',
                                         f'{_OUTPUT_DIR}/equirect_mono_prores.mov'])
        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('SVHD') >= 0)
        self.assertTrue(
            contents.find('Spherical Metadata Tool') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)


    def test_inject_v2_rectangular_left_right(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--stereo', 'left-right',
                                         '--projection', 'none',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/rectangular_left_right.mp4'])
        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertTrue(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Stereo Mode: 2') >= 0)

    def test_inject_v2_rectangular_top_bottom(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--stereo', 'top-bottom',
                                         '--projection', 'none',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/rectangular_top_bottom.mp4'])

        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertTrue(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Stereo Mode: 1') >= 0)


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
        self.assertIn("StereoMode = left-right", text)

    def test_inject_inplace_refuses_moov_before_mdat(self):
        target = f"{_OUTPUT_DIR}/moov_before_mdat.mp4"
        _reorder_moov_before_mdat("data/testsrc_320x240_h264.mp4", target)
        with open(target, "rb") as f:
            original = f.read()

        logs = []
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


if __name__ == '__main__':
    try:
        os.mkdir('test_output')
    except:
        pass
    unittest.main()
