# bc-bot
Bondage Club Bot using socket.io.

## About this project
This project is based on [BC-BotNyan](https://github.com/miyu-notM/BC-BotNyan), originally created by [@miyu-notM](https://github.com/miyu-notM).

## Installation

1. Edit configs

```bash
vim .env # based on .env.example
vim chatroom_config.json
```

Choose either of the following ways to install.

2.a Instaling using Docker

```bash
docker compose up --build
```

2.b Installing directly

```bash
pip install -r requirements.txt
python main.py
```

## Useful Links

- Server socketio event definition: [Ben987/Bondage-Club-Server](https://github.com/Ben987/Bondage-Club-Server)
- Client socketio event definition: [BondageProjects/Bondage-College](https://gitgud.io/BondageProjects/Bondage-College/-/blob/master/BondageClub/Scripts/Server.js)

## License

The original project is licensed under the MIT license.  
All original rights and credits belong to the original author.
