from .async_utils import fetch_urls
from ..share.cal import cal_path
from ..preproc.merge import gather_pulled_downloads
from ..preproc.format_conversion import mp4_to_wav
from ..preproc.segment import segment_pauses_and_spread
from ..stt import transcribe_audio_file
from ..data.store import channels
from ..precis.summary_exporters import DocSummaryExportEnum
import asyncio
from functools import reduce
from glob import glob
from pathlib import Path
from sys import stderr
from tqdm import tqdm
from pandas import read_csv

class Channel:
    def __init__(self, channel):
        self.channel = channel

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, c):
        self._channel = c

    @property
    def __channel__(self):
        return f"channel⠶{self.channel}"

    def __repr__(self):
        return self.__channel__

class Station(Channel):
    def __init__(self, channel, station):
        super().__init__(channel)
        self.station = station

    @property
    def station(self):
        return self._station

    @station.setter
    def station(self, s):
        self._station = s

    @property
    def __station__(self):
        return f"station⠶{self.station} on {self.__channel__}"

    def __repr__(self):
        return self.__station__

class Program(Station):
    def __init__(self, channel, station, program):
        super().__init__(channel, station)
        self.program = program

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, p):
        self._program = p

    @property
    def program_parts(self):
        return self.channel, self.station, self.program

    @property
    def program_dir(self):
        return reduce(getattr, self.program_parts, channels)._dir_path

    @property
    def __program__(self):
        return f"program⠶{self.program} on {self.__station__}"

    def __repr__(self):
        return self.__program__

class Episode(Program):
    def __init__(self, channel, station, program, date):
        super().__init__(channel, station, program)
        self.date = date

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, d):
        self._date = d

    @property
    def episode_dir(self):
        return self.program_dir / cal_path(self.date)

    @property
    def download_dir(self):
        return self.episode_dir / "assets"

    @property
    def __episode__(self):
        return f"episode⠶{self.date} of {self.__program__}"

    def __repr__(self):
        return self.__episode__

