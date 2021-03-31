import beeb
from .transcriber import StreamTranscriberMixIn

__all__ = ["Stream"]


class Stream(StreamTranscriberMixIn):
    def __init__(
        self,
        programme,
        station,
        broadcaster="bbc",
        ymd=None,
        ymd_ago=None,
        defer_pull=False,
        transcribe=False,
        reload=False,
        load_full_transcripts=True,
        **preproc_opts,
    ):
        if broadcaster == "bbc":
            self._source = beeb.stream.Stream.from_name(
                station=station,
                programme_name=programme,
                ymd=ymd,
                ymd_ago=ymd_ago,
                defer_pull=defer_pull
            )
        else:
            print(broadcaster)
            raise NotImplementedError("Only BBC supported")
        super().__init__(
            transcribe=transcribe,
            reload=reload,
            load_full_transcripts=load_full_transcripts,
            **preproc_opts,
        )  # call TranscribeStreamMixIn.__init__
