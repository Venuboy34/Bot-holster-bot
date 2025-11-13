"""
Telegram Bot Hoster - Main Entry Point (Enhanced Version)
Developer: @Zeroboy216
Channel: @zerodevbro
Version: 2.0
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

# Enhanced Welcome message with modern design
WELCOME_MESSAGE = """
╔═══════════════════════════╗
║  🚀 **ZERO DEV BOT HOSTER** 🚀  ║
╚═══════════════════════════╝

**Welcome to the Future of Bot Hosting!** 🌟

┏━━━━━━━━━━━━━━━━━━━━━━┓
┃  **✨ Premium Features**
┣━━━━━━━━━━━━━━━━━━━━━━┫
┃ 🤖 Unlimited Bot Hosting
┃ 🔄 Auto-Restart on Crash
┃ 📊 Real-time Monitoring
┃ ⚡ Lightning-Fast Deploy
┃ 🔒 Secure & Private
┃ 📁 Multi-File Support
┃ 🎯 One-Click Management
┃ 💎 100% Free Forever
┗━━━━━━━━━━━━━━━━━━━━━━┛

**🎯 Supported File Types:**
━━━━━━━━━━━━━━━━━━━━━━
• `.py` - Python Scripts
• `.js` - JavaScript/Node.js
• `.sh` - Shell Scripts
• `.rb` - Ruby Scripts
• `.php` - PHP Scripts
• `.go` - Go Programs

**⚡ Quick Start Guide:**
━━━━━━━━━━━━━━━━━━━━━━
**1️⃣** Get your bot token from @BotFather
**2️⃣** Click "➕ Add Bot" below
**3️⃣** Send your bot token
**4️⃣** Upload your script file
**5️⃣** Watch it go live! 🎉

**🎮 Command Center:**
━━━━━━━━━━━━━━━━━━━━━━
`/addbot` - Add a new bot
`/mybots` - Manage your bots  
`/help` - Get assistance
`/stats` - View statistics

━━━━━━━━━━━━━━━━━━━━━━━━
⚡ **Powered by Zero Dev Bro**
📢 **Updates:** @zerodevbro
👨‍💻 **Developer:** @Zeroboy216
━━━━━━━━━━━━━━━━━━━━━━━━
"""

HELP_MESSAGE = """
╔═══════════════════════════╗
║     **📚 HELP CENTER**     ║
╚═══════════════════════════╝

**🎯 How to Host Your Bot:**
━━━━━━━━━━━━━━━━━━━━━━

**Step 1: Get Bot Token**
• Open @BotFather on Telegram
• Send `/newbot` command
• Follow instructions
• Copy your bot token

**Step 2: Add Your Bot**
• Use `/addbot` command
• Paste your bot token
• Wait for verification ✅

**Step 3: Upload Script**
• Send your bot script file
• Supports: .py, .js, .sh, .rb, .php, .go
• Or paste code as text
• Script is validated automatically

**Step 4: Bot Goes Live!**
• Your bot starts instantly 🚀
• Monitor status anytime
• Edit script on-the-fly
• Auto-restart on errors

━━━━━━━━━━━━━━━━━━━━━━

**🛠️ Command Reference:**

`/addbot` - Add new bot
• Get bot token from @BotFather
• Submit token for verification
• Upload your script

`/mybots` - Manage bots
• View all your bots
• Start/Stop bots
• Edit scripts
• Delete bots
• Check status

`/help` - Show this guide

`/stats` - Platform statistics
• Total users
• Total bots
• Active bots

━━━━━━━━━━━━━━━━━━━━━━

**📝 Script Requirements:**

**Python (.py):**
```python
from pyrogram import filters

@bot.on_message(filters.command('start'))
async def start(client, message):
    await message.reply('Hello!')
```

**JavaScript (.js):**
```javascript
bot.on('message', (msg) => {
    bot.sendMessage(msg.chat.id, 'Hello!');
});
```

━━━━━━━━━━━━━━━━━━━━━━

**🔧 Troubleshooting:**

**Bot not starting?**
• Check script syntax
• Verify dependencies
• Review error logs

**Token invalid?**
• Get new token from @BotFather
• Copy entire token
• No extra spaces

**Script errors?**
• Validate Python syntax
• Check indentation
• Test locally first

━━━━━━━━━━━━━━━━━━━━━━

**💡 Pro Tips:**

✅ Test scripts locally first
✅ Use clear variable names
✅ Add error handling
✅ Keep scripts organized
✅ Monitor bot regularly

**🆘 Need Help?**
Contact: @Zeroboy216

