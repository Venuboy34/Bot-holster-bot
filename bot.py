"""
Telegram Bot Hoster System
Developer: @Zeroboy216
Channel: https://t.me/zerodevbro
"""

import os
import asyncio
import sys
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import subprocess
import psutil
import logging
import re
from typing import Dict, Optional
import tempfile
import signal

# Configuration
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "YOUR_OWNER_ID"))
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YOUR_BOT_USERNAME")
MONGO_URL = os.environ.get("MONGO_URL", "YOUR_MONGO_URL")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_hoster.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Pyrogram client
app = Client(
    "bot_hoster",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# MongoDB setup
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client.bot_hoster
bots_collection = db.bots
users_collection = db.users

# Store running bot processes
running_bots: Dict[str, subprocess.Popen] = {}

# Footer message for hosted bots
FOOTER_MESSAGE = "\n\n⚡ Powered by Zero Dev Bro\n📢 Updates: @zerodevbro"

# Dangerous imports to block
BLOCKED_IMPORTS = [
    'os.remove', 'os.unlink', 'os.rmdir', 'shutil.rmtree',
    'subprocess', 'eval', 'exec', '__import__',
    'open', 'file', 'input', 'compile'
]


# ============= Database Functions =============

async def get_user_bots(user_id: int):
    """Get all bots owned by a user"""
    cursor = bots_collection.find({"user_id": user_id})
    return await cursor.to_list(length=100)


async def get_bot_by_id(bot_id: str):
    """Get a specific bot by ID"""
    return await bots_collection.find_one({"_id": bot_id})


async def save_bot(user_id: int, bot_token: str, script_code: str):
    """Save a new bot to database"""
    bot_doc = {
        "user_id": user_id,
        "bot_token": bot_token,
        "script_code": script_code,
        "status": "stopped",
        "created_at": datetime.utcnow(),
        "last_restart": None,
        "error_count": 0
    }
    result = await bots_collection.insert_one(bot_doc)
    return str(result.inserted_id)


async def update_bot_status(bot_id: str, status: str):
    """Update bot status"""
    await bots_collection.update_one(
        {"_id": bot_id},
        {"$set": {"status": status, "last_restart": datetime.utcnow()}}
    )


async def update_bot_script(bot_id: str, script_code: str):
    """Update bot script"""
    await bots_collection.update_one(
        {"_id": bot_id},
        {"$set": {"script_code": script_code}}
    )


async def delete_bot(bot_id: str):
    """Delete a bot from database"""
    await bots_collection.delete_one({"_id": bot_id})


async def get_all_active_bots():
    """Get all active bots"""
    cursor = bots_collection.find({"status": "running"})
    return await cursor.to_list(length=1000)


async def increment_error_count(bot_id: str):
    """Increment error count for a bot"""
    await bots_collection.update_one(
        {"_id": bot_id},
        {"$inc": {"error_count": 1}}
    )


async def add_user(user_id: int, username: str = None):
    """Add or update user in database"""
    await users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "username": username,
                "last_seen": datetime.utcnow()
            },
            "$setOnInsert": {
                "joined_at": datetime.utcnow()
            }
        },
        upsert=True
    )


# ============= Script Validation =============

def validate_script(script_code: str) -> tuple[bool, str]:
    """Validate user script for security"""
    # Check for blocked imports
    for blocked in BLOCKED_IMPORTS:
        if blocked in script_code:
            return False, f"❌ Blocked import detected: {blocked}"
    
    # Check for basic syntax
    try:
        compile(script_code, '<string>', 'exec')
    except SyntaxError as e:
        return False, f"❌ Syntax error: {str(e)}"
    
    # Check for required function
    if 'on_message' not in script_code:
        return False, "❌ Script must contain 'on_message(message)' function"
    
    return True, "✅ Script is valid"


# ============= Bot Runner =============

async def validate_bot_token(bot_token: str) -> tuple[bool, str]:
    """Validate if bot token is valid"""
    try:
        temp_client = Client(
            f"temp_{bot_token[:10]}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            in_memory=True
        )
        await temp_client.start()
        me = await temp_client.get_me()
        await temp_client.stop()
        return True, me.username
    except Exception as e:
        return False, str(e)


