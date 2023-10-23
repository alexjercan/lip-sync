"""Lip Sync from audio file"""
import argparse
import csv
import io
import os
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import ffmpeg


def run_rhubarb(audio: str, lipsync: str) -> Optional[List[Tuple[str, float]]]:
    """Run the rhubarb cli tool to generate the phoneme's

    This function will work only with `.wav` or `.ogg` audio formats. This is
    how rhubarb works. For other formats, it will convert the audio file to
    `.wav` format and then run rhubarb. The converted file name will be the
    same as the original file but with the `.wav` extension. For example, if
    the audio file is `some_file.mp3`, the converted file will be
    `some_file.mp3.wav`. This will automatically overwrite any existing file
    with the same name. If you want to keep the original file, make a copy of
    it before running this function.

    It will generate a list with tuple elements. Each tuple will contain the
    path to the PNG file and the duration of that phoneme.

    Example
    -------
    > run_rhubarb("some_file.wav")
    [("a.png", 0.56), ("closed.png", 1.2), ...]

    Parameters
    ----------
    audio : str
        The path to the audio file to use
    lipsync : str
        The path to the lipsync file

    Returns
    -------
    Optional[List[Tuple[str, float]]]
        The chunks as a list of tuples of png files and durations
    """
    if not audio.endswith(".wav") and not audio.endswith(".ogg"):
        audio_wav = audio + ".wav"
        ffmpeg.input(audio).output(audio_wav).overwrite_output().run()
        audio = audio_wav

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

    lips = {}
    lipsync_path = Path(lipsync)
    with open(lipsync_path, "r", encoding="utf-8") as fd:
        rd = csv.reader(fd)
        for name, file in rd:
            lips[name] = os.path.join(lipsync_path.parent, file)

    for i, (name, duration) in enumerate(chunks):
        chunks[i] = (lips[name], duration)

    return chunks


def run_blink(
    audio: str, blink: Optional[str], min_wait: float = 2.0, max_wait: float = 4.0
) -> Optional[List[Tuple[str, float]]]:
    """Run the blink cli tool to generate the blink's

    Parameters
    ----------
    audio : str
        The path to the audio file to use
    blink : str
        The path to the blink file
    min_wait : float
        The minimum time to wait between blinks
    max_wait : float
        The maximum time to wait between blinks

    Example
    -------
    > run_blink("some_file.wav", "blink.csv")
    [("open.png", 2.56), ("closed.png", 0.04), ...]

    Returns
    -------
    Optional[List[Tuple[str, float]]]
        The chunks as a list of tuples of names and durations
    """
    if blink is None:
        return None

    duration = float(ffmpeg.probe(audio)["format"]["duration"])

    chunks = []
    while duration > 0:
        wait = random.uniform(min_wait, max_wait)
        if wait > duration:
            wait = duration

        chunks.extend([("A", wait), ("B", 1 / 24), ("C", 1 / 24)])
        duration -= wait + 2 / 24

    blinks = {}
    blink_path = Path(blink)
    with open(blink_path, "r", encoding="utf-8") as fd:
        rd = csv.reader(fd)
        for name, file in rd:
            blinks[name] = os.path.join(blink_path.parent, file)

    for i, (name, duration) in enumerate(chunks):
        chunks[i] = (blinks[name], duration)

    return chunks


def generate_video(
    lip_chunks: List[Tuple[str, float]],
    blink_chunks: Optional[Tuple[str, float]],
    audio: str,
    background: Optional[str],
    output: str,
):
    """Run ffmpeg to generate the video from the chunks

    Parameters
    ----------
    lip_chunks : List[Tuple[str, float]]
        The chunks containing the path to the images and the duration
    blink_chunks : Optional[List[Tuple[str, float]]]
        The chunks containing the path to the blink images and the duration;
        if none it will not use blink
    audio : str
        The path to the audio file
    background : Optional[str]
        The path to the background image;
        if none it will not use a background image
    output : str
        The path to the output video file
    """
    pipe = ffmpeg.concat(
        *[
            ffmpeg.input(image, loop=1, t=duration)
            for i, (image, duration) in enumerate(lip_chunks)
        ],
    )

    if background is not None:
        pipe = ffmpeg.overlay(
            ffmpeg.input(background),
            pipe,
        )

    if blink_chunks is not None:
        pipe = ffmpeg.overlay(
            pipe,
            ffmpeg.concat(
                *[
                    ffmpeg.input(image, loop=1, t=duration)
                    for i, (image, duration) in enumerate(blink_chunks)
                ],
            ),
        )

    pipe.output(
        ffmpeg.input(audio), output, vcodec="qtrle", pix_fmt="argb"
    ).overwrite_output().run()


@dataclass
class Args:
    """The arguments of the application

    Attributes
    ----------
    lipsync : str
        The path to the file that contains the mapping from phoneme to png path
    blink : Optional[str]
        The path to the file that contains the blink stages of the character
    audio : str
        The path to the audio file that will be used to perform lip sync
    background : str
        The path to the file that will be used as a background image under the pngs
    output : str
        The name of the output file, will be a mkv video file
    """

    lipsync: str
    blink: Optional[str]
    audio: str
    background: Optional[str]
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
        "--lipsync", type=str, help="path to the mapping file", required=True
    )
    parser.add_argument(
        "--blink", type=str, help="path to the blink file", required=False
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
        required=False,
    )
    parser.add_argument(
        "--output", type=str, help="name of the output file", required=True
    )

    args = parser.parse_args()

    return Args(
        lipsync=args.lipsync,
        blink=args.blink,
        audio=args.audio,
        background=args.background,
        output=args.output,
    )


def main():
    """Entry Point"""
    args = parse_args()

    lip_chunks = run_rhubarb(args.audio, args.lipsync)
    assert lip_chunks is not None, "Could not generate the chunks"

    blink_chunks = run_blink(args.audio, args.blink)

    generate_video(lip_chunks, blink_chunks, args.audio, args.background, args.output)
