# Pi Telegram Bot

A Telegram bot powered by the **pi coding agent** — any AI model (Claude, GPT, Gemini) with tools, streaming, and persistent sessions per chat.

## Features

- 🤖 Full pi agent (Claude) with all installed tools active
- 💬 One persistent session per Telegram chat (survives restarts)
- ⚡ Live streaming — bot message updates as Claude thinks
- 🗜️ `/compact` to compress long conversations
- 🔄 `/new` to start fresh
- 🛑 `/abort` to cancel a running task
- 🔒 Optional allowlist via `ALLOWED_CHAT_IDS`

## Setup

### 1. Get a Telegram Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the token

### 2. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: restrict to specific chat IDs
# Get yours by messaging @userinfobot on Telegram
ALLOWED_CHAT_IDS=123456789
```

### 3. Install dependencies

```bash
npm install
```

### 4. Run

```bash
# Development (auto-restart on change)
npm run dev

# Production
npm start
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Introduction and help |
| `/new` | Start a fresh conversation |
| `/compact` | Compress the conversation history |
| `/abort` | Cancel the current task |
| `/status` | Show session info (model, message count) |

## Sessions

Each Telegram chat gets its own persistent pi session stored in:

```
~/pi-telegram-bot/sessions/<chat_id>/
```

Sessions survive bot restarts and pick up where they left off.

## Installed Pi Tools (from nicobailon)

All tools are loaded from `~/.pi/agent/settings.json` and activate automatically:

| Package | What it does |
|---------|-------------|
| `pi-interactive-shell` | Control interactive CLIs in an overlay |
| `pi-design-deck` | Visual design deck with multi-slide previews |
| `pi-mcp-adapter` | Token-efficient MCP adapter |
| `pi-interview` | Interactive forms and user input |
| `pi-web-access` | Web search and content extraction |
| `pi-subagents` | Async subagent delegation |
| `pi-messenger` | Multi-agent communication |
| `pi-review-loop` | Automated code review loop |
| `pi-annotate` | Visual browser feedback |
| `pi-model-switch` | Agent-driven model switching |
| `pi-rewind-hook` | Rewind file changes |
| `pi-powerline-footer` | Powerline status bar |
| `pi-prompt-template-model` | Model frontmatter in prompt templates |
| `pi-skill-palette` | VS Code-style skill selector |
| `surf-cli` | Agent-controlled Chrome browser |
| `visual-explainer` | Rich HTML visual explanations |
| `pi-foreground-chains` | Multi-agent workflow orchestration |

## Deployment (VPS / Fly.io)

### With `pm2`:

```bash
npm install -g pm2
pm2 start "npm start" --name pi-bot
pm2 save
```

### With Docker:

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
CMD ["npm", "start"]
```

```bash
docker build -t pi-telegram-bot .
docker run -d --env-file .env pi-telegram-bot
```
