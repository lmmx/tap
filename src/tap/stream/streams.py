import beeb
from .transcriber import StreamTranscriberMixIn

__all__ = ["Stream"]

class TapHandle:
    "Decorator class to modify `_root_store_dir` of stream class"
    _root_store_dir = StreamTranscriberMixIn._root_store_dir

class Stream(StreamTranscriberMixIn):
    def __init__(
        self,
        programme,
        station,
        broadcaster="bbc",
        ymd=None,
        ymd_ago=None,
        defer_pull=False,
        transcribe=True,
        reload=True,
        load_full_transcripts=True,
        **preproc_opts,
    ):
        custom_storage_root = self._root_store_dir / broadcaster
        if broadcaster == "bbc":
            self._source = beeb.stream.Stream.from_name(
                station=station,
                programme_name=programme,
                ymd=ymd,
                ymd_ago=ymd_ago,
                defer_pull=defer_pull,
                custom_storage_path=custom_storage_root,
            )
        else:
            msg = f"Only broadcaster='bbc' supported (not {broadcaster=})"
            raise NotImplementedError(msg)
        super().__init__(
            transcribe=transcribe,
            reload=reload,
            load_full_transcripts=load_full_transcripts,
            **preproc_opts,
        )  # call TranscribeStreamMixIn.__init__
