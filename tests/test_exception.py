import pytest
import traceback
import sys


def test_error_forwarding(env):
    def child(env):
        raise ValueError("Onoes!")
        yield env.timeout(1)

    def parent(env):
        try:
            yield env.process(child(env))
            pytest.fail("We should not have gotton here ...")
        except ValueError as err:
            assert err.args[0] == "Onoes!"

    env.process(parent(env))
    env.run()


def test_no_parent_process(env):
    """Exceptions should be normally raised if there are no processes waiting
    for the one that raises something.

    """

    def child(env):
        raise ValueError("Onoes!")
        yield env.timeout(1)

    def parent(env):
        try:
            env.process(child(env))
            yield env.timeout(1)
        except Exception as err:
            pytest.fail(f"There should be no error ({err}).")

    env.process(parent(env))
    pytest.raises(ValueError, env.run)


def test_crashing_child_traceback(env):
    def panic(env):
        yield env.timeout(1)
        raise RuntimeError("Oh noes, roflcopter incoming... BOOM!")

    def root(env):
        try:
            yield env.process(panic(env))
            pytest.fail("Hey, where's the roflcopter?")
        except RuntimeError:
            # The current frame must be visible in the stacktrace.
            stacktrace = traceback.format_exc()
            print(stacktrace)
            assert stacktrace.find("yield env.process(panic(env))") != -1

    env.process(root(env))
    env.run()


def test_invalid_event(env):
    """Invalid yield values will cause the simulation to fail."""

    def root(env):
        yield None

    env.process(root(env))
    try:
        env.run()
        pytest.fail("Hey, this is not allowed!")
    except RuntimeError as err:
        assert err.args[0].endswith('Invalid yield value "None"')


def test_exception_handling(env):
    """If failed events are not defused (which is the default) the simulation
    crashes."""

    event = env.event()
    event.fail(RuntimeError())
    try:
        env.run(until=1)
        assert False, "There must be a RuntimeError!"
    except RuntimeError:
        pass


def test_callback_exception_handling(env):
    """Callbacks of events may handle exception by setting the defused
    attribute of event to True.

    If the defused has been set, than the exception will not be raised
    by env.step() function.
    """

    def callback(event):
        event.defused = True

    event = env.event()
    event.callbacks.append(callback)
    event.fail(RuntimeError())
    assert not event.defused, "Event has been defused immediately"
    env.run(until=1)
    assert event.defused, "Event has not been defused"


def test_process_exception_handling(env):
    """Processes can't ignore failed events and auto-handle exceptions."""

    def pem(env, event):
        try:
            yield event
            assert False, "Hey, the event should fail!"
        except RuntimeError:
            pass

    event = env.event()
    env.process(pem(env, event))
    event.fail(RuntimeError())

    assert not event.defused, "Event has been defused immediately"
    env.run(until=1)
    assert event.defused, "Event has not been defused"


def test_process_exception_chaining(env):
    """Because multiple processes can be waiting for an event, exceptions of
    failed events are copied before being thrown into a process. Otherwise, the
    traceback of the exception gets modified by a process."""
    import traceback

    def process_a(event):
        try:
            yield event
        except RuntimeError:
            stacktrace = traceback.format_exc()
            assert "process_b" not in stacktrace

    def process_b(event):
        try:
            yield event
        except RuntimeError:
            stacktrace = traceback.format_exc()
            assert "process_a" not in stacktrace

    event = env.event()
    event.fail(RuntimeError("foo"))

    env.process(process_a(event))
    env.process(process_b(event))

    env.run()


def test_sys_excepthook(env):
    """Check that the default exception hook reports exception chains."""

    def process_a(event):
        yield event

    def process_b(event):
        yield event

    event = env.event()
    event.fail(RuntimeError("foo"))

    env.process(process_b(env.process(process_a(event))))

    try:
        env.run()
    except BaseException:
        # Let the default exception hook print the traceback to the redirected
        # standard error channel.
        import sys
        from io import StringIO

        stderr, sys.stderr = sys.stderr, StringIO()

        sys.excepthook(*sys.exc_info())

        traceback = sys.stderr.getvalue()

        sys.stderr = stderr

        # Check if frames of process_a and process_b are visible in the
        # traceback.
        assert "process_a" in traceback
        assert "process_b" in traceback
