from collections import deque
from threading import Lock


class LiveBuffer:

    def __init__(self, max_size=1000):
        self.data = deque(maxlen=max_size)
        self.lock = Lock()

    def add(self, reading):
        with self.lock:
            self.data.append(reading)

    def latest(self):
        with self.lock:
            if not self.data:
                return None

            return self.data[-1]

    def get_all(self):
        with self.lock:
            return list(self.data)

    def get_latest(self, count=100):
        with self.lock:
            if count <= 0:
                return []

            return list(self.data)[-count:]

    def size(self):
        with self.lock:
            return len(self.data)

    def clear(self):
        with self.lock:
            self.data.clear()


# Global buffer used by the live-data system
live_buffer = LiveBuffer(max_size=1000)