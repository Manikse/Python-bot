# Python-bot
# Fortune Teller Telegram Bot
🌌 Multilingual AI-powered Telegram bot built with Python & Aiogram

# About the Project 🚀 

Fortune Teller Bot is an intelligent AI-based Telegram bot that can:

🔮 Generate predictions
✨ Send motivational messages
🧠 Remember user details (name, favorite things, etc.)
🌍 Work in 5 languages
💾 Store user data in SQLite
🤖 Chat like ChatGPT
💎 Provide Premium features
📨 Broadcast messages to all users
⏰ Auto-reset daily usage limits

Powered by Python 3 + Aiogram 3 + OpenRouter API.

# Features 🌟

Feature	Description
🔮 AI Predictions	Powered by OpenRouter (GPT-4o-mini / LLaMA / Mistral)
💬 Motivational Messages	Local + AI-generated
🌍 Multi-language Support	UA, EN, SK, DE, JA
🧠 User Memory	Bot remembers user details
💾 SQLite Database	Stores users, limits, preferences
💎 Premium Mode	BuyMeACoffee support
📡 Mass Broadcasting	/broadcast <text>
🔄 Daily Auto-Reset	Via APScheduler
🚀 Replit-ready	Built-in keep-alive server

# Installation
 Clone the repository
git clone https://github.com/Manikse/Python-bot.git
cd Python-bot

# Environment Variables 🔑

Create a .env file:

BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_openrouter_api_key
BUYME_LINK=https://buymeacoffee.com/your_link
DAILY_HOUR=9
OPENAI_MODEL=gpt-4o-mini
USE_OPENAI=true


⚠️ Do NOT upload .env to GitHub — use .env.example.

▶️ Run the bot locally
python bot.py


# Hosting on Replit ☁️

Upload all project files
Add environment variables
Ensure keep_alive() is enabled
Start the bot
Use UptimeRobot → Monitor type: HTTP

https://your-repl-name.username.repl.co

# Tech Stack 🛠

Python 3.11+
Aiogram 3
OpenRouter API
SQLite3
Flask Keep-Alive
APScheduler
Replit Hosting

# Support the Developer ☕
<p align="center"> <b>If you like this bot, consider supporting me:</b><br><br> <a href="https://buymeacoffee.com/manikse"> <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="220"> </a> </p>
