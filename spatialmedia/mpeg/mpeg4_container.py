#! /usr/bin/env python

# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MPEG4 processing classes.

Functions for loading MP4/MOV files and manipulating boxes.
"""

from __future__ import annotations

import io
from typing import BinaryIO, Optional

from spatialmedia.mpeg import constants, container


def load(fh: BinaryIO) -> Optional[Mpeg4Container]:
    """Load the mpeg4 file structure of a file.

    Args:
      fh: file handle, input file handle.

    return:
      mpeg4, the loaded mpeg4 structure.
    """

    fh.seek(0, 2)
    size = fh.tell()
    contents = container.load_multiple(fh, 0, size)

    if not contents:
        print("Error, failed to load .mp4 file.")
        return None
    elif len(contents) == 0:
        print("Error, no boxes found.")
        return None

    loaded_mpeg4 = Mpeg4Container()
    loaded_mpeg4.contents = contents

    for element in loaded_mpeg4.contents:
        if element.name == constants.TAG_MOOV:
            loaded_mpeg4.moov_box = element
        if element.name == constants.TAG_FREE:
            loaded_mpeg4.free_box = element
        if element.name == constants.TAG_MDAT and not loaded_mpeg4.first_mdat_box:
            loaded_mpeg4.first_mdat_box = element
        if element.name == constants.TAG_FTYP:
            loaded_mpeg4.ftyp_box = element

    if not loaded_mpeg4.moov_box:
        print("Error, file does not contain moov box.")
        return None

    if not loaded_mpeg4.first_mdat_box:
        print("Error, file does not contain mdat box.")
        return None

    loaded_mpeg4.first_mdat_position = loaded_mpeg4.first_mdat_box.position
    loaded_mpeg4.first_mdat_position += loaded_mpeg4.first_mdat_box.header_size

    loaded_mpeg4.content_size = 0
    for element in loaded_mpeg4.contents:
        loaded_mpeg4.content_size += element.size()

    return loaded_mpeg4


class Mpeg4Container(container.Container):
    """Specialized behaviour for the root mpeg4 container."""

    def __init__(self) -> None:
        self.contents = list()
        self.content_size = 0
        self.header_size = 0
        self.moov_box = None
        self.free_box = None
        self.first_mdat_box = None
        self.ftyp_box = None
        self.first_mdat_position: Optional[int] = None
        self.padding = 0

    def merge(self, element):
        """Mpeg4 containers do not support merging."""
        print("Cannot merge mpeg4 files")
        exit(0)

    def print_structure(self) -> None:
        """Print mpeg4 file structure recursively."""
        print(f"mpeg4 [{self.content_size}]")

        size = len(self.contents)
        for i in range(size):
            next_indent = " ├──"
            if i == (size - 1):
                next_indent = " └──"

            self.contents[i].print_structure(next_indent)

    def mdat_delta(self) -> int:
        """Return how much the first mdat content offset would move after resize."""
        self.resize()
        new_position = 0
        for element in self.contents:
            if element.name == constants.TAG_MDAT:
                new_position += element.header_size
                break
            new_position += element.size()
        return new_position - self.first_mdat_position

    def save(self, in_fh: BinaryIO, out_fh: BinaryIO) -> None:
        """Save mpeg4 filecontent to file.

        Args:
          in_fh: file handle, source file handle for uncached contents.
          out_fh: file handle, destination file hand for saved file.
        """
        delta = self.mdat_delta()

        for element in self.contents:
            element.save(in_fh, out_fh, delta)

    def save_moov_inplace(self, fh: BinaryIO) -> None:
        """Overwrite the on-disk moov box in place.

        Args:
          fh: file handle opened r+b on the original file. Must still contain
              the original moov bytes for any leaf reads during serialization.

        Raises:
          ValueError: if mdat would move, or moov is not the last top-level box.
        """
        if not self.contents or self.contents[-1] is not self.moov_box:
            raise ValueError("In-place inject requires moov to be the last top-level box.")
        delta = self.mdat_delta()
        if delta != 0:
            raise ValueError(
                "In-place inject requires mdat offsets to stay unchanged "
                "(typically moov after mdat). Use a separate output path."
            )

        moov_pos = self.moov_box.position
        buf = io.BytesIO()
        self.moov_box.save(fh, buf, 0)
        moov_bytes = buf.getvalue()
        fh.seek(moov_pos)
        fh.write(moov_bytes)
        fh.truncate(moov_pos + len(moov_bytes))
        fh.flush()
