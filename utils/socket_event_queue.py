import asyncio
import socketio
import logging

logger = logging.getLogger(__name__)

class SocketEventQueue:
    def __init__(self, sio: socketio.AsyncClient):
        logger.info("Initializing EventQueue...")
        self.sio = sio
        self.event_queue = asyncio.Queue()
        self._sender_task = None
        logger.info("EventQueue initialized")


    async def start(self):
        """Start a background task"""
        logger.info("Starting EventQueue...")
        if self._sender_task is None or self._sender_task.done():
            self._sender_task = asyncio.create_task(self._sio_event_sender())
            logger.info("EventQueue has started")

    async def shutdown(self):
        """Shutdown the background task"""
        logger.info("Shutting down EventQueue...")
        if self._sender_task:
            self._sender_task.cancel()
            try:
                await self._sender_task
            except asyncio.CancelledError:
                logger.info("EventQueue has been shutdown")
            self._sender_task = None

    async def put_event(self, event_name: str, data: dict):
        """Add an event to the queue"""
        await self.event_queue.put((event_name, data))

    async def _sio_event_sender(self):
        """A background task that sends events from the queue"""
        while True:
            try:
                event, data = await self.event_queue.get()
                await self.sio.emit(event, data)
                await asyncio.sleep(0.1)  # frequency control
            except asyncio.CancelledError as e:
                logger.debug("Event sender is cancelled.", exc_info=e)
                return
