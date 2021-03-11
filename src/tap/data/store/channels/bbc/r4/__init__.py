from . import __path__ as _dir_nspath
from pathlib import Path as _Path

_dir_path = _Path(list(_dir_nspath)[0])

_all_programs = ["today"]
__all__ = ["_dir_path", *_all_programs, "pid"]

from importlib import import_module

for program in _all_programs:
    import_module(f".{program}", __name__)
    del program # delete from namespace after iterating over

del import_module # keep this out of namespace too
