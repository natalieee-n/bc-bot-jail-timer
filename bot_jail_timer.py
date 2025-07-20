from bot import BCBot
from utils.jail_timer import JailTimer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BCBotJailTimer(BCBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.silent = False
        self.timer_list = {}
    
    async def _on_finish(self, id: str):
        logger.info(f"Player {id}'s timer has ended.")
        self.timer_list.pop(id)
        await self.send_to_chat(f"玩家 {id} 的计时结束")
    
    async def sentence(self, playerid: int, days: int):
        if playerid in self.others:
            self.timer_list[playerid] = JailTimer(
                on_finish_handler=self._on_finish,
                id=playerid,
            )
            await self.timer_list[playerid].add_time(days=days)
            await self.timer_list[playerid].start()
            await self.send_to_chat(f"玩家 {playerid} 已被审判：{await self.timer_list[playerid].get_remaining_time()}")
        else:
            await self.send_to_chat(f"玩家 {playerid} 不在房间中")
    
    async def update_time(self, playerid: int, update_days: int = None):
        if playerid in self.timer_list:
            if update_days != None:
                await self.timer_list[playerid].add_time(days=update_days)
            await self.send_to_chat(f"玩家 {playerid} 的剩余时间为：{await self.timer_list[playerid].get_remaining_time()}")
        else:
            await self.send_to_chat(f"玩家 {playerid} 没有被审判")

    async def start_timer(self, playerid: int):
        if playerid in self.timer_list:
            await self.timer_list[playerid].start()
            await self.send_to_chat(f"玩家 {playerid} 计时器继续，剩余时间为：{await self.timer_list[playerid].get_remaining_time()}")
        else:
            await self.send_to_chat(f"玩家 {playerid} 没有被审判")
    
    async def pause_timer(self, playerid: int):
        if playerid in self.timer_list:
            await self.timer_list[playerid].pause()
            await self.send_to_chat(f"玩家 {playerid} 计时器暂停，剩余时间为：{await self.timer_list[playerid].get_remaining_time()}")
        else:
            await self.send_to_chat(f"玩家 {playerid} 没有被审判")



    async def customized_event_handler(self, data):
        logger.info(f"Starting customized event handler...")

        if data["Type"] == "Chat" \
                and data["Sender"] != self.player["MemberNumber"] \
                and data["Sender"] in self.current_chatroom["Admin"]:

            message = data["Content"]
            if message == "N 安静":
                self.silent = True
                return
            elif message == "N 取消安静":
                self.silent = False
                return
            elif message == "N 笑":
                await self.send_to_chat("哈哈哈哈鱼鱼是笨蛋")

            # Sentence to jail (N 审判 {playerid} {days}天)
            elif message.startswith("N 审判"):
                message.split()
                playerid = int(message.split()[2])
                days = int(message.split()[3].strip("天"))
                
                await self.sentence(playerid, days)
            
            # Check/update time (N 时间 {playerid} (+/-{days}天))
            elif message.startswith("N 时间"):
                playerid = int(message.split()[2])

                if len(message.split()) == 4:
                    await self.update_time(playerid, int(message.split()[3].strip("天")))
                else:
                    await self.update_time(playerid)
            
            # Pause time (N 暂停 {playerid})
            elif message.startswith("N 暂停"):
                playerid = int(message.split()[2])
                if self.timer_list[playerid]._running == True:
                    await self.pause_timer(playerid)

            # Pause time (N 继续 {playerid})
            elif message.startswith("N 继续"):
                playerid = int(message.split()[2])
                if self.timer_list[playerid]._running == False:
                    await self.start_timer(playerid)
            

        if data["Type"] == "Action" \
                and data["Content"] == "ServerEnter" \
                and data["Sender"] in self.timer_list:
            await self.start_timer(data["Sender"])
        
        if data["Type"] == "Action" \
                and data["Content"] in ["ServerLeave", "ServerDisconnect"] \
                and data["Sender"] in self.timer_list:
            await self.pause_timer(data["Sender"])