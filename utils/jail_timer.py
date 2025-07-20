import asyncio
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JailTimer:
    def __init__(
            self, 
            on_finish_handler = None,
            **kwargs
        ):
        self.parameters = kwargs
        self.remaining_seconds = 0
        self._running = False
        self._lock = asyncio.Lock()
        self._on_finish_handler = on_finish_handler

    async def start(self):
        self._running = True
        asyncio.create_task(self._run())

    async def pause(self):
        self._running = False

    async def _run(self):
        while self._running and self.remaining_seconds > 0:
            await asyncio.sleep(1)
            async with self._lock:
                self.remaining_seconds -= 1
        
        if self._running and self.remaining_seconds <= 0:
            self._running = False
            if self._on_finish_handler:
                await self._on_finish_handler(**self.parameters)

    async def add_time(
            self, 
            days=0, 
            hours=0, 
            minutes=0, 
            seconds=0,
            ):
        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
        async with self._lock:
            self.remaining_seconds = max(0, self.remaining_seconds + total_seconds)

    async def get_remaining_time(self):
        async with self._lock:
            return str(timedelta(seconds=self.remaining_seconds))