class Stream(Episode):
    def __init__(self, channel, station, program, date, urlset, transcribe=False,
            reload=False, load_full_transcripts=True, **preproc_opts):
        # Set repr and directory properties for channel, station, program, episode, date
        super().__init__(channel, station, program, date)
        self.stream_urls = urlset
        self.full_text_transcripts_loaded = False
        if reload:
            self.reload_transcripts()
        else:
            self.pull()
            self.preprocess(**preproc_opts)
            if transcribe:
                self.transcribe() # Can also pass in model_to_load or `just_filenames`
        try:
            # Load texts into `transcript_timings` DataFrame
            # pass `full_text=True` to load the transcript text into memory
            self.load_transcript_text(full_text=load_full_transcripts)
        except Exception as e:
            print("Non-fatal error while trying to reload transcripts", file=stderr)

    @property
    def stream_urls(self):
        return self._stream_urls

    @stream_urls.setter
    def stream_urls(self, u):
        self._stream_urls = u

    @property
    def stream_len(self):
        return self.stream_urls.size

    @property
    def __stream__(self):
        return f"stream⠶{self.stream_urls} from {self.__episode__}"

    def __repr__(self):
        return self.__stream__

    @property
    def transcripts(self):
        return self._transcripts

    @transcripts.setter
    def transcripts(self, transcripts):
        self._transcripts = transcripts
        if hasattr(self, "transcript_timings"):
            # Set a column on the segment_times dataframe with the transcript text
            try:
                self.segment_times["transcript"] = transcripts
            except Exception as e:
                print(e, file=stderr) # Errors break entire object initialisation

    def pull(self, verbose=False):
        if verbose:
            print(f"Pulling {self.stream_urls}")
        urls = self.stream_urls
        last_url = self.stream_urls.make_part_url(urls.size)
        last_url_file = self.download_dir / Path(str(last_url)).name
        if not last_url_file.exists():
            pbar = tqdm(total=urls.size)
            fetch_urls(urls, download_dir=self.download_dir, pbar=pbar, verbose=verbose)
        if verbose:
            print("Done")
        return

    def preprocess(self, **opts):
        """
        Gather stream files into a single MP4 file, convert to WAV, segment it
        at pauses in the audio, and create smaller WAV files accordingly.

        Any kwargs passed as `opts` are passed into `segment_pauses_and_spread`
        (from the `tap.preproc.segment.inaseg` module). These are by default:
        `csv_out_dir=None`, `segmented_out_dir=None`, `min_s=5.0`, `max_s=50.0`.
        The latter pair control the minimum and maximum segment length (if you
        encounter out of memory errors while running Wav2Vec2, reduce `max_s`,
        which will cause further segmenting at the audio's minimum amplitude
        points to bring each segment below this limit).
        """
        transcoded_wav = self.episode_dir / "output.wav"
        if not transcoded_wav.exists():
            gathered_mp4 = gather_pulled_downloads(self.download_dir, self.episode_dir)
            transcoded_wav = mp4_to_wav(gathered_mp4)
        self.transcript_timings, self.segment_dir = segment_pauses_and_spread(transcoded_wav, **opts)
        self.set_transcript_timings_config()
        self.transcript_timings.to_csv(self.txn_tsv, **self._txn_tsv_w_opts)

    def set_transcript_timings_config(self):
        """
        Create any necessary directories
        """
        self.txn_tsv = self.episode_dir / "segment_times.tsv"
        self._txn_tsv_r_opts = {"sep": "\t", "quoting": 2}
        self._txn_tsv_w_opts = {**self._txn_tsv_r_opts, "index": False}
        self._txn_tsv_r_col_map_opts = {"input": Path, "output": Path}

    def reload_transcripts(self):
        """
        Set the `segment_dir` and `transcript_dir` attributes which were otherwise
        provided by a call to `segment_pauses_and_spread` in the `preprocess` method.
        
        Reload the `transcript_timings` DataFrame (with very small floating point
        error from original values).
        """
        if not hasattr(self, "segment_dir"):
            self.segment_dir = self.episode_dir / "segmented"
        if not hasattr(self, "transcript_dir"):
            self.transcript_dir = self.segment_dir / "transcripts"
        self.set_transcript_timings_config()
        self.transcript_timings = read_csv(self.txn_tsv, **self._txn_tsv_r_opts)
        for col, mappable in self._txn_tsv_r_col_map_opts.items():
            self.transcript_timings[col] = self.transcript_timings[col].map(mappable)

    def load_transcript_text(self, full_text=True):
        """
        To not load the transcript text itself into memory (instead just store the file
        paths to the transcripts) set `full_text` to False (default: True).
        """
        transcripts = []
        self.full_text_transcripts_loaded = full_text
        for wav in self.transcript_timings.output:
            transcript_filename = wav.stem + ".txt"
            transcript = self.transcript_dir / transcript_filename
            if full_text:
                with open(transcript, "r") as f:
                    txt = f.read().rstrip("\n")
                transcripts.append(txt)
            else:
                transcripts.append(transcript)
        self.transcript_timings["transcripts"] = transcripts

    def transcribe(self, model_to_load="facebook/wav2vec2-base-960h"):
        files_to_transcribe = sorted(glob(str(self.segment_dir / "*.wav")))
        # Setting `.transcripts` attr adds `transcript` column to `.transcript_timings`
        print(f"Transcribing {len(files_to_transcribe)} segmented audio files", file=stderr)
        self.transcript_dir = self.segment_dir / "transcripts"
        self.transcript_dir.mkdir(exist_ok=True)
        for f in tqdm(files_to_transcribe):
            transcript = transcribe_audio_file(f, model_to_load)
            transcript_filename = Path(f).stem + ".txt"
            with open(self.transcript_dir / transcript_filename, "w") as fh:
                fh.write(transcript+"\n")

    def export_transcripts(self, out_format="txt", out_dir=None, domain=None, single_file=False):
        """
        If `out_format` is "txt" (default) the transcripts are exported as plain text,
        if `out_format` is "md" they are converted to GitHub-flavoured markdown (using
        `<details>` blocks to display a collapsed view of the full transcripts and 
        `<summary>` tags to display the associated summary text).
        if `out_format` is "mmd" they are converted to quill’s lever MMD format
        (specifically designed for transcripts, particularly when clauses are split
        on conjunctives).
        """
        dir_sep = "_"
        program_dirname = dir_sep.join(["tap", *self.program_parts])
        if domain:
            try:
                from quill import AddressPath
            except (ImportError, ModuleNotFoundError) as e:
                raise type(e)(
                    f"quill must be installed to export transcripts to domains\n{e.msg}"
                )
            ymd = [*self.date.timetuple()][:3]
            out_dir = AddressPath.from_parts(domain=domain, ymd=ymd).filepath
        elif out_dir is None:
            raise ValueError("No output directory supplied for transcript export")
        out_dir = out_dir / program_dirname
        if out_format not in DocSummaryExportEnum.__members__:
            raise ValueError(f"{out_format} is not a valid DocSummaryExportEnum")
        if not self.full_text_transcripts_loaded:
            self.load_transcript_text(full_text=True)
        all_transcripts = self.transcript_timings.transcripts.tolist()
        summary_exporter = DocSummaryExportEnum[out_format].value
        print(f"Exporting {len(all_transcripts)} transcripts to {out_dir}", file=stderr)
        exporter = summary_exporter(documents=all_transcripts, to=out_dir)
        wire_mmt_config = exporter.wire_post_hook(single_file=single_file)
        # TODO: `meta.mmt` too with `[schedule]` and `[via]`
        if wire_mmt_config:
            with open(out_dir / "wire.mmt", "w") as f:
                f.write(wire_mmt_config)
