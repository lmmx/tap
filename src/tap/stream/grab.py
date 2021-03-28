from subprocess import call
from pathlib import Path
from ..data.store.broadcasters import _dir_path as data_dir
from ..share.cal import cal_path, cal_shift, cal_date, parse_abs_from_rel_date
from .streams import Stream

from .stream_dir_prep import ensure_stream_dir
from beeb.api import final_m4s_link_from_programme_pid
from beeb.nav import ProgrammeCatalogue
from beeb.stream.urlsets import StreamUrlSet

__all__ = ["load_stream"]

def ensure_stream_dir(link_dir_path, broadcaster, station, programme_pid, cal_subpath):
    "The function of this is to create a directory"
    if not link_dir_path.exists():
        raise FileNotFoundError(f"{link_dir_path} not found")
    link_file_dir = link_dir_path / broadcaster / station / programme_pid / cal_subpath
    link_file_dir.mkdir(parents=True, exist_ok=True)

def load_stream(
    broadcaster="bbc", station="r4", programme="Today", ymd=None, ymd_ago=None, **stream_opts
):
    """
    Create a `Stream` for a specific episode of a radio programme from the named arguments
    and pass `stream_opts` through.

    `ymd` and `ymd_ago` are options to specify either an absolute
    or relative date as `(year, month, day)` tuple of 3 integers in both cases.
    `ymd` defaults to today's date and `ymd_ago` defaults to `(0,0,0)`.

    `stream_opts` include:
    - `transcribe=False` to determine whether the `Stream.transcribe`
      method is called upon initialisation
    - `reload=False` to control whether to reload the stream from disk
    - `min_s=5.`/`max_s=50.` to control the min./max. audio segment length.

    If `reload` is True, do not pull/preprocess/transcribe: the transcripts are expected
    to already exist on disk, so just load them from there and recreate the `Stream`.
    """
    ymd = parse_abs_from_rel_date(ymd, ymd_ago)
    cal_subpath = cal_path(ymd)
    prog_date_dir = data_dir / broadcaster / station / programme / cal_subpath
    # This step obtains the episode PID and uses this to obtain the last M4S stream URL
    if broadcaster != "bbc":
        raise NotImplementedError("Only currently supporting BBC stations")
    programme_pid = ProgrammeCatalogue.lazy_generate(station).get_programme_by_title(
        programme, pid_only=True
    )
    
    ymd_parts = [*map(lambda p: int(p[:2]), ymd)]
    y2k_y, m, d = ymd_parts
    # Convert internal date to explicitly post-Y2K Y
    y2k_y += 2000
    y2k_ymd = tuple(y2k, m, d)

    last_link_url = final_m4s_link_from_programme_pid(programme_pid, ymd=y2k_ymd)
    ensure_stream_dir(data_dir, broadcaster, station, programme_pid, cal_subpath)
    urlset = StreamUrlSet.from_last_m4s_url(last_link_url)
    stream = Stream(broadcaster, station, programme, ymd, urlset, **stream_opts)
    return stream
