import pytest

from OpenNetLab import simpy


def test_resource(env, log):
    def pem(env, name, resource, log):
        req = resource.request()
        yield req
        assert resource.count == 1

        yield env.timeout(1)
        resource.release(req)

        log.append((name, env.now))

    resource = simpy.Resource(env, capacity=1)
    assert resource.capacity == 1
    assert resource.count == 0
    env.process(pem(env, 'a', resource, log))
    env.process(pem(env, 'b', resource, log))
    env.run()

    assert log == [('a', 1), ('b', 2)]


def test_resource_context_manager(env, log):
    """The event that ``Resource.request()`` returns can be used as
    Context Manager."""
    def pem(env, name, resource, log):
        with resource.request() as request:
            yield request
            yield env.timeout(1)

        log.append((name, env.now))

    resource = simpy.Resource(env, capacity=1)
    env.process(pem(env, 'a', resource, log))
    env.process(pem(env, 'b', resource, log))
    env.run()

    assert log == [('a', 1), ('b', 2)]


def test_resource_slots(env, log):
    def pem(env, name, resource, log):
        with resource.request() as req:
            yield req
            log.append((name, env.now))
            yield env.timeout(1)

    resource = simpy.Resource(env, capacity=3)
    for i in range(9):
        env.process(pem(env, str(i), resource, log))
    env.run()

    assert log == [('0', 0), ('1', 0), ('2', 0), ('3', 1), ('4', 1), ('5', 1),
                   ('6', 2), ('7', 2), ('8', 2)]


def test_resource_continue_after_interrupt(env):
    """A process may be interrupted while waiting for a resource but
    should be able to continue waiting afterwards."""
    def pem(env, res):
        with res.request() as req:
            yield req
            yield env.timeout(1)

    def victim(env, res):
        try:
            evt = res.request()
            yield evt
            pytest.fail('Should not have gotten the resource.')
        except simpy.Interrupt:
            yield evt
            res.release(evt)
            assert env.now == 1

    def interruptor(env, proc):
        proc.interrupt()
        return 0
        yield

    res = simpy.Resource(env, 1)
    env.process(pem(env, res))
    proc = env.process(victim(env, res))
    env.process(interruptor(env, proc))
    env.run()
