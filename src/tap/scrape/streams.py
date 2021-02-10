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
        return f"station⠶{self.station} on {self.__channel__}"

    def __repr__(self):
        return self.__station__

class Program(Station):
    def __init__(self, channel, station, program):
        super().__init__(channel, station)
        self.program = program

    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, p):
        self._program = p

    @property
    def __program__(self):
        return f"program⠶{self.program} on {self.__station__}"

    def __repr__(self):
        return self.__program__

class Episode(Program):
    def __init__(self, channel, station, program, date):
        super().__init__(channel, station, program)
        self.date = date

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, d):
        self._date = d

    @property
    def __episode__(self):
        return f"episode⠶{self.date} of {self.__program__}"

    def __repr__(self):
        return self.__episode__

class Stream(Episode):
    def __init__(self, channel, station, program, date, urlset):
        super().__init__(channel, station, program, date)
        self.stream_urls = urlset

    @property
    def stream_urls(self):
        return self._stream_urls

    @stream_urls.setter
    def stream_urls(self, u):
        self._stream_urls = u

    @property
    def stream_len(self):
        return self.stream_urls.size

    @property
    def __stream__(self):
        return f"stream⠶{self.stream_urls} from {self.__episode__}"

    def __repr__(self):
        return self.__stream__
