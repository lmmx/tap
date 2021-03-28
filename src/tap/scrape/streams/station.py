from beeb.nav import ChannelPicker

__all__ = ["Broadcaster", "Station"]

class Broadcaster:
    def __init__(self, broadcaster):
        self.broadcaster = broadcaster

    @property
    def broadcaster(self):
        return self._broadcaster

    @broadcaster.setter
    def broadcaster(self, c):
        self._broadcaster = c

    @property
    def __broadcaster__(self):
        return f"broadcaster⠶{self.broadcaster}"

    def __repr__(self):
        return self.__broadcaster__

    @property
    def is_bbc(self):
        return self.broadcaster == "bbc"

class Station(Broadcaster):
    def __init__(self, broadcaster , station):
        super().__init__(broadcaster )
        self.station = station

    @property
    def station(self):
        return self._station

    @station.setter
    def station(self, s):
        self._station = s

    @property
    def __station__(self):
        return f"station⠶'{self.station_title}' (id⠶'{self.station_id}')"

    def __repr__(self):
        return self.__station__

    @property
    def beeb_channel(self):
        return ChannelPicker.by_name(self.station) if self.is_bbc else None

    @property
    def station_id(self):
        return self.beeb_channel.channel_id if self.is_bbc else None

    @property
    def station_title(self):
        return self.beeb_channel.title if self.is_bbc else self.station
