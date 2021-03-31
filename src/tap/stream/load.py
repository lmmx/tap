from ..share.cal import parse_abs_from_rel_date
from .streams import Stream

__all__ = ["load_stream"]


def load_stream(
    programme="Today",
    station="r4",
    broadcaster="bbc",
    ymd=None,
    ymd_ago=None,
    **stream_opts,
):
    """
    Create a `Stream` for a specific episode of a radio programme from the named
    arguments and pass `stream_opts` through.

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
    if broadcaster != "bbc":
        raise NotImplementedError("Only currently supporting BBC stations")
    date = parse_abs_from_rel_date(ymd=ymd, ymd_ago=ymd_ago)
    ymd = (date.year, date.month, date.day)
    stream = Stream(programme, station, broadcaster, ymd, **stream_opts)
    return stream
