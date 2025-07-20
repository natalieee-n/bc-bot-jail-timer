from utils.jail_timer import JailTimer
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    async def on_finish(info: str = None):
        logger.info(f"Timer finished! {info}")

    timers = {
        "timer1": JailTimer(on_finish_handler=on_finish, info="timer1"),
        "timer2": JailTimer(on_finish_handler=on_finish, info="timer2"),
        "timer3": JailTimer(on_finish_handler=on_finish, info="timer3"),
    }
    for idx, timer in enumerate(timers.values()):
        await timer.add_time(days=idx * 5)
        await timer.start()

    await asyncio.sleep(3)
    for timer in timers.values():
        logger.info(f"Remaining time: {await timer.get_remaining_time()}")

    await asyncio.sleep(4)
    for timer in timers.values():
        logger.info(f"Remaining time: {await timer.get_remaining_time()}")

if __name__ == "__main__":
    asyncio.run(main())