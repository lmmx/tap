# dex ⠶ tap

`tap` is an audio transcriber for web radio
(so far just BBC)

## Requirements

The pre-requisites for installation are:

- Python 3
- `tensorflow-gpu`, or `tensorflow` for CPU-only (required for speech segmentation, recommended
  to install via pip)

Dependencies are specified in `requirements.txt`:

- dateutil
- HTTPX (with HTTP/2 support), aiostream, aiofiles
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)
- [inaSpeechSegmenter](https://github.com/ina-foss/inaSpeechSegmenter)
  - Dependency: `sidekit`
    - Forces `matplotlib<3.3.0` due to a deprecation of the
      [`warn` argument to `use`](https://matplotlib.org/stable/api/prev_api_changes/api_changes_3.3.0.html?highlight=deprecations#arguments)
- soundfile
- HuggingFace Transformers for Wav2Vec 2.0 transcription and T5 summarisation
  - The T5 summarisation part has a dependency of SentencePiece

Optional additional dependency (for my use):

- [quill](https://github.com/spin-systems/quill)
  - Website generator driver

### Suggested conda setup

```sh
conda create -y -n tap
conda activate tap
#conda install "cudatoolkit>=11.0,<11.0.221" -c conda-forge
conda install "cudatoolkit<11.2" -c conda-forge
conda install pytorch torchaudio -c pytorch
pip install -r requirements.txt
pip install -e . # or `pip install .` for a fixed installation
# Also run `pip install -e .` for quill if using
```

To install CUDA with conda (and get a managed CUDNN)

```sh
conda create -y -n tap
conda activate tap
conda install cudnn "cudatoolkit<11.2" -c conda-forge
conda install pytorch torchaudio -c pytorch
pip install -r requirements.txt
pip install -e . # or `pip install .` for a fixed installation
# Also run `pip install -e .` for quill if using
```

If using CUDA 11.1 for RTX, you'll also need to hardlink the shared library for `libcusolver`
for TensorFlow to work (for the InaSpeechSegmenter step), as
[documented here](https://github.com/tensorflow/tensorflow/issues/44777)

```sh
cd $CONDA_PREFIX/lib
sudo ln libcusolver.so.11 libcusolver.so.10 # hard link
cd -
```

- Possibly faster to install Intel-optimised Tensorflow via conda(?)

## Usage

### Stream downloading and reloading from disk

For a given program, we can make a `Stream` object with its
URLs for the day's episode, download ("pull"), and segment ("preprocess")
the audio ready for transcription, which we kick off immediately:

```py
from tap.scrape import load_stream
stream = load_stream(transcribe=True)
```

<details><summary>More details</summary>

<p>

- Current default program for `load_stream` is the BBC R4 Today programme.
- Current default value of the `transcribe` argument for `load_stream` is `False`. Setting it to
  `True` will initiate the transcription immediately upon creating the stream object.
- Currently this requires manual provision of the final MP4 segment from inspecting the browser's
  network console (TODO: automate with Selenium)
- To get its URLs for the day before yesterday, pass the `ymd_ago` argument (a tuple)
  e.g. `load_stream(ymd_ago=(0,0,-2))` or pass the `ymd` argument [either a `datetime.date` or an integer tuple
  `(y,m,d)`] for an absolute date e.g. `load_stream(ymd=(2021,2,8))`
- The value for `max_s` is crucial to avoiding an out of memory error when running the model:
  the audio file is first split up based on pauses between speakers, but the `max_s` value (a float)
  sets the maximum number of seconds between the segments (i.e. maximum duration of audio clips
  to be transcribed). Default is 50 seconds based on my experience.

</p>

</details>
  
The `load_stream` function initialises a `Stream` object, and upon doing so the
`Stream.pull()`, `Stream.preprocess()`, and `Stream.transcribe()` methods are called
in sequence, to pull the MP4 stream from its URLs, concatenate into a single output
and convert to WAV at 16 kHz

After this has been done, the transcript timings for each of the segments is stored in a TSV
so that it can be reloaded without having to recompute each time. To reload a stream that's
already been transcribed, use `load_stream(reload=True)` (which will reload the segmented
audio clips, and the transcripts too if they exist), e.g. for the episode 5 days ago:

```py
from tap.scrape import load_stream
stream = load_stream(ymd_ago=(0,0,-5), reload=True)
```

To summarise the transcripts, we can't just merge them all (due to token limits of the language
models which do the summarisation). To merge the first two transcripts from a stream, pass to
`tap.precis.summarise`:

```py
from tap.scrape import load_stream
from tap.precis import summarise
stream = load_stream(ymd_ago=(0,0,-5), reload=True)
all_transcripts = stream.transcript_timings.transcripts.tolist()
some_transcripts = " ".join(all_transcripts[:2])
summary = summarise(some_transcripts)
```

To process an entire stream then, we must summarise it in chunks:

```py
from tap.scrape import load_stream
from tap.precis import summarise_in_chunks
stream = load_stream(ymd=(2021,2,17), reload=True)
all_transcripts = stream.transcript_timings.transcripts.tolist()
summaries, chunk_sizes = summarise_in_chunks(all_transcripts)
```

This is facilitated as a pipeline, writing to a specified output directory

```py
from tap.scrape import load_stream
stream = load_stream(ymd=(2021,2,17), reload=True)
stream.export_transcripts(format="txt", out_dir="/path/to/output/")
```

For my personal use I combine this with `quill`, to build a website:

```py
from tap.scrape import load_stream
stream = load_stream(ymd=(2021,2,17), reload=True)
stream.export_transcripts(out_format="mmd", domain="poll", single_file=True)
```

- The `single_file` option defaults to False, but this creates many files (one per transcript,
  derived from a chunk of one or more audio segments, around 60 per 3 hour program). With
  `single_file=True`, one file `transcript_summaries.mmd` is generated for the web (i.e. a single
  web page).

- There's also a pipeline API version (which loads a 1.22GB _DistilBART_ model,
  [`sshleifer/distilbart-cnn-12-6`](https://huggingface.co/sshleifer/distilbart-cnn-12-6))

- You can also use T5 which works best up to 512 tokens, even though it won't complain until OOM at
  1024 tokens ([source](https://github.com/huggingface/transformers/issues/4224#issuecomment-670550353))

### Preprocessing details

In the final step of preprocessing, the audio is chopped up ("segmented") at 'gaps'
(typically, pauses between speech). This is obtained via the
[INA speech segmenter](https://github.com/ina-foss/inaSpeechSegmenter)

<details><summary>More details</summary>

<p>

First, the audio is labelled as speech/noise/music (by default it will also annotate gender,
which in my experience gives more accurate speaker segmentation). While gender assignment is
not necessary if we are solely interested in the blanks (annotated as `noEnergy`), obtaining
it now means it's unnecessary to recompute later:

This creates a TSV something like this:

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

Given a minimum window (e.g. 10 seconds) we can segment on these "no energy" pauses.
Any smaller segments than this simply get fused together.

Lastly, a Wav2Vec2 model trained for 960h is loaded from the HuggingFace Hub,
and the text produced is annotated onto each segment in the `Stream.transcripts`
attribute (which when set adds a column to the `Stream.transcript_timings` DataFrame).

</p>

</details>

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
