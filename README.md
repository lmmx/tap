# dex ⠶ tap

`tap` is an audio transcriber for web radio
(so far just BBC)

## Usage

### Stream downloading

For a given program, we can populate a `Stream` object with its
URLs for the day's episode and download ("pull") them as:

```py
from tap.scrape import load_stream
stream = load_stream()
stream.pull()
```

- Currently this is defaulting to `bbc⠶r4⠶today`
- Currently this requires manual provision of the final MP4 segment from inspecting the browser's
  network console (TODO: automate with Selenium)
- To get its URLs for the day before yesterday, pass the `ymd_ago` argument (a tuple)
  e.g. `load_stream(ymd_ago=(0,0,-2))` or pass the `ymd` argument [either a `datetime.date` or an integer tuple
  `(y,m,d)`] for an absolute date e.g. `load_stream(ymd=(2021,2,8))`
  ```
  
After pulling URLs, concatenate them into a single output:

```sh
for x in assets/*.dash assets/*.m4s; do cat $x >> output.mp4; done
ffmpeg -i output.mp4 -ar 16000 -ac 2 -f wav output.wav
ffmpeg -i output.wav -f segment -segment_time 60 -c copy segmented/output%09d.wav
```

- Currently this must be done on the command line manually (TODO: use `ffmpeg-python`)

### Speaker segmentation

Accurate transcription is heavily reliant on accurate speaker segmentation.
The first step in obtaining this is to obtain the speech segments, which can
be done with [inaSpeechSegmenter](https://github.com/ina-foss/inaSpeechSegmenter).

First, obtain the segmentation of speech/noise/music (by default it will also annotate gender,
which in my experience gives more accurate speaker segmentation):

```sh
mkdir seg_times
ina_speech_segmenter.py -i ./entire_program.wav -o ./seg_times/
```

This will create a file `./seg_times/entire_program.csv` which starts something like this:

```csv
labels  start   stop
male    0.0     1.72
noEnergy        1.72    2.32
male    2.32    19.32
noEnergy        19.32   19.78
male    19.78   38.44
noEnergy        38.44   38.82
male    38.82   39.92
noEnergy        39.92   40.5
male    40.5    59.96
```

The benefit of calculating this once on the entire program is that it's less likely to assign
the "no energy" label to the speech immediately at the beginning of an arbitrarily segmented
audio clip (e.g. previously I split the program into 60 second breaks).

For a given window (e.g. 30 seconds, or 50% of the 60 second target length) we can suggest to
segment on "noEnergy" points. This will give a minimum possible length of 30 seconds and a maximum
length of 60 seconds.

### Catalogue exploration

The namespace of the channels provides an inventory, so running:

```py
from tap import tap.data.store.channels
```

and typing `channels.`<kbd>Tab</kbd> will enumerate the available channels
(i.e. those already stored).

For a given channel, tab completion (in future: command line tab completion)
will give the path to a _channel » station » program_, e.g.

```py
channels.bbc.r4.today
```

(TBC)

## Requirements

The pre-requisites for installation are:

- Python 3
- `tensorflow-gpu`, or `tensorflow` for CPU-only (required for speech segmentation, not recommended
  to install via pip)

Dependencies are specified in `requirements.txt`:

- dateutil
- HTTPX (with HTTP/2 support), aiostream, aiofiles
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)
- [inaSpeechSegmenter](https://github.com/ina-foss/inaSpeechSegmenter)
- soundfile

### Suggested conda setup

```sh
conda create -n tap
conda activate tap
conda install python tensorflow-gpu # or tensorflow for CPU-only
pip install -r requirements.txt
pip install -e . # or `pip install .` for a fixed installation
```
