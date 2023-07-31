from typing import Callable
from ..sim import Environment, ProcessGenerator, Interrupt, SimTime

class Timer:
    def __init__(
        self,
        env: Environment,
        timeout: SimTime,
        timeout_callback: Callable,
        args=None,
        kwargs=None
    ):
        if timeout <= 0:
            raise ValueError("timeout should be positive value")
        self.env = env
        self.timeout = timeout
        self.timeout_callback = timeout_callback
        self.start_time = self.env.now
        self.expire_time = self.start_time + timeout
        self.stopped = False
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        try:
            while env.now < self.expire_time:
                yield self.env.timeout(self.expire_time - env.now)
                if not self.stopped:
                    self.timeout_callback(*self.args, **self.kwargs)
        except Interrupt as _:
            pass

    def wait(self):
        yield self.proc

    def stop(self):
        self.stopped = True
        self.expire_time = self.env.now

    def restart(self, timeout: SimTime):
        self.start_time = self.env.now
        self.timeout = timeout
        self.expire_time = self.start_time + timeout
        if not self.proc.processed:
            self.proc.interrupt("restart timer")
            self.proc = self.env.process(self.run(self.env))