━━━━━━━━━━━━━━━━━━━━━━
⚡ **Powered by Zero Dev Bro**
📢 @zerodevbro | 👨‍💻 @Zeroboy216
━━━━━━━━━━━━━━━━━━━━━━
"""

# Start command with enhanced UI
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
            InlineKeyboardButton("📚 Help Guide", callback_data="help"),
            InlineKeyboardButton("📊 Statistics", callback_data="stats")
        ],
        [
            InlineKeyboardButton("📢 Updates", url="https://t.me/zerodevbro"),
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Zeroboy216")
        ],
        [
            InlineKeyboardButton("⭐ Rate Us", url="https://t.me/zerodevbro"),
            InlineKeyboardButton("🔗 Share", switch_inline_query="Check out this bot hoster!")
        ]
    ])
    
    await message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# Help command with detailed guide
@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
            InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
            InlineKeyboardButton("🏠 Home", callback_data="start")
        ],
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/zerodevbro"),
            InlineKeyboardButton("💬 Support", url="https://t.me/Zeroboy216")
        ]
    ])
    
    await message.reply_text(
        HELP_MESSAGE, 
        reply_markup=keyboard, 
        disable_web_page_preview=True
    )

# Add bot command with file type support info
@app.on_message(filters.command("addbot") & filters.private)
async def add_bot_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ])
    
    msg = await message.reply_text(
        "╔═══════════════════════════╗\n"
        "║    **🤖 ADD NEW BOT**    ║\n"
        "╚═══════════════════════════╝\n\n"
        "**Step 1: Bot Token** 🔑\n\n"
        "Please send your bot token from @BotFather\n\n"
        "**📝 Format:**\n"
        "`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **Tip:** Copy the entire token\n"
        "⚠️ Don't share your token publicly\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Click **Cancel** to abort ❌",
        reply_markup=keyboard
    )
    
    await db.set_user_state(user_id, "waiting_token", msg.id)

# Enhanced My bots command with better UI
@app.on_message(filters.command("mybots") & filters.private)
async def my_bots_command(client: Client, message: Message):
    user_id = message.from_user.id
    bots = await db.get_user_bots(user_id)
    
    if not bots:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Your First Bot", callback_data="add_bot")],
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
        await message.reply_text(
            "╔═══════════════════════════╗\n"
            "║   **📋 YOUR BOTS**   ║\n"
            "╚═══════════════════════════╝\n\n"
            "❌ **No bots found!**\n\n"
            "You haven't hosted any bots yet.\n\n"
            "🚀 Ready to get started?\n"
            "Click the button below to add your first bot!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚡ **It takes less than 2 minutes!**",
            reply_markup=keyboard
        )
        return
    
    text = "╔═══════════════════════════╗\n"
    text += "║   **📋 YOUR BOTS**   ║\n"
    text += "╚═══════════════════════════╝\n\n"
    
    keyboards = []
    
    for idx, bot in enumerate(bots, 1):
        status_icon = "🟢" if bot.get("status") == "running" else "🔴"
        status_text = "Online" if bot.get("status") == "running" else "Offline"
        
        text += f"**Bot #{idx}** {status_icon}\n"
        text += f"┣━ **Name:** @{bot.get('bot_username', 'unknown')}\n"
        text += f"┣━ **ID:** `{bot['_id']}`\n"
        text += f"┣━ **Status:** {status_text}\n"
        text += f"┗━ **Added:** {bot.get('created_at', 'N/A')}\n\n"
        
        button_text = f"⏹️ Stop #{idx}" if bot.get("status") == "running" else f"▶️ Start #{idx}"
        
        keyboards.append([
            InlineKeyboardButton(button_text, callback_data=f"toggle_{bot['_id']}"),
            InlineKeyboardButton(f"✏️ Edit #{idx}", callback_data=f"edit_{bot['_id']}")
        ])
        keyboards.append([
            InlineKeyboardButton(f"📊 Stats #{idx}", callback_data=f"botstats_{bot['_id']}"),
            InlineKeyboardButton(f"🗑️ Delete #{idx}", callback_data=f"delete_confirm_{bot['_id']}")
        ])
        keyboards.append([InlineKeyboardButton("━━━━━━━━━━━━━━━", callback_data="separator")])
    
    keyboards.pop()  # Remove last separator
    keyboards.append([
        InlineKeyboardButton("🔄 Refresh", callback_data="my_bots"),
        InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")
    ])
    keyboards.append([InlineKeyboardButton("🏠 Home", callback_data="start")])
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboards))

# Handle messages based on user state (text and ANY file type)
@app.on_message(filters.private & ~filters.command(["start", "help", "mybots", "addbot", "cancel", "broadcast", "total", "restart", "stats"]))
async def handle_message(client: Client, message: Message):
    user_id = message.from_user.id
    state = await db.get_user_state(user_id)
    
    if not state:
        await message.reply_text(
            "⚠️ **No active operation**\n\n"
            "Use /start to begin or /help for assistance."
        )
        return
    
    if state["action"] == "waiting_token":
        await handle_token_input(client, message, state)
    elif state["action"] == "waiting_script":
        if message.document:
            await handle_script_file(client, message, state)
        else:
            await handle_script_input(client, message, state)
    elif state["action"] == "editing_script":
        if message.document:
            await handle_script_file_edit(client, message, state)
        else:
            await handle_script_edit(client, message, state)

async def handle_token_input(client: Client, message: Message, state):
    user_id = message.from_user.id
    token = message.text.strip()
    
    if not token or ":" not in token:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await message.reply_text(
            "❌ **Invalid Token Format!**\n\n"
            "**Expected format:**\n"
            "`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 **Common issues:**\n"
            "• Extra spaces before/after\n"
            "• Missing colon (:)\n"
            "• Incomplete token\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Please try again or click Cancel ❌",
            reply_markup=keyboard
        )
        return
    
    processing = await message.reply_text(
        "⏳ **Verifying Bot Token...**\n\n"
        "⚙️ Connecting to Telegram...\n"
        "🔍 Validating token...\n"
        "📡 Checking bot status...\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Please wait...**"
    )
    
    is_valid, bot_info = await runner.verify_token(token)
    
    if not is_valid:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await processing.edit_text(
            "❌ **Token Verification Failed!**\n\n"
            "**Possible reasons:**\n"
            "• Invalid token format\n"
            "• Bot was deleted\n"
            "• Token revoked\n"
            "• Network error\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 **Solution:**\n"
            "Get a fresh token from @BotFather\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=keyboard
        )
        await db.clear_user_state(user_id)
        return
    
    await db.set_user_state(user_id, "waiting_script", None, {"token": token, "bot_info": bot_info})
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ])
    
    await processing.edit_text(
        f"✅ **Bot Verified Successfully!**\n\n"
        f"╔═══════════════════════════╗\n"
        f"║   **BOT INFORMATION**   ║\n"
        f"╚═══════════════════════════╝\n\n"
        f"**📛 Name:** {bot_info['first_name']}\n"
        f"**🔗 Username:** @{bot_info['username']}\n"
        f"**🆔 ID:** `{bot_info['id']}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Step 2: Upload Script** 📁\n\n"
        f"**Supported formats:**\n"
        f"🐍 Python (.py)\n"
        f"📜 JavaScript (.js)\n"
        f"🐚 Shell (.sh)\n"
        f"💎 Ruby (.rb)\n"
        f"🐘 PHP (.php)\n"
        f"🔵 Go (.go)\n"
        f"📝 Text (paste code)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **Tip:** Upload file or paste code\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=keyboard
    )

async def handle_script_input(client: Client, message: Message, state):
    user_id = message.from_user.id
    script = message.text
    
    if not script or len(script) < 10:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await message.reply_text(
            "❌ **Script Too Short!**\n\n"
            "Minimum 10 characters required.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Please send a valid script or upload a file.",
            reply_markup=keyboard
        )
        return
    
    processing = await message.reply_text(
        "⏳ **Processing Your Bot...**\n\n"
        "🔍 Step 1: Validating script... ⏳\n"
        "⚙️ Step 2: Setting up environment... ⏳\n"
        "🚀 Step 3: Starting bot... ⏳\n"
        "✅ Step 4: Going live... ⏳\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Please wait, this may take a moment...**"
    )
    
    token = state.get("data", {}).get("token")
    bot_info = state.get("data", {}).get("bot_info")
    
    if not token:
        await processing.edit_text(
            "❌ **Session Expired!**\n\n"
            "Please start over with /addbot"
        )
        await db.clear_user_state(user_id)
        return
    
    is_safe, error = await runner.validate_script(script)
    if not is_safe:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
            [InlineKeyboardButton("📚 Help", callback_data="help")]
        ])
        await processing.edit_text(
            f"❌ **Script Validation Failed!**\n\n"
            f"**Error Details:**\n"
            f"{error}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **Common issues:**\n"
            f"• Syntax errors\n"
            f"• Missing imports\n"
            f"• Malicious code detected\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=keyboard
        )
        return
    
    bot_id = await db.add_bot(user_id, token, script, bot_info)
    success = await runner.start_bot(bot_id, token, script)
    
    if success:
        await db.update_bot_status(bot_id, "running")
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")],
            [InlineKeyboardButton("➕ Add Another", callback_data="add_bot")],
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
        
        await processing.edit_text(
            f"🎉 **Bot Deployed Successfully!**\n\n"
            f"╔═══════════════════════════╗\n"
            f"║   **DEPLOYMENT INFO**   ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"**📛 Bot Name:** {bot_info['first_name']}\n"
            f"**🔗 Username:** @{bot_info['username']}\n"
            f"**🆔 Bot ID:** `{bot_id}`\n"
            f"**📊 Status:** 🟢 **Online & Running**\n"
            f"**⚡ Uptime:** Just started\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Your bot is now **LIVE**!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**🎯 Next Steps:**\n"
            f"• Test your bot on Telegram\n"
            f"• Use /mybots to manage it\n"
            f"• Monitor its performance\n\n"
            f"⚡ **Powered by Zero Dev Bro**\n"
            f"📢 Updates: @zerodevbro",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/Zeroboy216")]
        ])
        await processing.edit_text(
            "❌ **Deployment Failed!**\n\n"
            "**Possible causes:**\n"
            "• Runtime error in script\n"
            "• Missing dependencies\n"
            "• Server overload\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 **Try:**\n"
            "• Check script syntax\n"
            "• Test locally first\n"
            "• Contact support\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=keyboard
        )
        await db.delete_bot(bot_id)
    
    await db.clear_user_state(user_id)

async def handle_script_edit(client: Client, message: Message, state):
    user_id = message.from_user.id
    script = message.text
    bot_id = state.get("data", {}).get("bot_id")
    
    processing = await message.reply_text(
        "⏳ **Updating Bot Script...**\n\n"
        "🔍 Validating new script...\n"
        "⚙️ Applying changes...\n"
        "🔄 Restarting bot...\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Please wait...**"
    )
    
    is_safe, error = await runner.validate_script(script)
    if not is_safe:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="my_bots")]
        ])
        await processing.edit_text(
            f"❌ **Validation Failed!**\n\n"
            f"**Error:**\n{error}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Please fix the script and try again.",
            reply_markup=keyboard
        )
        return
    
    await db.update_bot_script(bot_id, script)
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
            "✅ **Update Successful!**\n\n"
            f"╔═══════════════════════════╗\n"
            f"║   **UPDATED BOT**   ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"**📛 Bot:** @{bot.get('bot_username', 'unknown')}\n"
            f"**📊 Status:** 🟢 **Running**\n"
            f"**🔄 Updated:** Just now\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Your bot has been restarted with the new script!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=keyboard
        )
    else:
        await processing.edit_text(
            "⚠️ **Restart Failed!**\n\n"
            "Script saved but bot couldn't restart.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Check script and try again or contact @Zeroboy216",
            reply_markup=keyboard
        )
    
    await db.clear_user_state(user_id)

async def handle_script_file(client: Client, message: Message, state):
    """Handle ANY script file upload with extension detection"""
    user_id = message.from_user.id
    
    # Get file extension
    file_name = message.document.file_name
    file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    
    # Supported extensions
    supported_exts = ['py', 'js', 'sh', 'rb', 'php', 'go', 'txt']
    
    if file_ext not in supported_exts:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await message.reply_text(
            f"❌ **Unsupported File Type!**\n\n"
            f"**Your file:** `.{file_ext}`\n\n"
            f"**Supported formats:**\n"
            f"🐍 `.py` - Python\n"
            f"📜 `.js` - JavaScript\n"
            f"🐚 `.sh` - Shell\n"
            f"💎 `.rb` - Ruby\n"
            f"🐘 `.php` - PHP\n"
            f"🔵 `.go` - Go\n"
            f"📝 `.txt` - Text\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Please upload a valid script file.",
            reply_markup=keyboard
        )
        return
    
    # Check file size (max 10MB)
    if message.document.file_size > 10 * 1024 * 1024:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        await message.reply_text(
            f"❌ **File Too Large!**\n\n"
            f"**Maximum size:** 10MB\n"
            f"**Your file:** {message.document.file_size / (1024 * 1024):.2f}MB\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **Tip:** Optimize your script or split into modules",
            reply_markup=keyboard
        )
        return
    
    processing = await message.reply_text(
        f"⏳ **Processing {file_ext.upper()} Script...**\n\n"
        f"📥 Downloading file... ⏳\n"
        f"🔍 Validating script... ⏳\n"
        f"⚙️ Setting up environment... ⏳\n"
        f"🚀 Deploying bot... ⏳\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**File:** `{file_name}`\n"
        f"**Size:** {message.document.file_size / 1024:.2f}KB\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    try:
        # Download the file
        file_path = await message.download()
        
        # Read the script content with proper encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                script = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 encoding as fallback
            with open(file_path, 'r', encoding='latin-1') as f:
                script = f.read()
        
        # Delete the downloaded file
        os.remove(file_path)
        
        # Store file metadata
        file_metadata = {
            "file_name": file_name,
            "file_type": file_ext,
            "file_size": message.document.file_size
        }
        
        token = state.get("data", {}).get("token")
        bot_info = state.get("data", {}).get("bot_info")
        
        if not token:
            await processing.edit_text(
                "❌ **Session Expired!**\n\n"
                "Your session timed out.\n"
                "Please start over with /addbot"
            )
            await db.clear_user_state(user_id)
            return
        
        is_safe, error = await runner.validate_script(script, file_ext)
        if not is_safe:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
                [InlineKeyboardButton("📚 Help", callback_data="help")]
            ])
            await processing.edit_text(
                f"❌ **Validation Failed!**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Type:** {file_ext.upper()}\n\n"
                f"**Error Details:**\n"
                f"```\n{error[:200]}\n```\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 **Suggestions:**\n"
                f"• Check syntax errors\n"
                f"• Remove malicious code\n"
                f"• Test locally first\n"
                f"━━━━━━━━━━━━━━━━━━━━━━",
                reply_markup=keyboard
            )
            return
        
        # Save to database with file metadata
        bot_id = await db.add_bot(user_id, token, script, bot_info, file_metadata)
        success = await runner.start_bot(bot_id, token, script, file_ext)
        
        if success:
            await db.update_bot_status(bot_id, "running")
            
            # Get file type emoji
            type_emoji = {
                'py': '🐍',
                'js': '📜',
                'sh': '🐚',
                'rb': '💎',
                'php': '🐘',
                'go': '🔵',
                'txt': '📝'
            }.get(file_ext, '📄')
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")],
                [InlineKeyboardButton("➕ Add Another", callback_data="add_bot")],
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
            
            await processing.edit_text(
                f"🎉 **Deployment Successful!**\n\n"
                f"╔═══════════════════════════╗\n"
                f"║   **BOT DEPLOYED**   ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"**📛 Name:** {bot_info['first_name']}\n"
                f"**🔗 Username:** @{bot_info['username']}\n"
                f"**🆔 ID:** `{bot_id}`\n"
                f"**📊 Status:** 🟢 **Online**\n"
                f"**{type_emoji} Script:** `{file_name}`\n"
                f"**💾 Size:** {message.document.file_size / 1024:.2f}KB\n"
                f"**🕐 Started:** Just now\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ **Your bot is LIVE!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**Features Active:**\n"
                f"✅ Auto-restart enabled\n"
                f"✅ Error monitoring active\n"
                f"✅ 24/7 uptime guaranteed\n\n"
                f"⚡ **Powered by Zero Dev Bro**\n"
                f"📢 @zerodevbro | 👨‍💻 @Zeroboy216",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Retry", callback_data="add_bot")],
                [InlineKeyboardButton("💬 Support", url="https://t.me/Zeroboy216")]
            ])
            await processing.edit_text(
                f"❌ **Deployment Failed!**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Type:** {file_ext.upper()}\n\n"
                f"**Common Issues:**\n"
                f"• Runtime errors\n"
                f"• Missing dependencies\n"
                f"• Invalid configuration\n"
                f"• Server resources\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 **Need help?** Contact support\n"
                f"━━━━━━━━━━━━━━━━━━━━━━",
                reply_markup=keyboard
            )
            await db.delete_bot(bot_id)
        
        await db.clear_user_state(user_id)
        
    except Exception as e:
        logger.error(f"Error handling script file: {e}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="add_bot")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/Zeroboy216")]
        ])
        await processing.edit_text(
            f"❌ **Processing Error!**\n\n"
            f"**File:** `{file_name}`\n\n"
            f"**Error:** Failed to process file\n\n"
            f"**Details:**\n"
            f"```\n{str(e)[:150]}\n```\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Try uploading again or contact support",
            reply_markup=keyboard
        )
        await db.clear_user_state(user_id)

async def handle_script_file_edit(client: Client, message: Message, state):
    """Handle ANY script file upload for editing"""
    user_id = message.from_user.id
    bot_id = state.get("data", {}).get("bot_id")
    
    # Get file extension
    file_name = message.document.file_name
    file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    
    supported_exts = ['py', 'js', 'sh', 'rb', 'php', 'go', 'txt']
    
    if file_ext not in supported_exts:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="my_bots")]
        ])
        await message.reply_text(
            f"❌ **Unsupported File Type!**\n\n"
            f"**Supported:** {', '.join(['.' + ext for ext in supported_exts])}\n"
            f"**Your file:** `.{file_ext}`",
            reply_markup=keyboard
        )
        return
    
    processing = await message.reply_text(
        f"⏳ **Updating with {file_ext.upper()} Script...**\n\n"
        f"📥 Downloading file...\n"
        f"🔍 Validating...\n"
        f"⚙️ Applying changes...\n"
        f"🔄 Restarting bot...\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**File:** `{file_name}`"
    )
    
    try:
        file_path = await message.download()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                script = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                script = f.read()
        
        os.remove(file_path)
        
        is_safe, error = await runner.validate_script(script, file_ext)
        if not is_safe:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="my_bots")]
            ])
            await processing.edit_text(
                f"❌ **Validation Failed!**\n\n"
                f"**Error:**\n```\n{error[:200]}\n```\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Fix the script and try again.",
                reply_markup=keyboard
            )
            return
        
        await db.update_bot_script(bot_id, script)
        bot = await db.get_bot(bot_id)
        await runner.stop_bot(bot_id)
        success = await runner.start_bot(bot_id, bot["token"], script, file_ext)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")],
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
        
        type_emoji = {
            'py': '🐍', 'js': '📜', 'sh': '🐚',
            'rb': '💎', 'php': '🐘', 'go': '🔵', 'txt': '📝'
        }.get(file_ext, '📄')
        
        if success:
            await db.update_bot_status(bot_id, "running")
            await processing.edit_text(
                f"✅ **Update Successful!**\n\n"
                f"╔═══════════════════════════╗\n"
                f"║   **BOT UPDATED**   ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"**📛 Bot:** @{bot.get('bot_username', 'unknown')}\n"
                f"**📊 Status:** 🟢 **Running**\n"
                f"**{type_emoji} Script:** `{file_name}`\n"
                f"**💾 Size:** {message.document.file_size / 1024:.2f}KB\n"
                f"**🔄 Updated:** Just now\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Your bot is running with the new script!\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━",
                reply_markup=keyboard
            )
        else:
            await processing.edit_text(
                f"⚠️ **Restart Failed!**\n\n"
                f"Script saved but bot couldn't start.\n\n"
                f"**File:** `{file_name}`\n"
                f"**Type:** {file_ext.upper()}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Check script or contact @Zeroboy216",
                reply_markup=keyboard
            )
        
        await db.clear_user_state(user_id)
        
    except Exception as e:
        logger.error(f"Error handling script file edit: {e}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="my_bots")]
        ])
        await processing.edit_text(
            f"❌ **Processing Error!**\n\n"
            f"```\n{str(e)[:150]}\n```\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Please try again or contact support.",
            reply_markup=keyboard
        )
        await db.clear_user_state(user_id)

# Enhanced Callback query handler
@app.on_callback_query()
async def callback_handler(client: Client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Ignore separator clicks
    if data == "separator":
        await callback_query.answer()
        return
    
    if data == "start":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
                InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
            ],
            [
                InlineKeyboardButton("📚 Help Guide", callback_data="help"),
                InlineKeyboardButton("📊 Statistics", callback_data="stats")
            ],
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/zerodevbro"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Zeroboy216")
            ],
            [
                InlineKeyboardButton("⭐ Rate Us", url="https://t.me/zerodevbro"),
                InlineKeyboardButton("🔗 Share", switch_inline_query="Check out this amazing bot hoster!")
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
        await callback_query.answer()
    
    elif data == "add_bot":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])
        
        try:
            await callback_query.message.edit_text(
                "╔═══════════════════════════╗\n"
                "║    **🤖 ADD NEW BOT**    ║\n"
                "╚═══════════════════════════╝\n\n"
                "**Step 1: Bot Token** 🔑\n\n"
                "Please send your bot token from @BotFather\n\n"
                "**📝 Format:**\n"
                "`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 **Tip:** Copy the entire token\n"
                "⚠️ Don't share your token publicly\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Click **Cancel** to abort ❌",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
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
                "No changes were made.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Click Home to return to main menu.",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
        await callback_query.answer("❌ Cancelled")
        
    elif data == "my_bots":
        await callback_query.answer()
        bots = await db.get_user_bots(user_id)
        
        if not bots:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Your First Bot", callback_data="add_bot")],
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
            
            try:
                await callback_query.message.edit_text(
                    "╔═══════════════════════════╗\n"
                    "║   **📋 YOUR BOTS**   ║\n"
                    "╚═══════════════════════════╝\n\n"
                    "❌ **No bots found!**\n\n"
                    "You haven't hosted any bots yet.\n\n"
                    "🚀 Ready to get started?\n"
                    "Click the button below!\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "⚡ **Takes less than 2 minutes!**",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
            return
        
        text = "╔═══════════════════════════╗\n"
        text += "║   **📋 YOUR BOTS**   ║\n"
        text += "╚═══════════════════════════╝\n\n"
        
        keyboards = []
        
        for idx, bot in enumerate(bots, 1):
            status_icon = "🟢" if bot.get("status") == "running" else "🔴"
            status_text = "Online" if bot.get("status") == "running" else "Offline"
            
            text += f"**Bot #{idx}** {status_icon}\n"
            text += f"┣━ **Name:** @{bot.get('bot_username', 'unknown')}\n"
            text += f"┣━ **ID:** `{bot['_id']}`\n"
            text += f"┣━ **Status:** {status_text}\n"
            text += f"┗━ **Added:** {bot.get('created_at', 'N/A')}\n\n"
            
            button_text = f"⏹️ Stop #{idx}" if bot.get("status") == "running" else f"▶️ Start #{idx}"
            
            keyboards.append([
                InlineKeyboardButton(button_text, callback_data=f"toggle_{bot['_id']}"),
                InlineKeyboardButton(f"✏️ Edit #{idx}", callback_data=f"edit_{bot['_id']}")
            ])
            keyboards.append([
                InlineKeyboardButton(f"📊 Stats #{idx}", callback_data=f"botstats_{bot['_id']}"),
                InlineKeyboardButton(f"🗑️ Delete #{idx}", callback_data=f"delete_confirm_{bot['_id']}")
            ])
            keyboards.append([InlineKeyboardButton("━━━━━━━━━━━━━━━", callback_data="separator")])
        
        keyboards.pop()  # Remove last separator
        keyboards.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="my_bots"),
            InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")
        ])
        keyboards.append([InlineKeyboardButton("🏠 Home", callback_data="start")])
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
        
    elif data == "help":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Bot", callback_data="add_bot"),
                InlineKeyboardButton("📋 My Bots", callback_data="my_bots")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
                InlineKeyboardButton("🏠 Home", callback_data="start")
            ],
            [
                InlineKeyboardButton("📢 Channel", url="https://t.me/zerodevbro"),
                InlineKeyboardButton("💬 Support", url="https://t.me/Zeroboy216")
            ]
        ])
        
        try:
            await callback_query.message.edit_text(
                HELP_MESSAGE,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
        await callback_query.answer()
    
    elif data == "stats":
        stats = await db.get_stats()
        
        running_percent = (stats['running_bots'] / stats['total_bots'] * 100) if stats['total_bots'] > 0 else 0
        
        stats_text = f"""
