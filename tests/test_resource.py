from _pytest.main import pytest_addoption
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
        with resource.request() as req:
            yield req
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


def test_get_users(env):
    def process(env, resource):
        with resource.request() as req:
            yield req
            yield env.timeout(1)

    resource = simpy.Resource(env, 1)
    procs = [env.process(process(env, resource)) for i in range(3)]
    env.run(until=1)
    assert [evt.proc for evt in resource.users] == procs[0:1]
    assert [evt.proc for evt in resource.queue] == procs[1:]

    env.run(until=2)
    assert [evt.proc for evt in resource.users] == procs[1:2]
    assert [evt.proc for evt in resource.queue] == procs[2:]


#######################################################################
#                    Tests for PreemptiveResource                     #
#######################################################################

def test_preemptive_resource(env):
    def proc_a(env, resource, prio):
        try:
            with resource.request(priority=prio) as req:
                yield req
                pytest.fail('Should have received an preemption interrupt')
        except simpy.Interrupt:
            pass

    def proc_b(env, resource, prio):
        with resource.request(priority=prio) as req:
            yield req

    resource = simpy.PreemptiveResource(env, 1)
    env.process(proc_a(env, resource, 1))
    env.process(proc_b(env, resource, 0))

    env.run()


def test_preemptive_resource_timeout_0(env):
    def proc_a(env, resource, prio):
        with resource.request(priority=prio) as req:
            try:
                yield req
                yield env.timeout(1)
                pytest.fail('Should have received an interrupt/preemption.')
            except simpy.Interrupt:
                pass
        yield env.event()
        pytest.fail('Should never get here')

    def proc_b(env, resource, prio):
        with resource.request(priority=prio) as req:
            yield req
            assert env.now == 0

    resource = simpy.PreemptiveResource(env, 1)
    env.process(proc_a(env, resource, 1))
    env.process(proc_b(env, resource, 0))
    env.run()


def test_mixed_preemption(env, log):
    def p(env, res, id, delay, prio, preempt, log):
        yield env.timeout(delay)
        with res.request(priority=prio, preempt=preempt) as req:
            try:
                yield req
                yield env.timeout(2)
                log.append((env.now, id))
            except simpy.Interrupt as ir:
                log.append((env.now, id, (ir.cause.by, ir.cause.usage_since)))

    res = simpy.PreemptiveResource(env, capacity=1)
    p0 = env.process(p(env, res, id=0, delay=0, prio=2, preempt=True, log=log))
    p1 = env.process(p(env, res, id=1, delay=0, prio=2, preempt=True, log=log))
    p2 = env.process(
        p(env, res, id=2, delay=1, prio=1, preempt=False, log=log))
    p3 = env.process(p(env, res, id=3, delay=3, prio=0, preempt=True, log=log))
    p4 = env.process(p(env, res, id=4, delay=4, prio=3, preempt=True, log=log))
    # users: p0  put_queue: p2, p1
    # users: p2  put_queue: p1
    # p3 come, p2 is interrupted
    # users: p3  put_queue: p2, p0

    # At time 3, event queue: p3.Timeout -- p2.Request

    env.run()

    assert log == [
        (2, 0),  # p0
        (3, 2, (p3, 2)),  # p2 interrupted by
        (5, 3),
        (7, 1),
        (9, 4)
    ]


