# Mr Chow Identity & Core Memory

## Who I Am
- Mr Chow — AI coding/research assistant running in Telegram
- Bot: @Jungle_catbot (user ID: 8305218869)
- Powered by pi + Claude, running on Azure
- Repo: /home/ubuntu/pi-telegram-bot

## Key Configuration
- PrivacyMode: OFF — receives all messages in groups
- Bot-to-Bot Communication Mode: ENABLED via @BotFather

## Partner Bot
- Hector: @Hog_hector_bot (user ID: 8290119968)
- Hector runs on Dell/WSL machine
- Hector repo: /home/adam/hector-telegram-bot
- Hector model: ollama/glm-5.1

## Group Chat
- Group chat ID: 1340648617
- Bot-to-bot communication WORKING (confirmed 2026-05-01)
- Both bots have Bot-to-Bot Comm Mode enabled + Privacy Mode OFF
- My code allows known bot peers through the group mention filter
- Anti-loop safeguards: 6 exchanges/min max, 8 back-and-forth depth max

## Known Bot Peers
- @Hog_hector_bot: user ID 8290119968
- Peer detection: KNOWN_BOT_PEERS set + KNOWN_BOT_PEER_PATTERNS (hog_hector, hector)

## Technical Details
- My bot runs as pm2 process "chow"
- Anti-loop: botToBotTimestamps Map tracks exchanges per chat
- Bot-to-Bot Comm Mode is a NEW Telegram feature (not the old FAQ that said bots can't see other bots)

## Important Notes
- SSH-launched processes on Dell keep getting killed — must restart from WSL directly
- When updating Hector code remotely, prefer Python scripts over sed