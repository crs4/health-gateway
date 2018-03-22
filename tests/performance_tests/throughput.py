import time


class Throughput(object):
    """
    >>> t = Throughput(1)
    >>> t.get() == 0
    True
    >>> t.update();t.update(); t.get() == 2
    True
    >>> import time
    >>> time.sleep(1.1)
    >>> t.get() == 0
    True
    """
    def __init__(self, delta):
        self.delta = delta
        self.throughput = 0
        self.last_block = time.time()

    def update(self):
        now = time.time()
        if now - self.last_block > self.delta:
            self.throughput = 1
            self.last_block = now
        else:
            self.throughput += 1

    def get(self):
        if time.time() - self.last_block < self.delta:
            return self.throughput / self.delta
        return 0


if __name__ == "__main__":
    import doctest
    doctest.testmod()
