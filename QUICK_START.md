# Quick Start Guide for Amazon Job Monitor Bot

## Step 1: Install Python (if not done already)
- Download from: https://www.python.org/downloads/
- OR install from Microsoft Store (search for "Python")
- IMPORTANT: Check "Add Python to PATH" during installation

## Step 2: Set up Telegram Bot (Optional but Recommended)
1. Open Telegram and message @BotFather
2. Send /newbot and follow instructions
3. Copy your bot token
4. Message your new bot with any text
5. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
6. Find your chat ID in the response

## Step 3: Configure the Bot
1. Open .env file in this folder
2. Replace "your_bot_token_here" with your actual bot token
3. Replace "your_chat_id_here" with your actual chat ID
4. Optionally adjust AMAZON_URLS and POLL_INTERVAL

## Step 4: Run Setup
- Double-click setup.bat (Windows)
- OR run in command prompt: python -m pip install -r requirements.txt

## Step 5: Start the Bot
- Run in command prompt: python bot.py
- OR create a shortcut with: python bot.py

## Troubleshooting
- If Python not found: Restart command prompt after Python installation
- If no jobs found: Try changing USE_SELENIUM=true in .env
- If Selenium fails: Install Chrome browser
- For help: Check the logs folder for detailed error messages

## Testing
The bot will:
1. Check Amazon hiring page every 15 seconds (configurable)
2. Save job data to jobs.db file
3. Send notifications for new jobs
4. Open job links in your browser automatically
5. Log all activity to logs/bot.log