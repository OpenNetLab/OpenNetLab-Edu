import pytest
from onl.utils import Timer

def test_timer(env, log):
    def cb(id: int):
        log.append(f"{id} finish")

    timer = Timer(env, timeout=5, timeout_callback=cb, args=[1])

    def pem(env, timer):
        yield timer.proc
        assert env.now == 5
        assert log == ["1 finish"]

    env.process(pem(env, timer))
    env.run()


def test_timer_restart(env, log):
    def cb(id: int):
        log.append(f"finish {id}")

    timer = Timer(env, timeout=5, timeout_callback=cb, args=[1])

    def pem(env, timer):
        yield env.timeout(3)
        assert env.now == 3
        timer.restart(6)
        yield timer.proc
        assert env.now == 9
        assert log == ["finish 1"]

    env.process(pem(env, timer))
    env.run()


def test_timer_auto_restart(env, log):
    def cb(id: int):
        log.append(env.now)

    timer = Timer(env, timeout=5, timeout_callback=cb, auto_restart=True, args=[1])
    def pem(env, timer):
        yield env.timeout(26)
        assert env.now == 26
        timer.stop()
        assert len(log) == 5
        assert log == [5, 10, 15, 20, 25]

    env.process(pem(env, timer))
    env.run()