from . import __path__ as _dir_nspath
from .channel_ids import ChannelPicker
from pathlib import Path as _Path

_dir_path = _Path(list(_dir_nspath)[0])

_all_stations = ["r4"]
__all__ = ["_dir_path", "channel_ids", *_all_stations]

from importlib import import_module

for station in _all_stations:
    import_module(f".{station}", __name__)

del station # delete from namespace after iterating over
del import_module # keep this out of namespace too
