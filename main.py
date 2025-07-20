import asyncio
import json
import os
from dotenv import load_dotenv
load_dotenv()

from bot_jail_timer import BCBotJailTimer

with open('chatroom_config.json', 'r') as f:
    chatroom_config = json.load(f)

bot_test = BCBotJailTimer(
    username=os.getenv("BC_USERNAME", ""),
    password=os.getenv("BC_PASSWORD", ""),
    chatroom_settings=chatroom_config,
    appearance_code=os.getenv("APPEARANCE_CODE", ""),
)

asyncio.run(bot_test.run())