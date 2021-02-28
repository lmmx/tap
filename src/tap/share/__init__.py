from . import cal, audio, multiproc, pandas
from .torch_utils import *

from . import __path__ as _dir_nspath
from pathlib import Path as _Path

__all__ = ["_dir_path", "pkg_path"]

_dir_path = _Path(list(_dir_nspath)[0])
pkg_path = _dir_path.parent
