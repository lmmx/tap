from . import __path__ as _dir_nspath
from pathlib import Path as _Path

_dir_path = _Path(list(_dir_nspath)[0])

__all__ = ["_dir_path"]
