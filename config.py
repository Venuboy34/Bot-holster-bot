"""
Configuration File for Bot Hoster (Enhanced Multi-Language Support)
Developer: @Zeroboy216
Channel: @zerodevbro
Version: 2.0
"""

import os
import sys
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
DATABASE_NAME = os.getenv("DATABASE_NAME", "@bothoster_z_bot")

# Bot Settings
MAX_BOTS_PER_USER = int(os.getenv("MAX_BOTS_PER_USER", "5"))
AUTO_RESTART = os.getenv("AUTO_RESTART", "true").lower() == "true"
LOG_CHANNEL = os.getenv("LOG_CHANNEL", None)  # Optional: Channel ID for logs

# File Settings
MAX_SCRIPT_SIZE = int(os.getenv("MAX_SCRIPT_SIZE", "10485760"))  # 10MB default
SESSION_DIR = os.getenv("SESSION_DIR", "./sessions")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
LOG_DIR = os.getenv("LOG_DIR", "./logs")

# Create directories if they don't exist
for directory in [SESSION_DIR, DOWNLOAD_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Debug mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Security Settings - Python specific
BLOCKED_IMPORTS = [
    "os.system",
    "os.remove",
    "os.rmdir",
    "os.unlink",
    "subprocess.call",
    "subprocess.run",
    "subprocess.Popen",
    "eval(",
    "exec(",
    "__import__",
    "open(",
    "file(",
    "shutil.rmtree",
    "shutil.move",
    "pathlib.Path.unlink",
    "importlib.import_module",
]

# Supported File Types Configuration
SUPPORTED_FILE_TYPES = {
    "py": {
        "name": "Python",
        "emoji": "🐍",
        "runtime": "python3",
        "extension": ".py",
        "enabled": True,
        "description": "Python scripts with Pyrogram",
    },
    "js": {
        "name": "JavaScript",
        "emoji": "📜",
        "runtime": "node",
        "extension": ".js",
        "enabled": True,
        "description": "Node.js bots with Telegraf/node-telegram-bot-api",
    },
    "sh": {
        "name": "Shell Script",
        "emoji": "🐚",
        "runtime": "bash",
        "extension": ".sh",
        "enabled": True,
        "description": "Bash scripts for Linux",
    },
    "rb": {
        "name": "Ruby",
        "emoji": "💎",
        "runtime": "ruby",
        "extension": ".rb",
        "enabled": True,
        "description": "Ruby scripts with telegram-bot-ruby",
    },
    "php": {
        "name": "PHP",
        "emoji": "🐘",
        "runtime": "php",
        "extension": ".php",
        "enabled": True,
        "description": "PHP scripts with Telegram Bot API",
    },
    "go": {
        "name": "Go",
        "emoji": "🔵",
        "runtime": "go",
        "extension": ".go",
        "enabled": True,
        "description": "Go programs with tgbotapi",
    },
}

# Get list of enabled file types
ENABLED_FILE_TYPES = [ft for ft, config in SUPPORTED_FILE_TYPES.items() if config["enabled"]]

# Footer for hosted bots
BOT_FOOTER = """
━━━━━━━━━━━━━━━━
⚡ Powered by Zero Dev Bro
📢 Updates: @zerodevbro
"""

# Logging Configuration
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Rate Limiting (future feature)
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_PERIOD = 60  # seconds

# Bot Limits
MAX_SCRIPT_LINES = 1000
MAX_FILE_SIZE_MB = 10
MAX_UPLOAD_SIZE_MB = 10

# Runtime Validation
RUNTIME_CHECK_TIMEOUT = 5  # seconds

# Auto-restart Settings
AUTO_RESTART_DELAY = 5  # seconds
MAX_AUTO_RESTARTS = 10  # maximum restarts before giving up
RESTART_WINDOW = 3600  # time window in seconds for counting restarts

# Performance Settings
BOT_IDLE_TIMEOUT = 3600  # seconds before stopping idle bots
CLEANUP_INTERVAL = 86400  # seconds between cleanup tasks (24 hours)
LOG_RETENTION_DAYS = 30  # days to keep logs

# Validate required environment variables
required_vars = {
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "BOT_TOKEN": BOT_TOKEN,
    "OWNER_ID": OWNER_ID,
    "MONGO_URL": MONGO_URL
}

missing_vars = []
invalid_vars = []

for var_name, var_value in required_vars.items():
    if not var_value or (isinstance(var_value, int) and var_value == 0):
        missing_vars.append(var_name)
    elif var_name == "API_ID" and var_value == 0:
        invalid_vars.append(f"{var_name} (must be a valid integer)")
    elif var_name == "API_HASH" and len(var_value) < 10:
        invalid_vars.append(f"{var_name} (seems too short)")
    elif var_name == "BOT_TOKEN" and ":" not in str(var_value):
        invalid_vars.append(f"{var_name} (invalid format, should contain ':')")

if missing_vars:
    print("❌ Missing required environment variables:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\n💡 Copy .env.example to .env and fill in your values")
    sys.exit(1)

if invalid_vars:
    print("⚠️  Invalid environment variables detected:")
    for var in invalid_vars:
        print(f"   - {var}")
    print("\n💡 Please check your .env file")
    sys.exit(1)

# Success message
print("╔═══════════════════════════════════════════╗")
print("║   ✅ Configuration Loaded Successfully    ║")
print("╚═══════════════════════════════════════════╝")
print(f"🤖 Bot Username: @{BOT_USERNAME}")
print(f"👤 Owner ID: {OWNER_ID}")
print(f"🗄️  Database: {DATABASE_NAME}")
print(f"📁 Max Bots Per User: {MAX_BOTS_PER_USER}")
print(f"🔄 Auto-Restart: {'Enabled' if AUTO_RESTART else 'Disabled'}")
print(f"🐛 Debug Mode: {'Enabled' if DEBUG else 'Disabled'}")
print(f"\n📚 Supported Languages ({len(ENABLED_FILE_TYPES)}):")
for file_type in ENABLED_FILE_TYPES:
    config = SUPPORTED_FILE_TYPES[file_type]
    print(f"   {config['emoji']} {config['name']} ({file_type})")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# Export configuration summary for other modules
CONFIG_SUMMARY = {
    "version": "2.0",
    "bot_username": BOT_USERNAME,
    "max_bots_per_user": MAX_BOTS_PER_USER,
    "auto_restart": AUTO_RESTART,
    "supported_languages": len(ENABLED_FILE_TYPES),
    "debug_mode": DEBUG,
}

def get_runtime_command(file_type: str):
    """Get the runtime command for a file type"""
    if file_type in SUPPORTED_FILE_TYPES:
        return SUPPORTED_FILE_TYPES[file_type]["runtime"]
    return None

def is_file_type_supported(file_type: str):
    """Check if a file type is supported"""
    return file_type in ENABLED_FILE_TYPES

def get_file_type_info(file_type: str):
    """Get information about a file type"""
    return SUPPORTED_FILE_TYPES.get(file_type, None)
