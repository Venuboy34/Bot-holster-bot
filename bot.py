"""
Telegram Bot Hoster - Main Entry Point
Developer: @Zeroboy216
Channel: @zerodevbro
"""

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, BOT_USERNAME
from database import Database
from runner import BotRunner
from admin import handle_admin_commands
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
app = Client("hoster_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = Database()
runner = BotRunner(db)

# Welcome message
WELCOME_MESSAGE = """
🎉 **Welcome to Zero Dev Bot Hoster!**

Host your Telegram bots easily and for **FREE**!

**✨ Features:**
━━━━━━━━━━━━━━━━
🚀 Host unlimited bots
⚡ Auto-restart on crash
📊 Real-time bot status
🔧 Easy script editing
💾 Secure MongoDB storage
📈 Performance monitoring

**📚 Quick Start:**
━━━━━━━━━━━━━━━━
1️⃣ Get your bot token from @BotFather
2️⃣ Use /addbot to add your bot
3️⃣ Send your Python script
4️⃣ Your bot goes live instantly!

**🛠️ Commands:**
━━━━━━━━━━━━━━━━
/addbot - Add a new bot
/mybots - View your bots
/startbot - Start your bot
/stopbot - Stop your bot
/editbot - Edit bot script
/deletebot - Delete a bot
/help - Show this message

━━━━━━━━━━━━━━━━
⚡ **Powered by Zero Dev Bro**
📢 **Updates:** @zerodevbro
👨‍💻 **Developer:** @Zeroboy216
"""

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Add user to database
    await db.add_user(user_id, message.from_user.first_name)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
            InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
        ],
        [
            InlineKeyboardButton("📚 Help", callback_data="help"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/zerodevbro"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Zeroboy216")
        ]
    ])
    
    await message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# Help command
@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
            InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ],
        [
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/zerodevbro"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Zeroboy216")
        ]
    ])
    
    await message.reply_text(
        WELCOME_MESSAGE, 
        reply_markup=keyboard, 
        disable_web_page_preview=True
    )

# Add bot command
@app.on_message(filters.command("addbot") & filters.private)
async def add_bot_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ])
    
    msg = await message.reply_text(
        "**🤖 Add Your Bot**\n\n"
        "Please send me your bot token from @BotFather\n\n"
        "**Example:** `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
        "Click Cancel to stop this operation.",
        reply_markup=keyboard
    )
    
    # Store state
    await db.set_user_state(user_id, "waiting_token", msg.id)

# My bots command
@app.on_message(filters.command("mybots") & filters.private)
async def my_bots_command(client: Client, message: Message):
    user_id = message.from_user.id
    bots = await db.get_user_bots(user_id)
    
    if not bots:
        await message.reply_text(
            "❌ You don't have any bots yet!\n\n"
            "Use /addbot to add your first bot."
        )
        return
    
    text = "**📋 Your Hosted Bots:**\n\n"
    keyboards = []
    
    for idx, bot in enumerate(bots, 1):
        status = "🟢 Running" if bot.get("status") == "running" else "🔴 Stopped"
        text += f"{idx}. **Bot ID:** `{bot['_id']}`\n"
        text += f"   Status: {status}\n"
        text += f"   Created: {bot.get('created_at', 'N/A')}\n\n"
        
        keyboards.append([
            InlineKeyboardButton(
                f"{'⏹️ Stop' if bot.get('status') == 'running' else '▶️ Start'} Bot {idx}",
                callback_data=f"toggle_{bot['_id']}"
            ),
            InlineKeyboardButton(f"✏️ Edit {idx}", callback_data=f"edit_{bot['_id']}")
        ])
        keyboards.append([
            InlineKeyboardButton(f"🗑️ Delete Bot {idx}", callback_data=f"delete_{bot['_id']}")
        ])
    
    keyboards.append([InlineKeyboardButton("🔄 Refresh", callback_data="my_bots")])
    
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboards)
    )

# Handle messages based on user state
@app.on_message(filters.private & ~filters.command(["start", "help", "mybots", "addbot", "cancel", "broadcast", "total", "restart", "stats"]))
async def handle_message(client: Client, message: Message):
    user_id = message.from_user.id
    state = await db.get_user_state(user_id)
    
    if not state:
        await message.reply_text("Please use /start to begin.")
        return
    
    if state["action"] == "waiting_token":
        await handle_token_input(client, message, state)
    elif state["action"] == "waiting_script":
        await handle_script_input(client, message, state)
    elif state["action"] == "editing_script":
        await handle_script_edit(client, message, state)

