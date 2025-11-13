"""
Configuration File for Bot Hoster
Developer: @Zeroboy216
Channel: @zerodevbro
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API Credentials
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# MongoDB Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = "@bothoster_z_bot"

# Bot Settings
MAX_BOTS_PER_USER = 5
AUTO_RESTART = True
LOG_CHANNEL = os.getenv("LOG_CHANNEL", None)  # Optional: Channel ID for logs

# Security Settings
BLOCKED_IMPORTS = [
    "os.system",
    "os.remove",
    "subprocess",
    "eval",
    "exec",
    "__import__",
    "open",
    "file",
    "shutil.rmtree",
]

# Footer for hosted bots
BOT_FOOTER = """
━━━━━━━━━━━━━━━━
⚡ Powered by Zero Dev Bro
📢 Updates: @zerodevbro
"""

# Validate required environment variables
required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "OWNER_ID", "MONGO_URL"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

print("✅ Configuration loaded successfully!")
print(f"🤖 Bot Username: @{BOT_USERNAME}")
print(f"👤 Owner ID: {OWNER_ID}")
print(f"🗄️ Database: {DATABASE_NAME}")
