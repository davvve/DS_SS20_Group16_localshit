import threading


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(
            name=self.__class__.__name__, *args, **kwargs
        )
        self._stop_event = threading.Event()
        self._interval = 1

    def setup(self):
        """Can be overwritten."""
        pass

    def clean_up(self):
        """Can be overwritten."""
        pass

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        self.setup()
        while not self._stop_event.is_set():
            self.work_func()
        self.clean_up()

    def work_func(self):
        raise NotImplementedError
