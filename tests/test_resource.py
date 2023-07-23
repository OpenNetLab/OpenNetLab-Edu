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


def test_resource_release_after_interrupt(env):
    """A process needs to release a resource, even it it was interrupted
    and does not continue to wait for it."""
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
            res.release(evt)
            assert env.now == 0

    def interruptor(env, proc):
        proc.interrupt()
        return 0
        yield

    res = simpy.Resource(env, 1)
    env.process(pem(env, res))
    proc = env.process(victim(env, res))
    env.process(interruptor(env, proc))
    env.run()


def test_resource_immediate_requests(env):
    def child(env, res):
        ans = []
        for i in range(3):
            with res.request() as req:
                yield req
                ans.append(env.now)
                yield env.timeout(1)
        return ans

    def parent(env):
        res = simpy.Resource(env, 1)
        child1 = env.process(child(env, res))
        child2 = env.process(child(env, res))
        ans1 = yield child1
        ans2 = yield child2
        assert ans1 == [0, 2, 4]
        assert ans2 == [1, 3, 5]

    env.process(parent(env))
    env.run()


def test_resource_cm_exception(env, log):
    """Resource with context manager receives an exception"""
    def pem(env, resource, log, raise_):
        try:
            with resource.request() as req:
                yield req
                yield env.timeout(1)
                log.append(env.now)
                if raise_:
                    raise ValueError('foo')
        except ValueError as err:
            assert err.args == ('foo',)

    resource = simpy.Resource(env, 1)
    env.process(pem(env, resource, log, True))
    env.process(pem(env, resource, log, False))
    env.run()
    assert log == [1, 2]


def test_resource_with_condition(env):
    def process(env, resource):
        with resource.request() as res_event:
            result = yield res_event | env.timeout(1)
            assert res_event in result

    resource = simpy.Resource(env, 1)
    env.process(process(env, resource))
    env.run()


def test_resource_with_priority_queue(env):
    def process(env, delay, resource, priority, res_time):
        yield env.timeout(delay)
        req = resource.request(priority=priority)
        yield req
        # assert env.now == res_time
        print(env.now, delay, priority)
        yield env.timeout(5)
        resource.release(req)

    resource = simpy.PriorityResource(env, capacity=1)
    env.process(process(env, 0, resource, 2, 0))
    env.process(process(env, 2, resource, 3, 10))
    env.process(process(env, 2, resource, 3, 15))  # Test equal priority
    env.process(process(env, 4, resource, 1, 5))
    env.run()



def test_sorted_queue_maxlen(env):
    """Requests must fail if more than *maxlen* requests happen
    concurrently."""
    resource = simpy.PriorityResource(env, capacity=1)
    resource.put_queue.maxlen = 1

    def process(env, resource):
        # The first request immediately triggered and does not enter the queue.
        resource.request(priority=1)
        # The second request is enqueued.
        resource.request(priority=1)
        try:
            # The third request will now fail.
            resource.request(priority=1)
            pytest.fail('Expected a RuntimeError')
        except RuntimeError as e:
            assert e.args[0] == 'Cannot append event. Queue is full.'
        yield env.timeout(0)

    env.process(process(env, resource))
    env.run()
