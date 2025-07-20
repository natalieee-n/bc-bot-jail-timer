import asyncio
import socketio
import json
from lzstring import LZString

from utils.socket_event_queue import SocketEventQueue
from utils.logger import get_logger

logger = get_logger(__name__)


class BCBot:
    def __init__(
        self,
        username: str,
        password: str,
        chatroom_settings: dict,
        appearance_code: str = None,
    ):
        
        logger.info("Initializing bot...")
        self.sio = socketio.AsyncClient()
        self._register_handlers()

        self.event_queue = SocketEventQueue(self.sio)

        self.player = {}
        self.others = {}
        self.appearance = json.loads(
            LZString.decompressFromBase64(
                appearance_code
            )
        ) if appearance_code else None
        self.is_logged_in = False
        self.username = username
        self.password = password
        self.chatroom_settings = chatroom_settings
        self.current_chatroom = None
        self.chatroom_search_result = None

        logger.info("Bot initialized")
    
    def _register_handlers(self):
        self.sio.on("connect", self.on_connect)
        self.sio.on("disconnect", self.on_disconnect)
        self.sio.on("LoginResponse", self.on_LoginResponse)
        self.sio.on("ChatRoomSearchResponse", self.on_ChatRoomSearchResponse)
        self.sio.on("ChatRoomSearchResult", self.on_ChatRoomSearchResult)
        self.sio.on("AccountQueryResult", self.on_AccountQueryResult)
        self.sio.on("ChatRoomMessage", self.on_ChatRoomMessage)
        self.sio.on("ChatRoomSync", self.on_ChatRoomSync)
        self.sio.on("ChatRoomSyncItem", self.on_ChatRoomSyncItem)
        self.sio.on("ChatRoomSyncMemberLeave", self.on_ChatRoomSyncMemberLeave)
        self.sio.on("ChatRoomSyncCharacter", self.on_ChatRoomSyncCharacter)
        self.sio.on("ChatRoomSyncSingle", self.on_ChatRoomSyncSingle)
        self.sio.on("LoginQueue", self.on_LoginQueue)
    
    async def connect(self, url, **kwargs):
        try:
            logger.info("Connecting to server...")
            await self.sio.connect(url, **kwargs)
            logger.info("Successfully connected to server")
            return True
        except Exception as e:
            logger.error(e)
            return False

    async def disconnect(self):
        await self.sio.disconnect()
        logger.info("Disconnected from server")

    async def on_connect(self):
        logger.info("Socket connected")

    async def on_disconnect(self):
        logger.info("Socket disconnected")
        self.is_logged_in = False
        self.current_chatroom = None

    async def on_LoginResponse(self, data):
        logger.info("on_LoginResponse received.")
        logger.debug(f"on_LoginResponsedata: {data}")

        self.player = data
        self.is_logged_in = True
    
    async def on_ChatRoomSearchResponse(self, data):
        logger.info(f"on_ChatRoomSearchResponse data: {data}")

    async def on_AccountQueryResult(self, data):
        logger.info(f"on_AccountQueryResult data: {data}")

    async def on_ChatRoomMessage(self, data):
        logger.info(f"on_ChatRoomMessage data received. Type: {data['Type']}, Player: {data['Sender']}, Content: {data['Content']}")

        await self.customized_event_handler(data)

    async def on_ChatRoomSync(self, data):
        logger.info(f"on_ChatRoomSync data received.")
        logger.debug(f"on_ChatRoomSync data: {data}")
        self.current_chatroom = {
            k: v for k, v in data.items() if k not in ["Character", "Space"]
        }
        logger.info(f"Entered room {data['Name']}, {len(data['Character'])} members in total")

        await self.on_ChatRoomSyncCharacter(data)

    async def on_ChatRoomSyncItem(self, data):
        logger.info(f"on_ChatRoomSyncItem data received.")
        logger.debug(f"on_ChatRoomSyncItem data: {data}")

        item = data["Item"]
        if not self.others.get(item["Target"]):
            logger.warning(
                f"try to update an item on character {item['Target']} but the data is not in database"
            )
            return
        # update character data
        appearance = self.others[item["Target"]]["Appearance"]
        for i in range(len(appearance)):
            if appearance[i]["Group"] == item["Group"]:
                if item.get("Name"):  # change an item
                    appearance[i] = item
                else:  # remove an item
                    appearance = appearance[:i] + appearance[i + 1 :]
                return
        appearance.append(item)  # add a new item

    async def on_ChatRoomSyncMemberLeave(self, data):
        logger.info(f"on_ChatRoomSyncMemberLeave data: {data}")

        self.others.pop(data["SourceMemberNumber"], None)
        logger.info(f'Player left: {data["SourceMemberNumber"]}')

    async def on_ChatRoomSearchResult(self, data):
        logger.info(f"on_ChatRoomSearchResult data received.")
        logger.debug(f"on_ChatRoomSearchResult data: {data}")

        self.chatroom_search_result = data

    async def on_ChatRoomSyncCharacter(self, data):
        logger.info(f"on_ChatRoomSyncCharacter data received.")
        logger.debug(f"on_ChatRoomSyncCharacter data: {data}")

        Characters = (
            data["Character"]
            if isinstance(data["Character"], list)
            else [data["Character"]]
        )
        for i in Characters:
            logger.info(f"Update {i['Name']}({i['MemberNumber']})'s data")
            self.others[i["MemberNumber"]] = i

            # update ownership
            owner = i.get("Ownership", {})
            owner = owner.get("MemberNumber", 0) if owner else 0
            if (
                owner != 0
                and owner == self.player["MemberNumber"]
                and i["MemberNumber"] not in self.player["SubmissivesList"]
            ):
                await self.add_or_remove_submissive(i["MemberNumber"])
            # # add gameversion check
            # gameversion = i.get("OnlineSharedSettings", {}).get("GameVersion")
            # if gameversion:
            #     gv = int(gameversion[1:])
            #     mygv = int(
            #         self.player.get("OnlineSharedSettings", {}).get(
            #             "GameVersion", "R0"
            #         )[1:]
            #     )
            #     if gv > mygv:
            #         self.player["OnlineSharedSettings"]["GameVersion"] = "R{}".format(
            #             gv
            #         )
            #         await self.event_queue.put_event(
            #             "AccountUpdate",
            #             {"OnlineSharedSettings": self.player["OnlineSharedSettings"]}
            #         )

    async def on_ChatRoomSyncSingle(self, data):
        logger.info(f"on_ChatRoomSyncSingle data received.")
        logger.debug(f"on_ChatRoomSyncSingle data: {data}")

        await self.on_ChatRoomSyncCharacter(data)

    async def on_LoginQueue(self, data):
        logger.info(f"on_LoginQueue data: {data}")
        await asyncio.sleep(30)


    async def login(self):
        logger.info(f"Logging in using AccountName {self.username}.")
        await self.event_queue.put_event(
            "AccountLogin", 
            {
                "AccountName": self.username, 
                "Password": self.password
            }
        )

    async def search_chatroom(self, name, **kwargs):
        logger.info(f"Searching for chatroom {name}.")
        data = {
            "Query": name.upper(),
            "Language": "",
            "Space": "",
            "Game": "",
            "FullRooms": True,
            "ShowLocked": True,
        }
        data.update(kwargs)
        await self.event_queue.put_event("ChatRoomSearch", data)

    async def create_chatroom(self, chatroom_settings: dict):
        data = chatroom_settings
        data["Admin"].append(self.player["MemberNumber"])
        logger.info(f'Creating chatroom {data["Name"]}.')
        logger.debug(f"Chatroom data: {data}")
        await self.event_queue.put_event("ChatRoomCreate", data)
    
    async def join_chatroom(self, name):
        data = {"Name": name}
        logger.info(f"Joining chatroom {name}.")
        await self.event_queue.put_event("ChatRoomJoin", data)

    async def reset_appearance(self):
        logger.info("Resetting appearance...")
        if not self.appearance:
            logger.warning("No appearance data found. Skipping...")
            return
        data = {
            "AssetFamily": "Female3DCG",
            "Appearance": self.appearance,
            "ItemPermission": 1,
        }
        await self.event_queue.put_event("AccountUpdate", data)
    
    async def send_to_chat(self, msg):
        logger.info(f"Sending message: {msg}")
        data = {"Content": msg, "Type": "Chat", "Target": None}
        await self.event_queue.put_event("ChatRoomChat", data)

    async def customized_event_handler(self, data):
        logger.warning("No customized event handler found.")
        pass

    async def run(self):
        try:
            logger.info("Starting event queue...")
            await self.event_queue.start()

            
            await self.connect(
                "https://bondage-club-server.herokuapp.com/",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0",
                    "Origin": "https://www.bondage-europe.com",
                },
            )
            await self.login()
            while True:
                if not self.is_logged_in:
                    await self.login()
                elif not self.current_chatroom:
                    await self.search_chatroom(self.chatroom_settings["Name"])
                    while self.chatroom_search_result == None:
                        await asyncio.sleep(0.5)
                    if self.chatroom_search_result:
                        await self.join_chatroom(self.chatroom_settings["Name"])
                    else:
                        await self.create_chatroom(self.chatroom_settings)
                    await asyncio.sleep(1)
                    await self.reset_appearance()
                else:
                    logger.info(
                        "Idling..."
                    )
                    await self.sio.wait()
                await asyncio.sleep(3)
                


        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Shutting down with Ctrl+C...")
        except Exception as e:
            logger.error(e)
        
        finally:
            await self.disconnect()
