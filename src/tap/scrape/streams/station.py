from beeb.nav import ChannelPicker

__all__ = ["Channel", "Station"]

class Channel:
    def __init__(self, channel):
        self.channel = channel

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, c):
        self._channel = c

    @property
    def __channel__(self):
        return f"channel⠶{self.channel}"

    def __repr__(self):
        return self.__channel__

    @property
    def is_bbc(self):
        return self.channel == "bbc"

class Station(Channel):
    def __init__(self, channel, station):
        super().__init__(channel)
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
