# Lip Sync

Simple CLI tool to lip sync based on an audio file.

### Dependencies

You will need to have [ffmpeg](https://github.com/FFmpeg/FFmpeg) and
[rhubarb](https://github.com/DanielSWolf/rhubarb-lip-sync) installed to be able
to generate the lip sync.

The tool will use rhubarb to generate the phonemes from the audio file, then it
will use your defined mapping of mouth positions for each phoneme to render a
video file with ffmpeg. The video will contain the audio and it also allows you
to choose a background image. For example you should have the mouth positions
as PNG files with alpha background, then you should have your character as a
background image.

### Quickstart

```console
poetry run lip-sync -- --mapping sync.csv --output output.mkv --background bg.png --audio narration.wav
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

You also have to set the background, which should be your character (to put the
mouth on).

Also you need to specify the speech file as a `wav` or `ogg` see rhubarb for
more information on that.

Finally you have to set the output file, the video that will be generated.
