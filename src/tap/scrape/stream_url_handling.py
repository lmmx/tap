from functools import partial

__all__ = ["StreamPartURL", "construct_urlset", "StreamUrlSet"]

class EpisodeStreamPartURL:
    def __init__(self, url_prefix, filename_prefix, filename_sep, url_suffix):
        self.url_prefix = url_prefix
        self.filename_prefix = filename_prefix
        self.filename_sep = filename_sep
        self.url_suffix = url_suffix

    #def __repr__(self):
    #    return f"{self.url_prefix}{self.filename_prefix}(...){self.url_suffix}"

    def make_init_url(self, url_suffix=".dash"):
        return StreamInitURL(self.url_prefix, self.filename_prefix, self.filename_sep, url_suffix)

    def make_part_url(self, int_i):
        return StreamPartURL(int_i, self.zfill, self.url_prefix, self.filename_prefix, self.filename_sep, self.url_suffix)

class StreamInitURL(EpisodeStreamPartURL):
    def __repr__(self):
        return f"{self.url_prefix}{self.filename_prefix}{self.url_suffix}"

class StreamPartURL(EpisodeStreamPartURL):
    def __init__(self, int_i, zfill, url_prefix, filename_prefix, filename_sep, url_suffix):
        super().__init__(url_prefix, filename_prefix, filename_sep, url_suffix)
        self.zfill = zfill
        self.int_i = int_i

    @property
    def str_i(self):
        return str(self.int_i).zfill(self.zfill)

    def __repr__(self):
        return f"{self.url_prefix}{self.filename_prefix}{self.filename_sep}{self.str_i}{self.url_suffix}"
        return self.url_prefix + self.filename_prefix + self.str_i + self.url_suffix


class StreamUrlSet(EpisodeStreamPartURL):
    def __init__(self, size, url_prefix, filename_prefix, filename_sep, url_suffix, zero_based=False, zfill=True):
        super().__init__(url_prefix, filename_prefix, filename_sep, url_suffix)
        self.size = size # class is an iterator not a list so record size
        self.zfill = len(str(size)) if zfill else 0
        self.zero_based = zero_based
        self.reset_pos()
        self.is_initialised = False

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, n):
        self._size = n

    @property
    def pos_end(self):
        return self.size if self.zero_based else self.size + 1

    def reset_pos(self):
        self.pos = 0 if self.zero_based else 1

    def increment_pos(self):
        self.pos += 1

    def __repr__(self):
        return f"{self.size} URLs"

    def __iter__(self):
        return next(self)

    def __next__(self):
        while not self.is_initialised:
            self.is_initialised = True
            yield self.make_init_url()
        while self.pos < self.pos_end:
            p = self.pos
            self.increment_pos()
            yield self.make_part_url(p)


def construct_urlset(int_i, url_prefix, filename_prefix, filename_sep, url_suffix):
    episode_urls = StreamUrlSet(
        size=int_i,
        url_prefix=url_prefix,
        filename_prefix=filename_prefix,
        filename_sep=filename_sep,
        url_suffix=url_suffix,
    )
    return episode_urls
    #return [episode_url_base.make_part_url(int_i=i) for i in range(1, int_i + 1)]
