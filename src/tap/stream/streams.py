import beeb
from .transcriber import StreamTranscriberMixIn

__all__ = ["BbcStream"]

class Stream(StreamTranscriberMixIn, base_class):
    def __new__(cls, *args, **kwargs):
        if cls is Stream:
            if args[0] == "bbc":
                _, *args = args
                args = tuple(args)
            elif "broadcaster" in kwargs and kwargs["broadcaster"] == "bbc":
                kwargs.pop("broadcaster")
            else:
                raise NotImplementedError("Only BBC supported")
            cls = BbcStream
        return cls(*args, **kwargs)

class BbcStream(StreamTranscriberMixIn, beeb.stream.Stream):
    def __init__(
        self,
        station,
        programme,
        date,
        urlset,
        defer_pull=False,
        transcribe=False,
        reload=False,
        load_full_transcripts=True,
        **preproc_opts,
    ):
        super().__init__(
            self,
            transcribe=transcribe,
            reload=reload,
            load_full_transcripts=load_full_transcripts,
            **preproc_opts,
        ) # call TranscribeStreamMixIn.__init__
        super(StreamTranscriberMixIn, self).__init__(
            self,
            station,
            programme,
            date,
            urlset,
            defer_pull=defer_pull,
        ) # call base_class.__init__
