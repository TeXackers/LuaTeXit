import time


class BucketFull(Exception):
    """
    Throw when a requested Bucket is already full
    """


class BucketOverFull(BucketFull):
    """
    Throw when a requested Bucket is overfull
    """


class Bucket:
    __slots__ = ("_last_checked", "_last_full", "_level", "empty_time", "leak_rate", "max_level")

    def __init__(self, max_level, empty_time):
        self.max_level = max_level
        self.empty_time = empty_time
        self.leak_rate = max_level / empty_time

        self._level = 0
        self._last_checked = time.time()

        self._last_full = False

    @property
    def overfull(self):
        self._leak()
        return self._level > self.max_level

    def _leak(self):
        if self._level:
            elapsed = time.time() - self._last_checked
            self._level = max(0, self._level - (elapsed * self.leak_rate))

        self._last_checked = time.time()

    def request(self):
        self._leak()
        if self._level + 1 > self.max_level + 1:
            raise BucketOverFull
        if self._level + 1 > self.max_level:
            self._level += 1
            if self._last_full:
                raise BucketOverFull
            self._last_full = True
            raise BucketFull
        self._last_full = False
        self._level += 1
