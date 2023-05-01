from signal import getsignal, SIGINT, signal
from threading import Event


class WaitHandler:
    def __init__(self):
        self.original_sigint_handler = getsignal(SIGINT)
        self.event = Event()
        signal(SIGINT, self._stop)

    def __del__(self):
        signal(SIGINT, self.original_sigint_handler)

    def wait(self, seconds: int):
        self.event.wait(seconds)

    def _stop(self, _signalNumber, _):
        self.event.set()
        self.event.clear()