async def handle_token_input(client: Client, message: Message, state):
    user_id = message.from_user.id
    token = message.text.strip()
    
    # Validate token format
    if not token or ":" not in token:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await message.reply_text(
            "❌ **Invalid token format!**\n\n"
            "Token should look like:\n"
            "`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
            "Try again or click Cancel.",
            reply_markup=keyboard
        )
        return
    
    # Verify token
    processing = await message.reply_text("⏳ **Verifying bot token...**\n\nPlease wait...")
    
    is_valid, bot_info = await runner.verify_token(token)
    
    if not is_valid:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await processing.edit_text(
            "❌ **Invalid bot token!**\n\n"
            "Please check your token and try again.\n"
            "Get your token from @BotFather",
            reply_markup=keyboard
        )
        await db.clear_user_state(user_id)
        return
    
    # Save token temporarily
    await db.set_user_state(user_id, "waiting_script", None, {"token": token, "bot_info": bot_info})
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ])
    
    await processing.edit_text(
        f"✅ **Bot Verified Successfully!**\n\n"
        f"**Bot Name:** {bot_info['first_name']}\n"
        f"**Username:** @{bot_info['username']}\n\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"Now send me your **Python bot script**.\n\n"
        f"**Example Script:**\n"
        f"```python\n"
        f"from pyrogram import filters\n\n"
        f"@bot.on_message(filters.command('start'))\n"
        f"async def start(client, message):\n"
        f"    await message.reply('Hello!')\n"
        f"```\n\n"
        f"Click Cancel to stop.",
        reply_markup=keyboard
    )

async def handle_script_input(client: Client, message: Message, state):
    user_id = message.from_user.id
    script = message.text
    
    # Validate script
    if not script or len(script) < 10:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await message.reply_text(
            "❌ **Script too short!**\n\n"
            "Please send a valid Python script.\n"
            "Minimum 10 characters required.",
            reply_markup=keyboard
        )
        return
    
    processing = await message.reply_text(
        "⏳ **Processing your bot...**\n\n"
        "🔍 Validating script...\n"
        "⚙️ Setting up bot...\n"
        "🚀 Starting bot...\n\n"
        "Please wait..."
    )
    
    # Get token from state
    token = state.get("data", {}).get("token")
    bot_info = state.get("data", {}).get("bot_info")
    
    if not token:
        await processing.edit_text("❌ Session expired. Please start over with /addbot")
        await db.clear_user_state(user_id)
        return
    
    # Validate script safety
    is_safe, error = await runner.validate_script(script)
    if not is_safe:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await processing.edit_text(
            f"❌ **Script Validation Failed!**\n\n"
            f"**Reason:** {error}\n\n"
            f"Please fix your script and try again.",
            reply_markup=keyboard
        )
        return
    
    # Save to database
    bot_id = await db.add_bot(user_id, token, script, bot_info)
    
    # Start the bot
    success = await runner.start_bot(bot_id, token, script)
    
    if success:
        await db.update_bot_status(bot_id, "running")
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")],
            [InlineKeyboardButton("➕ Add Another Bot", callback_data="add_bot")],
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
        
        await processing.edit_text(
            f"✅ **Bot Started Successfully!**\n\n"
            f"**Bot Name:** {bot_info['first_name']}\n"
            f"**Username:** @{bot_info['username']}\n"
            f"**Bot ID:** `{bot_id}`\n"
            f"**Status:** 🟢 Running\n\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"Your bot is now live and ready to use!\n\n"
            f"Use /mybots to manage your bots.\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚡ **Powered by Zero Dev Bro**\n"
            f"📢 **Updates:** @zerodevbro",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
        await processing.edit_text(
            "❌ **Failed to start bot!**\n\n"
            "There was an error starting your bot.\n"
            "Please check your script and try again.\n\n"
            "If the problem persists, contact @Zeroboy216",
            reply_markup=keyboard
        )
        await db.delete_bot(bot_id)
    
    await db.clear_user_state(user_id)

async def handle_script_edit(client: Client, message: Message, state):
    user_id = message.from_user.id
    script = message.text
    bot_id = state.get("data", {}).get("bot_id")
    
    processing = await message.reply_text(
        "⏳ **Updating bot script...**\n\n"
        "Please wait..."
    )
    
    # Validate script
    is_safe, error = await runner.validate_script(script)
    if not is_safe:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to My Bots", callback_data="my_bots")]
        ])
        await processing.edit_text(
            f"❌ **Script Validation Failed!**\n\n"
            f"**Reason:** {error}\n\n"
            f"Please fix your script and try again.",
            reply_markup=keyboard
        )
        return
    
    # Update script
    await db.update_bot_script(bot_id, script)
    
    # Restart bot
    bot = await db.get_bot(bot_id)
    await runner.stop_bot(bot_id)
    success = await runner.start_bot(bot_id, bot["token"], script)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")],
        [InlineKeyboardButton("🏠 Home", callback_data="start")]
    ])
    
    if success:
        await db.update_bot_status(bot_id, "running")
        await processing.edit_text(
            "✅ **Bot Script Updated Successfully!**\n\n"
            f"**Bot:** @{bot.get('bot_username', 'unknown')}\n"
            f"**Status:** 🟢 Running\n\n"
            "Your bot has been restarted with the new script.\n\n"
            "Use /mybots to see all your bots.",
            reply_markup=keyboard
        )
    else:
        await processing.edit_text(
            "❌ **Failed to restart bot with new script!**\n\n"
            "The script has been saved but the bot couldn't start.\n"
            "Please check your script.\n\n"
            "Contact @Zeroboy216 if the problem persists.",
            reply_markup=keyboard
        )
    
    await db.clear_user_state(user_id)

