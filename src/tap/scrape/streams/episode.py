from .station import Station
from ...share.cal import cal_path
from ...data.store import broadcaster
from functools import reduce

__all__ = ["Program", "Episode"]

class Program(Station):
    def __init__(self, broadcaster, station, programme):
        super().__init__(broadcaster, station)
        self.programme = programme

    @property
    def programme(self):
        return self._programme

    @programme.setter
    def programme(self, p):
        self._programme = p

    @property
    def programme_parts(self):
        return self.broadcaster, self.station, self.programme

    @property
    def programme_dir(self):
        return reduce(getattr, self.programme_parts, broadcaster)._dir_path

    @property
    def __programme__(self):
        return f"programme⠶{self.programme} on {self.__station__}"

    def __repr__(self):
        return self.__programme__


class Episode(Program):
    def __init__(self, broadcaster, station, programme, date):
        super().__init__(broadcaster, station, programme)
        self.date = date

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, d):
        self._date = d

    @property
    def episode_dir(self):
        return self.programme_dir / cal_path(self.date)

    @property
    def download_dir(self):
        return self.episode_dir / "assets"

    @property
    def __episode__(self):
        return f"episode⠶{self.date} of {self.__programme__}"

    def __repr__(self):
        return self.__episode__