def create_bot_script(bot_token: str, script_code: str, bot_id: str) -> str:
    """Create a runnable bot script"""
    runner_script = f'''
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = {API_ID}
API_HASH = "{API_HASH}"
BOT_TOKEN = "{bot_token}"
BOT_ID = "{bot_id}"

app = Client(
    "hosted_bot_{bot_id}",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

FOOTER = "{FOOTER_MESSAGE}"

# User script
{script_code}

@app.on_message(filters.private)
async def message_handler(client: Client, message: Message):
    try:
        # Create a simple bot object for compatibility
        class BotCompat:
            def __init__(self, client):
                self.client = client
            
            async def sendMessage(self, chat_id, text, parse_mode="HTML"):
                await self.client.send_message(chat_id, text + FOOTER, parse_mode=parse_mode)
        
        bot = BotCompat(client)
        
        # Execute user's on_message function
        on_message(message)
        
    except Exception as e:
        logger.error(f"Error in bot {{BOT_ID}}: {{e}}")
        await message.reply_text("❌ An error occurred while processing your message.")

if __name__ == "__main__":
    logger.info(f"Starting bot {{BOT_ID}}...")
    app.run()
'''
    return runner_script


async def start_bot(bot_id: str) -> tuple[bool, str]:
    """Start a hosted bot"""
    try:
        bot_data = await get_bot_by_id(bot_id)
        if not bot_data:
            return False, "Bot not found"
        
        if bot_id in running_bots:
            return False, "Bot is already running"
        
        # Create temporary script file
        script_content = create_bot_script(
            bot_data['bot_token'],
            bot_data['script_code'],
            bot_id
        )
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            prefix=f'bot_{bot_id}_'
        )
        temp_file.write(script_content)
        temp_file.close()
        
        # Start bot process
        process = subprocess.Popen(
            [sys.executable, temp_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        running_bots[bot_id] = {
            'process': process,
            'script_file': temp_file.name
        }
        
        await update_bot_status(bot_id, "running")
        logger.info(f"Started bot {bot_id}")
        
        # Monitor bot in background
        asyncio.create_task(monitor_bot(bot_id))
        
        return True, "✅ Bot started successfully!"
        
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        return False, f"❌ Error: {str(e)}"


async def stop_bot(bot_id: str) -> tuple[bool, str]:
    """Stop a hosted bot"""
    try:
        if bot_id not in running_bots:
            return False, "Bot is not running"
        
        bot_info = running_bots[bot_id]
        process = bot_info['process']
        
        # Terminate process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        # Clean up
        try:
            os.unlink(bot_info['script_file'])
        except:
            pass
        
        del running_bots[bot_id]
        await update_bot_status(bot_id, "stopped")
        logger.info(f"Stopped bot {bot_id}")
        
        return True, "✅ Bot stopped successfully!"
        
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        return False, f"❌ Error: {str(e)}"


async def monitor_bot(bot_id: str):
    """Monitor bot process and restart on crash"""
    while bot_id in running_bots:
        await asyncio.sleep(10)
        
        bot_info = running_bots.get(bot_id)
        if not bot_info:
            break
        
        process = bot_info['process']
        
        if process.poll() is not None:
            # Bot crashed
            logger.warning(f"Bot {bot_id} crashed, restarting...")
            await increment_error_count(bot_id)
            
            bot_data = await get_bot_by_id(bot_id)
            if bot_data and bot_data['error_count'] < 5:
                # Auto-restart
                del running_bots[bot_id]
                await asyncio.sleep(2)
                await start_bot(bot_id)
            else:
                # Too many errors, stop permanently
                logger.error(f"Bot {bot_id} has too many errors, stopping permanently")
                await stop_bot(bot_id)
                break


# ============= Keyboards =============

def main_menu_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Add New Bot", callback_data="add_bot")],
        [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/zerodevbro")]
    ]
    return InlineKeyboardMarkup(keyboard)


def bot_management_keyboard(bot_id: str, status: str):
    """Bot management keyboard"""
    keyboard = []
    
    if status == "running":
        keyboard.append([InlineKeyboardButton("🛑 Stop Bot", callback_data=f"stop_{bot_id}")])
    else:
        keyboard.append([InlineKeyboardButton("▶️ Start Bot", callback_data=f"start_{bot_id}")])
    
    keyboard.extend([
        [InlineKeyboardButton("✏️ Edit Script", callback_data=f"edit_{bot_id}")],
        [InlineKeyboardButton("🗑 Delete Bot", callback_data=f"delete_{bot_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="my_bots")]
    ])
    
    return InlineKeyboardMarkup(keyboard)


# ============= Command Handlers =============

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Start command handler"""
    await add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = f"""
🤖 <b>Welcome to Bot Hoster!</b>

Hi {message.from_user.first_name}! 

I can host your Telegram bots for free. Just provide:
• Bot Token
• Python Script

<b>Features:</b>
✅ Free bot hosting
✅ Auto-restart on crash
✅ Easy script editing
✅ 24/7 uptime

<b>Commands:</b>
/startbot - Start your bot
/stopbot - Stop your bot
/editbot - Edit bot script
/mybots - View all your bots

👨‍💻 Developer: @Zeroboy216
📢 Updates: @zerodevbro
"""
    
    await message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard()
    )


@app.on_message(filters.command("mybots") & filters.private)
async def my_bots_command(client: Client, message: Message):
    """Show user's bots"""
    await add_user(message.from_user.id, message.from_user.username)
    
    bots = await get_user_bots(message.from_user.id)
    
    if not bots:
        await message.reply_text(
            "📭 You don't have any hosted bots yet.\n\n"
            "Use /addbot to create your first bot!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    text = "🤖 <b>Your Hosted Bots:</b>\n\n"
    
    keyboard = []
    for bot in bots:
        status_emoji = "🟢" if bot['status'] == "running" else "🔴"
        text += f"{status_emoji} <b>Bot ID:</b> <code>{bot['_id']}</code>\n"
        text += f"   Status: {bot['status'].title()}\n"
        text += f"   Created: {bot['created_at'].strftime('%Y-%m-%d')}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status_emoji} {bot['_id'][:8]}...",
                callback_data=f"view_{bot['_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# User state management
user_states = {}

@app.on_message(filters.command("addbot") & filters.private)
async def add_bot_command(client: Client, message: Message):
    """Start bot creation process"""
    await add_user(message.from_user.id, message.from_user.username)
    
    user_states[message.from_user.id] = {"step": "waiting_token"}
    
    await message.reply_text(
        "🤖 <b>Create New Bot</b>\n\n"
        "Please send me your bot token.\n"
        "Get it from @BotFather\n\n"
        "Send /cancel to cancel this operation."
    )


@app.on_message(filters.text & filters.private & ~filters.command(["start", "mybots", "addbot", "cancel", "broadcast", "total", "stats"]))
async def handle_text_messages(client: Client, message: Message):
    """Handle text messages based on user state"""
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    
    if state["step"] == "waiting_token":
        # Validate token
        is_valid, result = await validate_bot_token(message.text)
        
        if not is_valid:
            await message.reply_text(
                f"❌ Invalid bot token!\n\n"
                f"Error: {result}\n\n"
                f"Please send a valid token or /cancel"
            )
            return
        
        user_states[user_id] = {
            "step": "waiting_script",
            "bot_token": message.text,
            "bot_username": result
        }
        
        example_script = '''def handle_start(message):
    welcome_text = """
🤖 <b>Welcome!</b>
I'm your custom bot!
"""
    bot.sendMessage(chat_id=message.chat.id, text=welcome_text, parse_mode="HTML")

def on_message(message):
    if message.text.startswith("/start"):
        handle_start(message)
    else:
        bot.sendMessage(chat_id=message.chat.id, text="You said: " + message.text)
'''
        
        await message.reply_text(
            f"✅ Bot token validated: @{result}\n\n"
            f"📝 Now send me your Python bot script.\n\n"
            f"<b>Example:</b>\n<code>{example_script}</code>\n\n"
            f"Requirements:\n"
            f"• Must contain on_message(message) function\n"
            f"• Use bot.sendMessage() to send messages\n"
            f"• No dangerous imports allowed\n\n"
            f"Send /cancel to cancel."
        )
    
    elif state["step"] == "waiting_script":
        script_code = message.text
        
        # Validate script
        is_valid, validation_msg = validate_script(script_code)
        
        if not is_valid:
            await message.reply_text(
                f"{validation_msg}\n\n"
                f"Please fix your script and send again or /cancel"
            )
            return
        
        # Save bot
        bot_id = await save_bot(
            user_id,
            state["bot_token"],
            script_code
        )
        
        del user_states[user_id]
        
        keyboard = [
            [InlineKeyboardButton("▶️ Start Bot", callback_data=f"start_{bot_id}")],
            [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")]
        ]
        
        await message.reply_text(
            f"✅ <b>Bot Created Successfully!</b>\n\n"
            f"🆔 Bot ID: <code>{bot_id}</code>\n"
            f"🤖 Username: @{state['bot_username']}\n"
            f"📊 Status: Stopped\n\n"
            f"Click 'Start Bot' to activate your bot!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


@app.on_message(filters.command("cancel") & filters.private)
async def cancel_command(client: Client, message: Message):
    """Cancel current operation"""
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
        await message.reply_text(
            "❌ Operation cancelled.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.reply_text("No active operation to cancel.")


# ============= Admin Commands =============

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_command(client: Client, message: Message):
    """Broadcast message to all users"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return
    
    broadcast_text = message.text.split(maxsplit=1)[1]
    
    users = await users_collection.find().to_list(length=10000)
    
    success = 0
    failed = 0
    
    status_msg = await message.reply_text(f"📡 Broadcasting to {len(users)} users...")
    
    for user in users:
        try:
            await client.send_message(user['user_id'], broadcast_text)
            success += 1
        except:
            failed += 1
        
        if (success + failed) % 50 == 0:
            await status_msg.edit_text(
                f"📡 Broadcasting...\n✅ Sent: {success}\n❌ Failed: {failed}"
            )
    
    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"✅ Successful: {success}\n"
        f"❌ Failed: {failed}"
    )


@app.on_message(filters.command("total") & filters.user(OWNER_ID))
async def total_command(client: Client, message: Message):
    """Show total bots statistics"""
    total_bots = await bots_collection.count_documents({})
    active_bots = await bots_collection.count_documents({"status": "running"})
    stopped_bots = await bots_collection.count_documents({"status": "stopped"})
    total_users = await users_collection.count_documents({})
    
    await message.reply_text(
        f"📊 <b>Bot Hoster Statistics</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"🤖 Total Bots: {total_bots}\n"
        f"🟢 Active Bots: {active_bots}\n"
        f"🔴 Stopped Bots: {stopped_bots}\n"
        f"💾 Running Processes: {len(running_bots)}"
    )


@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_command(client: Client, message: Message):
    """Show system statistics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    await message.reply_text(
        f"💻 <b>System Statistics</b>\n\n"
        f"🔹 CPU Usage: {cpu_percent}%\n"
        f"🔹 RAM Usage: {memory.percent}%\n"
        f"🔹 RAM Used: {memory.used / (1024**3):.2f} GB / {memory.total / (1024**3):.2f} GB\n"
        f"🔹 Disk Usage: {disk.percent}%\n"
        f"🔹 Disk Free: {disk.free / (1024**3):.2f} GB\n\n"
        f"🤖 Running Bots: {len(running_bots)}"
    )


@app.on_message(filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot_command(client: Client, message: Message):
    """Restart a specific bot"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /restart <bot_id>")
        return
    
    bot_id = message.command[1]
    
    status_msg = await message.reply_text(f"🔄 Restarting bot {bot_id}...")
    
    # Stop bot if running
    if bot_id in running_bots:
        await stop_bot(bot_id)
        await asyncio.sleep(2)
    
    # Start bot
    success, msg = await start_bot(bot_id)
    
    await status_msg.edit_text(msg)


# ============= Callback Handlers =============

@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle all callback queries"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "main_menu":
        await callback_query.message.edit_text(
            "🏠 <b>Main Menu</b>\n\nWhat would you like to do?",
            reply_markup=main_menu_keyboard()
        )
    
    elif data == "add_bot":
        user_states[user_id] = {"step": "waiting_token"}
        await callback_query.message.edit_text(
            "🤖 <b>Create New Bot</b>\n\n"
            "Please send me your bot token.\n"
            "Get it from @BotFather\n\n"
            "Send /cancel to cancel this operation."
        )
    
    elif data == "my_bots":
        bots = await get_user_bots(user_id)
        
        if not bots:
            await callback_query.message.edit_text(
                "📭 You don't have any hosted bots yet.\n\n"
                "Click 'Add New Bot' to create your first bot!",
                reply_markup=main_menu_keyboard()
            )
            return
        
        text = "🤖 <b>Your Hosted Bots:</b>\n\n"
        keyboard = []
        
        for bot in bots:
            status_emoji = "🟢" if bot['status'] == "running" else "🔴"
            text += f"{status_emoji} <code>{bot['_id'][:12]}</code> - {bot['status'].title()}\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_emoji} {bot['_id'][:8]}...",
                    callback_data=f"view_{bot['_id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        
        await callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("view_"):
        bot_id = data.split("_", 1)[1]
        bot_data = await get_bot_by_id(bot_id)
        
        if not bot_data or bot_data['user_id'] != user_id:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        status_emoji = "🟢" if bot_data['status'] == "running" else "🔴"
        
        text = f"🤖 <b>Bot Details</b>\n\n"
        text += f"{status_emoji} <b>Status:</b> {bot_data['status'].title()}\n"
        text += f"🆔 <b>Bot ID:</b> <code>{bot_id}</code>\n"
        text += f"📅 <b>Created:</b> {bot_data['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        text += f"🔢 <b>Errors:</b> {bot_data.get('error_count', 0)}\n"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=bot_management_keyboard(bot_id, bot_data['status'])
        )
    
    elif data.startswith("start_"):
        bot_id = data.split("_", 1)[1]
        bot_data = await get_bot_by_id(bot_id)
        
        if not bot_data or bot_data['user_id'] != user_id:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        await callback_query.answer("🔄 Starting bot...", show_alert=False)
        
        success, msg = await start_bot(bot_id)
        
        if success:
            await callback_query.answer("✅ Bot started!", show_alert=True)
            # Refresh view
            bot_data = await get_bot_by_id(bot_id)
            await callback_query.message.edit_reply_markup(
                reply_markup=bot_management_keyboard(bot_id, bot_data['status'])
            )
        else:
            await callback_query.answer(msg, show_alert=True)
    
    elif data.startswith("stop_"):
        bot_id = data.split("_", 1)[1]
        bot_data = await get_bot_by_id(bot_id)
        
        if not bot_data or bot_data['user_id'] != user_id:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        await callback_query.answer("🔄 Stopping bot...", show_alert=False)
        
        success, msg = await stop_bot(bot_id)
        
        if success:
            await callback_query.answer("✅ Bot stopped!", show_alert=True)
            # Refresh view
            bot_data = await get_bot_by_id(bot_id)
            await callback_query.message.edit_reply_markup(
                reply_markup=bot_management_keyboard(bot_id, bot_data['status'])
            )
        else:
            await callback_query.answer(msg, show_alert=True)
    
    elif data.startswith("edit_"):
        bot_id = data.split("_", 1)[1]
        bot_data = await get_bot_by_id(bot_id)
        
        if not bot_data or bot_data['user_id'] != user_id:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        user_states[user_id] = {
            "step": "editing_script",
            "bot_id": bot_id
        }
        
        await callback_query.message.edit_text(
            f"✏️ <b>Edit Bot Script</b>\n\n"
            f"Send me the new Python script for your bot.\n\n"
            f"<b>Current Script:</b>\n<code>{bot_data['script_code'][:500]}...</code>\n\n"
            f"Send /cancel to cancel editing."
        )
    
    elif data.startswith("delete_"):
        bot_id = data.split("_", 1)[1]
        bot_data = await get_bot_by_id(bot_id)
        
        if not bot_data or bot_data['user_id'] != user_id:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        # Stop bot if running
        if bot_id in running_bots:
            await stop_bot(bot_id)
        
        # Delete from database
        await delete_bot(bot_id)
        
        await callback_query.answer("✅ Bot deleted!", show_alert=True)
        await callback_query.message.edit_text(
            "🗑 <b>Bot Deleted Successfully!</b>\n\n"
            "Your bot has been removed from our system.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="my_bots")
            ]])
        )
    
    elif data == "help":
        help_text = """
ℹ️ <b>How to Use Bot Hoster</b>

<b>1. Create a Bot:</b>
• Get a bot token from @BotFather
• Click 'Add New Bot'
• Send your bot token
• Send your Python script

<b>2. Manage Your Bot:</b>
• Start/Stop your bot anytime
• Edit the script whenever needed
• Delete bots you don't need

<b>3. Script Requirements:</b>
• Must have on_message(message) function
• Use bot.sendMessage() to reply
• No dangerous imports allowed

<b>4. Script Example:</b>
<code>def on_message(message):
    if message.text == "/start":
        bot.sendMessage(
            chat_id=message.chat.id,
            text="Hello!"
        )
    else:
        bot.sendMessage(
            chat_id=message.chat.id,
            text="You said: " + message.text
        )</code>

<b>Commands:</b>
/addbot - Create a new bot
/mybots - View your bots
/cancel - Cancel operation

👨‍💻 Developer: @Zeroboy216
📢 Updates: @zerodevbro
"""
        
        await callback_query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            ]])
        )
    
    await callback_query.answer()


# Handle script editing
@app.on_message(filters.text & filters.private)
async def handle_editing_state(client: Client, message: Message):
    """Handle script editing"""
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    
    if state.get("step") == "editing_script":
        bot_id = state["bot_id"]
        new_script = message.text
        
        # Validate script
        is_valid, validation_msg = validate_script(new_script)
        
        if not is_valid:
            await message.reply_text(
                f"{validation_msg}\n\n"
                f"Please fix your script and send again or /cancel"
            )
            return
        
        # Update script
        await update_bot_script(bot_id, new_script)
        
        # Restart bot if it was running
        bot_data = await get_bot_by_id(bot_id)
        if bot_data['status'] == "running":
            await stop_bot(bot_id)
            await asyncio.sleep(2)
            await start_bot(bot_id)
            restart_msg = "\n\n🔄 Bot has been restarted with the new script."
        else:
            restart_msg = "\n\n💡 Start your bot to apply the changes."
        
        del user_states[user_id]
        
        await message.reply_text(
            f"✅ <b>Script Updated Successfully!</b>{restart_msg}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
            ]])
        )


# ============= Startup & Shutdown =============

async def restart_all_bots():
    """Restart all bots that were running before"""
    logger.info("Restarting all active bots...")
    active_bots = await get_all_active_bots()
    
    for bot in active_bots:
        try:
            await start_bot(str(bot['_id']))
            logger.info(f"Restarted bot {bot['_id']}")
        except Exception as e:
            logger.error(f"Failed to restart bot {bot['_id']}: {e}")


async def shutdown():
    """Clean shutdown"""
    logger.info("Shutting down...")
    
    # Stop all running bots
    for bot_id in list(running_bots.keys()):
        await stop_bot(bot_id)
    
    # Close MongoDB connection
    mongo_client.close()
    
    logger.info("Shutdown complete")


# ============= Main =============

async def main():
    """Main function"""
    try:
        logger.info("Starting Bot Hoster...")
        
        # Start Pyrogram client
        await app.start()
        logger.info("Bot started successfully!")
        
        # Restart previously active bots
        await restart_all_bots()
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await shutdown()
        await app.stop()


if __name__ == "__main__":
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the bot
    asyncio.run(main())
