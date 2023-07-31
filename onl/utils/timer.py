from typing import Callable
from ..sim import Environment, ProcessGenerator, Interrupt, SimTime

TimerId = int


class Timer:
    def __init__(
        self,
        env: Environment,
        timer_id: TimerId,
        timeout: SimTime,
        timeout_callback: Callable[[TimerId], None],
    ):
        if timeout <= 0:
            raise ValueError("timeout should be positive value")
        self.env = env
        self.timer_id = timer_id
        self.timeout = timeout
        self.timeout_callback = timeout_callback
        self.start_time = self.env.now
        self.expire_time = self.start_time + timeout
        self.stopped = False
        self.proc = env.process(self.run(env))

    def run(self, env: Environment) -> ProcessGenerator:
        try:
            while env.now < self.expire_time:
                yield self.env.timeout(self.expire_time - env.now)
                if not self.stopped:
                    self.timeout_callback(self.timer_id)
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
