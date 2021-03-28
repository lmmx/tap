from . import __path__ as _dir_nspath
from pathlib import Path as _Path

_dir_path = _Path(list(_dir_nspath)[0])

_all_programmes = ["today"]
__all__ = ["_dir_path", *_all_programmes, "pid"]

from importlib import import_module

for programme in _all_programmes:
    import_module(f".{programme}", __name__)
    del programme # delete from namespace after iterating over

del import_module # keep this out of namespace too