def test_nested_preemption(env, log):
    def process(env, res, id, delay, prio, preempt, log):
        yield env.timeout(delay)
        with res.request(priority=prio, preempt=preempt) as req:
            try:
                yield req
                yield env.timeout(5)
                log.append((env.now, id))
            except simpy.Interrupt as ir:
                log.append((env.now, id, (ir.cause.by, ir.cause.usage_since)))

    def process2(env, res0, res1, id, delay, prio, preempt, log):
        yield env.timeout(delay)
        with res0.request(priority=prio, preempt=preempt) as req0:
            try:
                yield req0
                with res1.request(priority=prio, preempt=preempt) as req1:
                    try:
                        yield req1
                        yield env.timeout(5)
                        log.append((env.now, id))
                    except simpy.Interrupt as ir:
                        log.append((env.now, id, (ir.cause.by,
                                                  ir.cause.usage_since,
                                                  ir.cause.resource)))
            except simpy.Interrupt as ir:
                log.append((env.now, id, (ir.cause.by, ir.cause.usage_since,
                                          ir.cause.resource)))

    res0 = simpy.PreemptiveResource(env, 1)
    res1 = simpy.PreemptiveResource(env, 1)

    # interrupted by p1
    p0 = env.process(process2(env, res0, res1, id=0, delay=0,
                     prio=-1, preempt=True, log=log))
    # normal
    p1 = env.process(process(env, res1,        id=1, delay=1,
                     prio=-2, preempt=True, log=log))
    # interrupted by p3
    p2 = env.process(process2(env, res0, res1, id=2, delay=20,
                     prio=-1, preempt=True, log=log))
    # normal
    p3 = env.process(process(env, res0,        id=3, delay=21,
                     prio=-2, preempt=True, log=log))
    # wait until p3.res1.req finish
    p4 = env.process(process2(env, res0, res1, id=4, delay=21,
                     prio=-1, preempt=True, log=log))
    env.run()

    assert log == [
        (1, 0, (p1, 0, res1)),
        (6, 1),
        (21, 2, (p3, 20, res0)),
        (26, 3),
        (31, 4)
    ]


#######################################################################
#                           test Container                            #
#######################################################################
def test_container(env, log):
    def putter(env, buf, log):
        yield env.timeout(1)
        while True:
            yield buf.put(2)
            log.append(('p', env.now))
            yield env.timeout(1)

    def getter(env, buf, log):
        yield buf.get(1)
        log.append(('g', env.now))

        yield env.timeout(1)
        yield buf.get(1)
        log.append(('g', env.now))

    buf = simpy.Container(env, init=0, capacity=2)
    env.process(putter(env, buf, log))
    env.process(getter(env, buf, log))
    env.run(until=5)

    assert log == [('p', 1), ('g', 1), ('g', 2), ('p', 2)]


def test_contaier_get_queued(env):
    def proc(env, delay, container, func_name):
        yield env.timeout(delay)
        with getattr(container, func_name)(1) as req:
            yield req

    container = simpy.Container(env, 1)
    p0 = env.process(proc(env, 0, container, 'get'))
    p1 = env.process(proc(env, 1, container, 'put'))
    p2 = env.process(proc(env, 1, container, 'put'))
    p3 = env.process(proc(env, 1, container, 'put'))

    env.run(until=1)
    assert [evt.proc for evt in container.put_queue] == []
    assert [evt.proc for evt in container.get_queue] == [p0]

    env.run(until=2)
    assert [evt.proc for evt in container.put_queue] == [p3]
    assert [evt.proc for evt in container.get_queue] == []



def test_initial_container_capacity(env):
    container = simpy.Container(env)
    assert container.capacity == float('inf')


def test_container_get_put_bounds(env):
    container = simpy.Container(env)
    pytest.raises(ValueError, container.get, -3)
    pytest.raises(ValueError, container.put, -3)


@pytest.mark.parametrize(('error', 'args'), [
    # erorr, capacity, init
    (None, [2, 1]),  # normal case
    (None, [1, 1]),  # init == capacity should be valid
    (None, [1, 0]),  # init == 0 should be valid
    (ValueError, [1, 2]),  # init > capcity
    (ValueError, [0]),  # capacity == 0
    (ValueError, [-1]),  # capacity < 0
    (ValueError, [1, -1]),  # init < 0
])
def test_container_init_capacity(env, error, args):
    args.insert(0, env)
    if error:
        pytest.raises(error, simpy.Container, *args)
    else:
        simpy.Container(*args)
