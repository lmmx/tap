from . import cal

from . import __path__ as _dir_nspath
from pathlib import Path as _Path

__all__ = ["dir_path", "pkg_path"]

dir_path = _Path(list(_dir_nspath)[0])
pkg_path = dir_path.parent
