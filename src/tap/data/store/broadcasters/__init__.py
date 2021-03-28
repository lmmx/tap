from . import __path__ as _dir_nspath
from pathlib import Path as _Path

_dir_path = _Path(list(_dir_nspath)[0])

_all_broadcasters = ["bbc"]
__all__ = ["_dir_path", *_all_broadcasters]

from importlib import import_module

for broadcaster in _all_broadcasters:
    import_module(f".{broadcaster}", __name__)

del broadcaster # delete from namespace after iterating over
del import_module # keep this out of namespace too
