import asyncio

class Timer:
    def __init__(self, timeout, callback, *args):
        """Set a timer a task. After the timeout seconds,
        callback will be executed
        """
        self.timeout = timeout
        self.callback = callback
        self.args = args
        self.task = None
        self.auto_reset = False

    async def _job(self):
        await asyncio.sleep(self.timeout / 1000)
        await self.callback(*self.args)
        if self.auto_reset:
            self.reset()

    def cancel(self):
        """Cancel the task
        """
        if self.task and not self.task.cancelled():
            self.task.cancel()

    def reset(self):
        """Reset the timer
        """
        if self.task and not self.task.cancelled():
            self.task.cancel()
        self.task = asyncio.create_task(self._job())
