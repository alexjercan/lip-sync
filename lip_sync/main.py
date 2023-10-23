"""Lip Sync from audio file"""
import argparse
import csv
import io
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import ffmpeg


def run_rhubarb(audio: str) -> Optional[List[Tuple[str, float]]]:
    """Run the rhubarb cli tool to generate the phoneme's

    This function will work only with `.wav` or `.ogg` audio formats. This is
    how rhubarb works. And could be fixed in the future.

    It will generate a list with tuple elements. Each tuple will contain the
    alphabetical name of the phoneme (A-H,X) and the duration of that phoneme.

    Example
    -------
    > run_rhubarb("some_file.wav")
    [("A", 0.56), ("X", 1.2), ...]

    Parameters
    ----------
    audio : str
        The path to the audio file to use

    Return
    Optional[List[Tuple[str, float]]]
        The chunks as a list of tuples of names and durations
    """
    try:
        result = subprocess.run(
            ["rhubarb", "-q", audio],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            text=True,
            check=True,
        )
        sync = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None

    frames = []
    rd = csv.reader(io.StringIO(sync), delimiter="\t")
    for time, name in rd:
        frames.append((float(time), name))

    chunks = []
    for i in range(len(frames) - 1):
        stamp, name = frames[i]
        next_stamp, _ = frames[i + 1]

        duration = next_stamp - stamp
        chunks.append((name, duration))

    return chunks


def generate_video(
    chunks: List[Tuple[str, float]], audio: str, background: str, output: str
):
    """Run ffmpeg to generate the video from the chunks

    Parameters
    ----------
    chunks : List[Tuple[str, float]]
        The chunks containing the path to the images and the duration
    audio : str
        The path to the audio file
    background : str
        The path to the background image
    output : str
        The path to the output video file
    """
    ffmpeg.overlay(
        ffmpeg.input(background),
        ffmpeg.concat(
            *[
                ffmpeg.input(image, loop=1, t=duration)
                for i, (image, duration) in enumerate(chunks)
            ],
        ),
    ).output(
        ffmpeg.input(audio), output, vcodec="qtrle", pix_fmt="argb"
    ).overwrite_output().run()


@dataclass
class Args:
    """The arguments of the application

    Attributes
    ----------
    mapping : str
        The path to the file that contains the mapping from phoneme to png path
    audio : str
        The path to the audio file that will be used to perform lip sync
    background : str
        The path to the file that will be used as a background image under the pngs
    output : str
        The name of the output file, will be a mkv video file
    """

    mapping: str
    audio: str
    background: str
    output: str


def parse_args() -> Args:
    """Parse the arguments of the application

    Returns
    -------
    Args
        The arguments of the application
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mapping", type=str, help="path to the mapping file", required=True
    )
    parser.add_argument(
        "--audio",
        type=str,
        help="path to the audio file to use to lip sync",
        required=True,
    )
    parser.add_argument(
        "--background",
        type=str,
        help="path to the background file (image or video)",
        required=True,
    )
    parser.add_argument(
        "--output", type=str, help="name of the output file", required=True
    )

    args = parser.parse_args()

    return Args(
        mapping=args.mapping,
        audio=args.audio,
        background=args.background,
        output=args.output,
    )


def main():
    """Entry Point"""
    args = parse_args()

    chunks = run_rhubarb(args.audio)
    assert chunks is not None, "Could not generate the chunks"

    lips = {}
    mapping_path = Path(args.mapping)
    with open(mapping_path, "r", encoding="utf-8") as fd:
        rd = csv.reader(fd)
        for name, file in rd:
            lips[name] = os.path.join(mapping_path.parent, file)

    for i, (name, duration) in enumerate(chunks):
        chunks[i] = (lips[name], duration)

    generate_video(chunks, args.audio, args.background, args.output)
