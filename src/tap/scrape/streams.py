from .async_utils import fetch_urls
from ..share.cal import cal_path
from ..preproc.merge import gather_pulled_downloads
from ..preproc.format_conversion import mp4_to_wav
from ..preproc.segment import segment_pauses_and_spread
from ..stt import transcribe_audio_file
from ..data.store import channels
import asyncio
from functools import reduce
from glob import glob
from pathlib import Path
from sys import stderr
from tqdm import tqdm

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
    def __init__(self, channel, station, program, date, urlset):
        super().__init__(channel, station, program, date)
        self.stream_urls = urlset
        self.pull()
        self.preprocess()
        self.transcribe()

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

    def preprocess(self):
        """
        Gather stream files into a single MP4 file, convert to WAV, segment it
        at pauses in the audio, and create smaller WAV files accordingly.
        """
        transcoded_wav = self.episode_dir / "output.wav"
        if not transcoded_wav.exists():
            gathered_mp4 = gather_pulled_downloads(self.download_dir, self.episode_dir)
            transcoded_wav = mp4_to_wav(gathered_mp4)
        self.transcript_timings, self.segment_dir = segment_pauses_and_spread(transcoded_wav)

    def transcribe(self):
        files_to_transcribe = sorted(glob(str(self.segment_dir / "*.wav")))
        # Setting `.transcripts` attr adds `transcript` column to `.transcript_timings`
        self.transcripts = [*map(transcribe_audio_file, files_to_transcribe)]
