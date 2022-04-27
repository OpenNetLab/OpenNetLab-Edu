import asyncio

class Timer:
    def __init__(self, timeout, callback):
        """Set a timer a task. After the timeout seconds,
        callback will be executed
        """
        self.timeout = timeout
        self.callback = callback
        self.task = None

    async def _job(self):
        await asyncio.sleep(self.timeout)
        await self.callback()

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