# Callback query handler
@app.on_callback_query()
async def callback_handler(client: Client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "start":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
                InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
            ],
            [
                InlineKeyboardButton("📚 Help", callback_data="help"),
                InlineKeyboardButton("📊 Stats", callback_data="stats")
            ],
            [
                InlineKeyboardButton("📢 Updates Channel", url="https://t.me/zerodevbro"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Zeroboy216")
            ]
        ])
        
        try:
            await callback_query.message.edit_text(
                WELCOME_MESSAGE,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                WELCOME_MESSAGE,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        await callback_query.answer()
    
    elif data == "add_bot":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        
        try:
            await callback_query.message.edit_text(
                "**🤖 Add Your Bot**\n\n"
                "Please send me your bot token from @BotFather\n\n"
                "**Example:** `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
                "Click Cancel to stop this operation.",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                "**🤖 Add Your Bot**\n\n"
                "Please send me your bot token from @BotFather\n\n"
                "**Example:** `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
                "Click Cancel to stop this operation.",
                reply_markup=keyboard
            )
        await db.set_user_state(user_id, "waiting_token", None)
        await callback_query.answer()
    
    elif data == "cancel_operation":
        await db.clear_user_state(user_id)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
        try:
            await callback_query.message.edit_text(
                "✅ **Operation Cancelled**\n\n"
                "Click Home to return to main menu.",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                "✅ **Operation Cancelled**\n\n"
                "Click Home to return to main menu.",
                reply_markup=keyboard
            )
        await callback_query.answer("❌ Cancelled")
        
    elif data == "my_bots":
        await callback_query.answer()
        bots = await db.get_user_bots(user_id)
        
        if not bots:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")],
                [InlineKeyboardButton("🔙 Back", callback_data="start")]
            ])
            
            try:
                await callback_query.message.edit_text(
                    "❌ **You don't have any bots yet!**\n\n"
                    "Use Add Bot button to add your first bot.",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                await callback_query.message.reply_text(
                    "❌ **You don't have any bots yet!**\n\n"
                    "Use Add Bot button to add your first bot.",
                    reply_markup=keyboard
                )
            return
        
        text = "**📋 Your Hosted Bots:**\n\n"
        keyboards = []
        
        for idx, bot in enumerate(bots, 1):
            status = "🟢 Running" if bot.get("status") == "running" else "🔴 Stopped"
            text += f"{idx}. **Bot:** @{bot.get('bot_username', 'unknown')}\n"
            text += f"   **ID:** `{bot['_id']}`\n"
            text += f"   **Status:** {status}\n"
            text += f"   **Created:** {bot.get('created_at', 'N/A')}\n\n"
            
            keyboards.append([
                InlineKeyboardButton(
                    f"{'⏹️ Stop' if bot.get('status') == 'running' else '▶️ Start'} Bot {idx}",
                    callback_data=f"toggle_{bot['_id']}"
                ),
                InlineKeyboardButton(f"✏️ Edit {idx}", callback_data=f"edit_{bot['_id']}")
            ])
            keyboards.append([
                InlineKeyboardButton(f"🗑️ Delete Bot {idx}", callback_data=f"delete_confirm_{bot['_id']}")
            ])
        
        keyboards.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="my_bots"),
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ])
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )
        
    elif data == "help":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
                InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
                InlineKeyboardButton("🔙 Back", callback_data="start")
            ],
            [
                InlineKeyboardButton("📢 Updates Channel", url="https://t.me/zerodevbro"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Zeroboy216")
            ]
        ])
        
        try:
            await callback_query.message.edit_text(
                WELCOME_MESSAGE,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                WELCOME_MESSAGE,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        await callback_query.answer()
    
    elif data == "stats":
        stats = await db.get_stats()
        
        stats_text = f"""
📊 **Bot Hoster Statistics**

**🤖 Bots:**
━━━━━━━━━━━━━━━━
Total Bots: `{stats['total_bots']}`
🟢 Running: `{stats['running_bots']}`
🔴 Stopped: `{stats['stopped_bots']}`

**👥 Users:**
━━━━━━━━━━━━━━━━
Total Users: `{stats['total_users']}`

━━━━━━━━━━━━━━━━
⚡ **Powered by Zero Dev Bro**
📢 **Updates:** @zerodevbro
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ])
        
        try:
            await callback_query.message.edit_text(
                stats_text,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                stats_text,
                reply_markup=keyboard
            )
        await callback_query.answer()
        
    elif data.startswith("toggle_"):
        bot_id = data.split("_")[1]
        bot = await db.get_bot(bot_id)
        
        if not bot:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        if bot["user_id"] != user_id:
            await callback_query.answer("❌ Not your bot!", show_alert=True)
            return
        
        if bot["status"] == "running":
            await runner.stop_bot(bot_id)
            await db.update_bot_status(bot_id, "stopped")
            await callback_query.answer("⏹️ Bot stopped!")
        else:
            success = await runner.start_bot(bot_id, bot["token"], bot["script"])
            if success:
                await db.update_bot_status(bot_id, "running")
                await callback_query.answer("▶️ Bot started!")
            else:
                await callback_query.answer("❌ Failed to start bot!", show_alert=True)
                return
        
        # Refresh the bots list
        bots = await db.get_user_bots(user_id)
        text = "**📋 Your Hosted Bots:**\n\n"
        keyboards = []
        
        for idx, bot in enumerate(bots, 1):
            status = "🟢 Running" if bot.get("status") == "running" else "🔴 Stopped"
            text += f"{idx}. **Bot:** @{bot.get('bot_username', 'unknown')}\n"
            text += f"   **ID:** `{bot['_id']}`\n"
            text += f"   **Status:** {status}\n"
            text += f"   **Created:** {bot.get('created_at', 'N/A')}\n\n"
            
            keyboards.append([
                InlineKeyboardButton(
                    f"{'⏹️ Stop' if bot.get('status') == 'running' else '▶️ Start'} Bot {idx}",
                    callback_data=f"toggle_{bot['_id']}"
                ),
                InlineKeyboardButton(f"✏️ Edit {idx}", callback_data=f"edit_{bot['_id']}")
            ])
            keyboards.append([
                InlineKeyboardButton(f"🗑️ Delete Bot {idx}", callback_data=f"delete_confirm_{bot['_id']}")
            ])
        
        keyboards.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="my_bots"),
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ])
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
        
    elif data.startswith("edit_"):
        bot_id = data.split("_")[1]
        bot = await db.get_bot(bot_id)
        
        if not bot:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        if bot["user_id"] != user_id:
            await callback_query.answer("❌ Not your bot!", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="my_bots")]
        ])
        
        try:
            await callback_query.message.edit_text(
                "**✏️ Edit Bot Script**\n\n"
                f"**Bot:** @{bot.get('bot_username', 'unknown')}\n\n"
                "Send me the new Python script for your bot.\n\n"
                "Click Cancel to go back.",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                "**✏️ Edit Bot Script**\n\n"
                f"**Bot:** @{bot.get('bot_username', 'unknown')}\n\n"
                "Send me the new Python script for your bot.\n\n"
                "Click Cancel to go back.",
                reply_markup=keyboard
            )
        
        await db.set_user_state(user_id, "editing_script", None, {"bot_id": bot_id})
        await callback_query.answer()
        
    elif data.startswith("delete_confirm_"):
        bot_id = data.split("_", 2)[2]
        bot = await db.get_bot(bot_id)
        
        if not bot:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        if bot["user_id"] != user_id:
            await callback_query.answer("❌ Not your bot!", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes, Delete", callback_data=f"delete_{bot_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="my_bots")
            ]
        ])
        
        try:
            await callback_query.message.edit_text(
                f"**⚠️ Confirm Delete**\n\n"
                f"Are you sure you want to delete this bot?\n\n"
                f"**Bot:** @{bot.get('bot_username', 'unknown')}\n"
                f"**ID:** `{bot_id}`\n\n"
                f"**This action cannot be undone!**",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                f"**⚠️ Confirm Delete**\n\n"
                f"Are you sure you want to delete this bot?\n\n"
                f"**Bot:** @{bot.get('bot_username', 'unknown')}\n"
                f"**ID:** `{bot_id}`\n\n"
                f"**This action cannot be undone!**",
                reply_markup=keyboard
            )
        await callback_query.answer()
    
    elif data.startswith("delete_"):
        bot_id = data.split("_")[1]
        bot = await db.get_bot(bot_id)
        
        if not bot:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        if bot["user_id"] != user_id:
            await callback_query.answer("❌ Not your bot!", show_alert=True)
            return
        
        await runner.stop_bot(bot_id)
        await db.delete_bot(bot_id)
        
        await callback_query.answer("🗑️ Bot deleted!")
        
        # Show updated bots list
        bots = await db.get_user_bots(user_id)
        
        if not bots:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")],
                [InlineKeyboardButton("🔙 Back", callback_data="start")]
            ])
            
            try:
                await callback_query.message.edit_text(
                    "✅ **Bot Deleted Successfully!**\n\n"
                    "❌ You don't have any bots now.\n\n"
                    "Use Add Bot button to add a new bot.",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                await callback_query.message.reply_text(
                    "✅ **Bot Deleted Successfully!**\n\n"
                    "❌ You don't have any bots now.\n\n"
                    "Use Add Bot button to add a new bot.",
                    reply_markup=keyboard
                )
            return
        
        text = "✅ **Bot Deleted Successfully!**\n\n**📋 Your Remaining Bots:**\n\n"
        keyboards = []
        
        for idx, bot in enumerate(bots, 1):
            status = "🟢 Running" if bot.get("status") == "running" else "🔴 Stopped"
            text += f"{idx}. **Bot:** @{bot.get('bot_username', 'unknown')}\n"
            text += f"   **ID:** `{bot['_id']}`\n"
            text += f"   **Status:** {status}\n\n"
            
            keyboards.append([
                InlineKeyboardButton(
                    f"{'⏹️ Stop' if bot.get('status') == 'running' else '▶️ Start'} Bot {idx}",
                    callback_data=f"toggle_{bot['_id']}"
                ),
                InlineKeyboardButton(f"✏️ Edit {idx}", callback_data=f"edit_{bot['_id']}")
            ])
            keyboards.append([
                InlineKeyboardButton(f"🗑️ Delete Bot {idx}", callback_data=f"delete_confirm_{bot['_id']}")
            ])
        
        keyboards.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="my_bots"),
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ])
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await callback_query.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )

# Admin commands
@app.on_message(filters.command(["broadcast", "total", "restart", "stats"]) & filters.user(OWNER_ID))
async def admin_commands(client: Client, message: Message):
    await handle_admin_commands(client, message, db, runner)

# Cancel command
@app.on_message(filters.command("cancel") & filters.private)
async def cancel_command(client: Client, message: Message):
    user_id = message.from_user.id
    await db.clear_user_state(user_id)
    await message.reply_text("✅ Operation cancelled.")

# Run the bot
if __name__ == "__main__":
    logger.info("Starting Bot Hoster...")
    app.run()
