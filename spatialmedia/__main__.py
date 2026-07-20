#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
"""Spatial Media Metadata Injector

Tool for examining and injecting spatial media metadata in MP4/MOV files.
"""

import argparse
import sys

from spatialmedia import metadata_utils


def console(contents):
  print(contents)


def main_entry():
  """Console-script entry point."""
  main(sys.argv[1:])


def main(main_args):
  """Main function for printing and injecting spatial media metadata."""

  parser = argparse.ArgumentParser(
      usage=
      "%(prog)s [options] [files...]\n\nBy default prints out spatial media "
      "metadata from specified files.")
  parser.add_argument(
      "-i",
      "--inject",
      action="store_true",
      help=
      "injects spatial media metadata into the first file specified (.mp4 or "
      ".mov) and saves the result to the second file specified")
  parser.add_argument(
      "-I",
      "--in-place",
      action="store_true",
      help=
      "inject metadata into a single file in place (no second full copy when "
      "supported by the file layout)")
  parser.add_argument(
      "-2",
      "--v2",
      action="store_true",
      help=
      "Uses v2 of the video metadata spec")
  parser.add_argument(
      "--vr180",
      action="store_true",
      help=
      "VR180 side-by-side helper: sets left-right stereo plus 180° crop and "
      "v2 equirect bounds from the video dimensions")
  video_group = parser.add_argument_group("Spherical Video")
  video_group.add_argument("-s",
                           "--stereo",
                           action="store",
                           dest="stereo_mode",
                           metavar="STEREO-MODE",
                           choices=["none", "top-bottom", "left-right"],
                           default="none",
                           help="stereo mode (none | top-bottom | left-right)")
  video_group.add_argument("-p",
                           "--projection",
                           action="store",
                           dest="projection",
                           choices=["none", "equirectangular"],
                           default="equirectangular",
                           help="projection (none | equirectangular)")
  video_group.add_argument(
      "-c",
      "--crop",
      action="store",
      default=None,
      help=
      "crop region. Must specify 6 integers in the form of \"w:h:f_w:f_h:x:y\""
      " where w=CroppedAreaImageWidthPixels h=CroppedAreaImageHeightPixels "
      "f_w=FullPanoWidthPixels f_h=FullPanoHeightPixels "
      "x=CroppedAreaLeftPixels y=CroppedAreaTopPixels")
  video_group.add_argument(
      "-b",
      "--bounds",
      action="store",
      default=None,
      help=
      "Equirect projection bounds for VR180. Must specify 4 integers "
      "in the form of \"top:bottom:left:right\" where each integer is "
      "a 0.32 fixed point value on the amount to crop from the corresponding "
      "border")
  audio_group = parser.add_argument_group("Spatial Audio")
  audio_group.add_argument(
      "-a",
      "--spatial-audio",
      action="store_true",
      help=
      "spatial audio. First-order periphonic ambisonics with ACN channel "
      "ordering and SN3D normalization")
  parser.add_argument("file", nargs="+", help="input/output files")

  args = parser.parse_args(main_args)

  if args.in_place and args.inject:
    console("Use either -i/--inject or -I/--in-place, not both.")
    return

  do_inject = args.inject or args.in_place
  if do_inject:
    if args.in_place:
      if len(args.file) != 1:
        console("In-place inject requires exactly one file.")
        return
      input_file = args.file[0]
      output_file = args.file[0]
    else:
      if len(args.file) != 2:
        console("Injecting metadata requires both an input file and output file.")
        return
      input_file = args.file[0]
      output_file = args.file[1]

    stereo_mode = args.stereo_mode
    projection = args.projection
    crop = args.crop
    bounds = args.bounds
    use_v2 = args.v2

    if args.vr180:
      dims = metadata_utils.get_video_dimensions(input_file)
      if not dims:
        console("Could not read video dimensions for --vr180.")
        return
      width, height = dims
      if width < 2 or height < 1:
        console("Invalid video dimensions for --vr180: %dx%d" % (width, height))
        return
      eye_w = width // 2
      eye_h = height
      stereo_mode = "left-right"
      projection = "equirectangular"
      crop = "%d:%d:%d:%d:%d:0" % (
          eye_w, eye_h, eye_w * 2, eye_h, eye_w // 2)
      bounds = "0:0:0x40000000:0x40000000"
      use_v2 = True
      console("VR180 settings: %dx%d frame, crop=%s, bounds=%s" % (
          width, height, crop, bounds))

    metadata = metadata_utils.Metadata(projection, stereo_mode, bounds)
    if args.vr180:
      # Keep v2 fields and also write v1 XML with crop for broader players.
      metadata.video = metadata_utils.generate_spherical_xml(
          projection, stereo_mode, crop)
    elif not use_v2:
      metadata.projection = None
      metadata.stereo_mode = None
      metadata.video = metadata_utils.generate_spherical_xml(
          projection, stereo_mode, crop)

    if args.spatial_audio:
      parsed_metadata = metadata_utils.parse_metadata(input_file, console)
      if not metadata.audio:
        spatial_audio_description = metadata_utils.get_spatial_audio_description(
            parsed_metadata.num_audio_channels)
        if spatial_audio_description.is_supported:
          metadata.audio = metadata_utils.get_spatial_audio_metadata(
              spatial_audio_description.order,
              spatial_audio_description.has_head_locked_stereo)
        else:
          console("Audio has %d channel(s) and is not a supported "
                  "spatial audio format." % (parsed_metadata.num_audio_channels))
          return

    if metadata.video or metadata.projection or metadata.stereo_mode:
      metadata_utils.inject_metadata(input_file, output_file, metadata, console)
    else:
      console("Failed to generate metadata.")
    return

  if len(args.file) > 0:
    for input_file in args.file:
      if args.spatial_audio:
        parsed_metadata = metadata_utils.parse_metadata(input_file, console)
        metadata.audio = metadata_utils.get_spatial_audio_description(
            parsed_metadata.num_channels)

      metadata_utils.parse_metadata(input_file, console)
    return

  parser.print_help()
  return


if __name__ == "__main__":
  main(sys.argv[1:])
