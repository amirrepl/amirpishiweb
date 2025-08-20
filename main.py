import os
import time
import json
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, Optional
import discord
import instaloader
from discord import Intents, File, Embed, Guild
from discord.ext import commands
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import aiohttp

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Simple config class - NO external config.py needed
class Config:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', '')
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')
    WEB_HOST = '0.0.0.0'
    WEB_PORT = 5000
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-me-123')
    REQUEST_DELAY = 12
    MAX_REQUESTS_PER_HOUR = 25
    MAX_REQUESTS_PER_DAY = 200
    SESSION_FILE = 'data/instagram_session'
    STATS_FILE = 'data/stats.json'
    LOG_FILE = 'data/bot.log'
    ENABLE_WEB_UI = True
    ENABLE_REALTIME_STATS = True

# Setup logging
print("🚀 Starting Instagram Reel Bot...")
print("📁 Current directory:", os.getcwd())
print("🐍 Python version:", os.sys.version)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('AdvancedReelBot')

# Flask setup
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

class AdvancedInstagramBot:
    def __init__(self):
        print("🔄 Initializing Instagram bot...")
        self.stats = self.load_stats()
        self.request_history = []
        self.active_downloads = {}
        self.instagram_loader = self.setup_instagram()
        print("✅ Instagram bot initialized")
    
    def load_stats(self):
        os.makedirs('data', exist_ok=True)
        if os.path.exists(Config.STATS_FILE):
            try:
                with open(Config.STATS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'rate_limited': 0,
            'user_activity': {},
            'guild_activity': {}
        }
    
    def setup_instagram(self):
        loader = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_videos=True,
            download_geotags=False,
            download_comments=False,
            save_metadata=False
        )
        
        try:
            if Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
                print("🔐 Attempting Instagram login...")
                loader.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
                print("✅ Instagram login successful")
            else:
                print("⚠️ Using public Instagram access (some features limited)")
        except Exception as e:
            print(f"❌ Instagram login failed: {e}")
            
        return loader

class AdvancedDiscordBot(commands.Bot):
    def __init__(self, instagram_bot: AdvancedInstagramBot):
        print("🤖 Initializing Discord bot...")
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.instagram_bot = instagram_bot
        print("✅ Discord bot initialized")
    
    async def on_ready(self):
        print(f'🎯 Bot logged in as: {self.user}')
        print(f'🏠 Serving {len(self.guilds)} guild(s)')
        print(f'🌐 Web UI: http://{Config.WEB_HOST}:{Config.WEB_PORT}')
        # Fixed activity setting
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for Instagram reels 📱"
            )
        )
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        content = message.content.lower()
        if 'instagram.com' in content and ('/reel/' in content or '/p/' in content):
            print(f"📱 Instagram link detected from {message.author}: {message.content}")
            await message.channel.send("🔄 Processing Instagram reel...")

# Flask Routes
@app.route('/')
def dashboard():
    return "Dashboard - Bot is running! Send Instagram reel links in Discord."

@app.route('/stats')
def stats():
    return "Statistics page - Coming soon"

@app.route('/settings')
def settings():
    return "Settings page - Coming soon"

@app.route('/logs')
def logs():
    return "Logs page - Coming soon"

def run_flask():
    print(f"🌐 Starting web server on http://{Config.WEB_HOST}:{Config.WEB_PORT}")
    try:
        socketio.run(app, host=Config.WEB_HOST, port=Config.WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Web server error: {e}")

async def main():
    print("🔧 Starting main function...")
    
    # Create directories
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    print("📁 Directories created")
    
    # Check Discord token
    if not Config.DISCORD_TOKEN or Config.DISCORD_TOKEN == 'your_bot_token_here':
        print("❌ ERROR: DISCORD_TOKEN not set properly!")
        print("💡 Please edit your .env file and add:")
        print("DISCORD_TOKEN=your_actual_bot_token_here")
        print("💡 Get your token from: https://discord.com/developers/applications")
        return
    
    print("✅ Discord token found")
    
    # Initialize bots
    try:
        instagram_bot = AdvancedInstagramBot()
        discord_bot = AdvancedDiscordBot(instagram_bot)
        print("✅ Both bots initialized successfully")
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return
    
    # Start Flask
    if Config.ENABLE_WEB_UI:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("✅ Web server started")
    
    # Run Discord bot
    try:
        print("🔗 Connecting to Discord...")
        await discord_bot.start(Config.DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Discord connection failed: {e}")
        print("💡 Check your Discord token and internet connection")

if __name__ == "__main__":
    print("=" * 50)
    print("INSTAGRAM REEL BOT STARTING...")
    print("=" * 50)
    
    # Check .env file
    if not os.path.exists('.env'):
        print("❌ .env file not found! Creating template...")
        with open('.env', 'w') as f:
            f.write("DISCORD_TOKEN=your_bot_token_here\n")
            f.write("INSTAGRAM_USERNAME=your_instagram_username\n")
            f.write("INSTAGRAM_PASSWORD=your_instagram_password\n")
            f.write("SECRET_KEY=change-this-to-random-string-123\n")
        print("💡 Please edit .env file with your actual credentials")
        print("💡 Then run the bot again")
    else:
        print("✅ .env file found")
        # Check if .env has placeholder values
        with open('.env', 'r') as f:
            content = f.read()
            if 'your_bot_token_here' in content:
                print("⚠️ Please replace 'your_bot_token_here' with your actual Discord bot token")
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        print("=" * 50)
        print("BOT SHUTDOWN COMPLETE")
        print("=" * 50)