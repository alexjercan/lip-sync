# Lip Sync

Simple CLI tool to lip sync based on an audio file.

### Dependencies

You will need to have [ffmpeg](https://github.com/FFmpeg/FFmpeg) and
[rhubarb](https://github.com/DanielSWolf/rhubarb-lip-sync) installed to be able
to generate the lip sync.

The tool will use rhubarb to generate the phonemes from the audio file, then it
will use your defined mapping of mouth positions for each phoneme to render a
video file with ffmpeg. The video will contain the audio and it also allows you
to choose a background image (optional). Another optional feature is to add
blinking using a blink mapping. For example you should have the mouth positions
as PNG files with alpha background, and/or blink position, then you should have
your character as a background image.

### Quickstart

For the minimal usage (just the lips)

```console
poetry run lip-sync -- --lipsync sync.csv --audio narration.wav --output output.mkv
```

For the full experience

```console
poetry run lip-sync -- --lipsync sync.csv --blink blink.csv --background bg.png --audio narration.wav --output output.mkv
```

You need to provide the mapping as a csv file. The mapping will contain the
alphabetical order of the phonemes. For example

```csv
A,mouth-mbp.png
B,mouth-sczdntgj.png
C,mouth-kgh.png
...
```

You can check <https://github.com/DanielSWolf/rhubarb-lip-sync> for more
information.

The blink positions are similar. You need to define the following positions:
- A (open)
- B (half)
- C (closed)

You can also set the background, which should be your character (to put the
mouth and blinks on).

The audio file can be in any format. The tool will use ffmpeg to convert it to
`wav` if it is not `wav` or `ogg`. See rhubarb for more information on audio
format.

Finally you have to set the output file, the video that will be generated.
