from . import __path__ as _dir_nspath
from pathlib import Path as _Path

_dir_path = _Path(list(_dir_nspath)[0])

_all_channels = ["bbc"]
__all__ = ["_dir_path", *_all_channels]

from importlib import import_module

for channel in _all_channels:
    import_module(f".{channel}", __name__)

del channel # delete from namespace after iterating over
del import_module # keep this out of namespace too