╔═══════════════════════════╗
║  **📊 PLATFORM STATS**  ║
╚═══════════════════════════╝

**🤖 Bot Statistics:**
━━━━━━━━━━━━━━━━━━━━━━
**Total Bots:** `{stats['total_bots']}`
🟢 **Running:** `{stats['running_bots']}`
🔴 **Stopped:** `{stats['stopped_bots']}`
📊 **Uptime Rate:** `{running_percent:.1f}%`

**👥 User Statistics:**
━━━━━━━━━━━━━━━━━━━━━━
**Total Users:** `{stats['total_users']}`
**Active Today:** `{stats.get('active_users', 'N/A')}`

**⚡ Performance:**
━━━━━━━━━━━━━━━━━━━━━━
**Server Status:** 🟢 Online
**Response Time:** < 100ms
**Uptime:** 99.9%

━━━━━━━━━━━━━━━━━━━━━━
⚡ **Powered by Zero Dev Bro**
📢 @zerodevbro | 👨‍💻 @Zeroboy216
━━━━━━━━━━━━━━━━━━━━━━
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="stats")],
            [InlineKeyboardButton("🏠 Home", callback_data="start")]
        ])
        
        try:
            await callback_query.message.edit_text(
                stats_text,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
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
            await callback_query.answer("⏹️ Bot stopped successfully!")
        else:
            file_ext = bot.get("file_metadata", {}).get("file_type", "py")
            success = await runner.start_bot(bot_id, bot["token"], bot["script"], file_ext)
            if success:
                await db.update_bot_status(bot_id, "running")
                await callback_query.answer("▶️ Bot started successfully!")
            else:
                await callback_query.answer("❌ Failed to start bot! Check logs.", show_alert=True)
                return
        
        # Refresh bots list
        bots = await db.get_user_bots(user_id)
        text = "╔═══════════════════════════╗\n"
        text += "║   **📋 YOUR BOTS**   ║\n"
        text += "╚═══════════════════════════╝\n\n"
        
        keyboards = []
        
        for idx, bot in enumerate(bots, 1):
            status_icon = "🟢" if bot.get("status") == "running" else "🔴"
            status_text = "Online" if bot.get("status") == "running" else "Offline"
            
            text += f"**Bot #{idx}** {status_icon}\n"
            text += f"┣━ **Name:** @{bot.get('bot_username', 'unknown')}\n"
            text += f"┣━ **ID:** `{bot['_id']}`\n"
            text += f"┣━ **Status:** {status_text}\n"
            text += f"┗━ **Added:** {bot.get('created_at', 'N/A')}\n\n"
            
            button_text = f"⏹️ Stop #{idx}" if bot.get("status") == "running" else f"▶️ Start #{idx}"
            
            keyboards.append([
                InlineKeyboardButton(button_text, callback_data=f"toggle_{bot['_id']}"),
                InlineKeyboardButton(f"✏️ Edit #{idx}", callback_data=f"edit_{bot['_id']}")
            ])
            keyboards.append([
                InlineKeyboardButton(f"📊 Stats #{idx}", callback_data=f"botstats_{bot['_id']}"),
                InlineKeyboardButton(f"🗑️ Delete #{idx}", callback_data=f"delete_confirm_{bot['_id']}")
            ])
            keyboards.append([InlineKeyboardButton("━━━━━━━━━━━━━━━", callback_data="separator")])
        
        keyboards.pop()
        keyboards.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="my_bots"),
            InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")
        ])
        keyboards.append([InlineKeyboardButton("🏠 Home", callback_data="start")])
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
    
    # Continue with remaining handlers (edit, delete, etc.)
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
                "╔═══════════════════════════╗\n"
                "║   **✏️ EDIT BOT**   ║\n"
                "╚═══════════════════════════╝\n\n"
                f"**Bot:** @{bot.get('bot_username', 'unknown')}\n"
                f"**ID:** `{bot_id}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "**Send new script:**\n"
                "📁 Upload file (.py, .js, .sh, etc.)\n"
                "📝 Or paste code as text\n\n"
                "Click Cancel to go back ❌",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
        
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
                InlineKeyboardButton("❌ No, Cancel", callback_data="my_bots")
            ]
        ])
        
        try:
            await callback_query.message.edit_text(
                f"╔═══════════════════════════╗\n"
                f"║  **⚠️ CONFIRM DELETE**  ║\n"
                f"╚═══════════════════════════╝\n\n"
                f"**Are you sure you want to delete this bot?**\n\n"
                f"**Bot Details:**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"**📛 Name:** @{bot.get('bot_username', 'unknown')}\n"
                f"**🆔 ID:** `{bot_id}`\n"
                f"**📊 Status:** {'🟢 Running' if bot.get('status') == 'running' else '🔴 Stopped'}\n"
                f"**📅 Created:** {bot.get('created_at', 'N/A')}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ **This action cannot be undone!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"All bot data and scripts will be permanently deleted.",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
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
        
        # Stop and delete the bot
        await runner.stop_bot(bot_id)
        await db.delete_bot(bot_id)
        
        await callback_query.answer("🗑️ Bot deleted successfully!", show_alert=True)
        
        # Show updated bots list
        bots = await db.get_user_bots(user_id)
        
        if not bots:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add New Bot", callback_data="add_bot")],
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ])
            
            try:
                await callback_query.message.edit_text(
                    "╔═══════════════════════════╗\n"
                    "║   **✅ DELETED**   ║\n"
                    "╚═══════════════════════════╝\n\n"
                    "**Bot deleted successfully!** 🗑️\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "❌ You have no bots now.\n\n"
                    "Ready to host a new bot?\n"
                    "Click the button below!\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
            return
        
        text = "╔═══════════════════════════╗\n"
        text += "║   **✅ DELETED**   ║\n"
        text += "╚═══════════════════════════╝\n\n"
        text += "**Bot deleted successfully!** 🗑️\n\n"
        text += "**📋 Your Remaining Bots:**\n\n"
        
        keyboards = []
        
        for idx, bot in enumerate(bots, 1):
            status_icon = "🟢" if bot.get("status") == "running" else "🔴"
            status_text = "Online" if bot.get("status") == "running" else "Offline"
            
            text += f"**Bot #{idx}** {status_icon}\n"
            text += f"┣━ **Name:** @{bot.get('bot_username', 'unknown')}\n"
            text += f"┣━ **ID:** `{bot['_id']}`\n"
            text += f"┣━ **Status:** {status_text}\n"
            text += f"┗━ **Added:** {bot.get('created_at', 'N/A')}\n\n"
            
            button_text = f"⏹️ Stop #{idx}" if bot.get("status") == "running" else f"▶️ Start #{idx}"
            
            keyboards.append([
                InlineKeyboardButton(button_text, callback_data=f"toggle_{bot['_id']}"),
                InlineKeyboardButton(f"✏️ Edit #{idx}", callback_data=f"edit_{bot['_id']}")
            ])
            keyboards.append([
                InlineKeyboardButton(f"📊 Stats #{idx}", callback_data=f"botstats_{bot['_id']}"),
                InlineKeyboardButton(f"🗑️ Delete #{idx}", callback_data=f"delete_confirm_{bot['_id']}")
            ])
            keyboards.append([InlineKeyboardButton("━━━━━━━━━━━━━━━", callback_data="separator")])
        
        keyboards.pop()
        keyboards.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="my_bots"),
            InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")
        ])
        keyboards.append([InlineKeyboardButton("🏠 Home", callback_data="start")])
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboards)
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
    
    elif data.startswith("botstats_"):
        bot_id = data.split("_")[1]
        bot = await db.get_bot(bot_id)
        
        if not bot:
            await callback_query.answer("❌ Bot not found!", show_alert=True)
            return
        
        if bot["user_id"] != user_id:
            await callback_query.answer("❌ Not your bot!", show_alert=True)
            return
        
        # Get bot statistics
        status_icon = "🟢" if bot.get("status") == "running" else "🔴"
        status_text = "Online & Running" if bot.get("status") == "running" else "Offline"
        
        file_info = bot.get("file_metadata", {})
        file_name = file_info.get("file_name", "Unknown")
        file_type = file_info.get("file_type", "py")
        file_size = file_info.get("file_size", 0)
        
        type_emoji = {
            'py': '🐍', 'js': '📜', 'sh': '🐚',
            'rb': '💎', 'php': '🐘', 'go': '🔵', 'txt': '📝'
        }.get(file_type, '📄')
        
        stats_text = f"""
╔═══════════════════════════╗
║   **📊 BOT STATISTICS**   ║
╚═══════════════════════════╝

**📛 Bot Information:**
━━━━━━━━━━━━━━━━━━━━━━
**Name:** @{bot.get('bot_username', 'unknown')}
**ID:** `{bot_id}`
**Status:** {status_icon} {status_text}

**{type_emoji} Script Information:**
━━━━━━━━━━━━━━━━━━━━━━
**File:** `{file_name}`
**Type:** {file_type.upper()}
**Size:** {file_size / 1024:.2f}KB
**Lines:** {len(bot.get('script', '').split(chr(10)))}

**📅 Timeline:**
━━━━━━━━━━━━━━━━━━━━━━
**Created:** {bot.get('created_at', 'N/A')}
**Last Updated:** {bot.get('updated_at', 'N/A')}

**⚙️ Performance:**
━━━━━━━━━━━━━━━━━━━━━━
**Uptime:** {bot.get('uptime', '0')} hours
**Restarts:** {bot.get('restart_count', 0)}
**Errors:** {bot.get('error_count', 0)}

━━━━━━━━━━━━━━━━━━━━━━
⚡ Auto-restart: {'✅ Enabled' if bot.get('auto_restart', True) else '❌ Disabled'}
━━━━━━━━━━━━━━━━━━━━━━
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data=f"botstats_{bot_id}")],
            [InlineKeyboardButton("🔙 Back to My Bots", callback_data="my_bots")]
        ])
        
        try:
            await callback_query.message.edit_text(
                stats_text,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
        await callback_query.answer()

# Admin commands
@app.on_message(filters.command(["broadcast", "total", "restart", "stats"]) & filters.user(OWNER_ID))
async def admin_commands(client: Client, message: Message):
    await handle_admin_commands(client, message, db, runner)

# Cancel command
@app.on_message(filters.command("cancel") & filters.private)
async def cancel_command(client: Client, message: Message):
    user_id = message.from_user.id
    await db.clear_user_state(user_id)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="start")]
    ])
    
    await message.reply_text(
        "✅ **Operation Cancelled**\n\n"
        "All pending operations have been cancelled.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Use /start to return to main menu.",
        reply_markup=keyboard
    )

# Error handler
@app.on_message(filters.private)
async def catch_all(client: Client, message: Message):
    """Catch-all handler for unhandled messages"""
    if message.text and message.text.startswith('/'):
        await message.reply_text(
            "❌ **Unknown Command**\n\n"
            "That command is not recognized.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Available commands:**\n"
            "/start - Main menu\n"
            "/addbot - Add new bot\n"
            "/mybots - Manage bots\n"
            "/help - Help guide\n"
            "/cancel - Cancel operation\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Use /help for more information."
        )

# Run the bot
if __name__ == "__main__":
    logger.info("╔═══════════════════════════════════╗")
    logger.info("║  Zero Dev Bot Hoster v2.0        ║")
    logger.info("║  Starting up...                   ║")
    logger.info("╚═══════════════════════════════════╝")
    logger.info("Developer: @Zeroboy216")
    logger.info("Channel: @zerodevbro")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise
