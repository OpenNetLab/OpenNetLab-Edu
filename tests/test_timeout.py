import pytest

def test_discrete_time_steps(env, log):
    def pem(env, log):
        while True:
            log.append(env.now)
            yield env.timeout(delay=1)

    env.process(pem(env, log))
    env.run(until=3)

    assert log == [0, 1, 2]


def test_negative_timeout(env):
    def pem(env):
        yield env.timeout(-1)

    env.process(pem(env))
    pytest.raises(ValueError, env.run)


def test_timeout_value(env):
    def pem(env):
        val = yield env.timeout(1, 'ohai')
        assert val == 'ohai'

    env.process(pem(env))
    env.run()


def test_shared_timeout(env, log):
    def child(env, timeout, id, log):
        yield timeout
        log.append((id, env.now))

    timeout = env.timeout(1)
    for i in range(3):
        env.process(child(env, timeout, i, log))

    env.run()
    assert log == [(0, 1), (1, 1), (2, 1)]


def test_triggered_timeout(env):
    def process(env):
        def child(env, event):
            value = yield event
            return value

        event = env.timeout(1, 'I was already done')
        yield env.timeout(2)
        value = yield env.process(child(env, event))
        assert value == 'I was already done'

    env.run(env.process(process(env)))
