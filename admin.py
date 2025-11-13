"""
Admin Commands for Bot Hoster
Developer: @Zeroboy216
Channel: @zerodevbro
"""

import asyncio
import psutil
import logging
from pyrogram import Client
from pyrogram.types import Message

logger = logging.getLogger(__name__)

async def handle_admin_commands(client: Client, message: Message, db, runner):
    """Handle admin-only commands"""
    command = message.command[0]
    
    if command == "broadcast":
        await handle_broadcast(client, message, db)
    elif command == "total":
        await handle_total(client, message, db)
    elif command == "restart":
        await handle_restart(client, message, db, runner)
    elif command == "stats":
        await handle_stats(client, message, db, runner)

async def handle_broadcast(client: Client, message: Message, db):
    """Broadcast message to all users"""
    if len(message.command) < 2:
        await message.reply_text(
            "**📢 Broadcast Command**\n\n"
            "Usage: `/broadcast <message>`\n\n"
            "Example: `/broadcast Hello all users!`"
        )
        return
    
    # Get broadcast message
    broadcast_msg = message.text.split(None, 1)[1]
    
    # Get all users
    users = await db.get_all_users()
    
    status_msg = await message.reply_text(
        f"📢 Broadcasting to {len(users)} users...\n"
        f"⏳ Please wait..."
    )
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await client.send_message(
                chat_id=user["user_id"],
                text=f"📢 **Broadcast Message**\n\n{broadcast_msg}\n\n"
                     f"━━━━━━━━━━━━━━━━\n"
                     f"⚡ **From:** Bot Hoster Admin\n"
                     f"📢 **Updates:** @zerodevbro"
            )
            success += 1
            await asyncio.sleep(0.1)  # Avoid flood limits
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to {user['user_id']}: {e}")
    
    await status_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(users)}"
    )

async def handle_total(client: Client, message: Message, db):
    """Show total statistics"""
    stats = await db.get_stats()
    all_bots = await db.get_all_bots()
    
    # Count bots per user
    user_bot_counts = {}
    for bot in all_bots:
        user_id = bot["user_id"]
        user_bot_counts[user_id] = user_bot_counts.get(user_id, 0) + 1
    
    # Top users
    top_users = sorted(user_bot_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    text = f"""
📊 **Bot Hoster Statistics**

**👥 Users:**
━━━━━━━━━━━━━━━━
Total Users: `{stats['total_users']}`

**🤖 Bots:**
━━━━━━━━━━━━━━━━
Total Bots: `{stats['total_bots']}`
🟢 Running: `{stats['running_bots']}`
🔴 Stopped: `{stats['stopped_bots']}`

**👑 Top Users:**
━━━━━━━━━━━━━━━━
"""
    
    for idx, (user_id, count) in enumerate(top_users, 1):
        text += f"{idx}. User `{user_id}`: {count} bots\n"
    
    text += f"""
━━━━━━━━━━━━━━━━
⚡ **Powered by Zero Dev Bro**
📢 **Updates:** @zerodevbro
"""
    
    await message.reply_text(text, parse_mode="markdown")

async def handle_restart(client: Client, message: Message, db, runner):
    """Restart a specific bot"""
    if len(message.command) < 2:
        await message.reply_text(
            "**🔄 Restart Command**\n\n"
            "Usage: `/restart <bot_id>`\n\n"
            "Example: `/restart 507f1f77bcf86cd799439011`"
        )
        return
    
    bot_id = message.command[1]
    
    # Check if bot exists
    bot = await db.get_bot(bot_id)
    if not bot:
        await message.reply_text("❌ Bot not found!")
        return
    
    status_msg = await message.reply_text(f"🔄 Restarting bot `{bot_id}`...")
    
    success = await runner.restart_bot(bot_id)
    
    if success:
        await db.update_bot_status(bot_id, "running")
        await status_msg.edit_text(
            f"✅ **Bot Restarted Successfully!**\n\n"
            f"**Bot ID:** `{bot_id}`\n"
            f"**Username:** @{bot.get('bot_username', 'unknown')}\n"
            f"**Status:** 🟢 Running"
        )
    else:
        await status_msg.edit_text(
            f"❌ **Failed to restart bot!**\n\n"
            f"**Bot ID:** `{bot_id}`\n"
            f"Check logs for more details."
        )

async def handle_stats(client: Client, message: Message, db, runner):
    """Show system statistics"""
    stats = await db.get_stats()
    
    # System stats
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Bot stats
    running_bots = await db.get_running_bots()
    
    text = f"""
📊 **System Statistics**

**💻 System Resources:**
━━━━━━━━━━━━━━━━
🖥️ CPU Usage: `{cpu_percent}%`
💾 RAM Usage: `{memory.percent}%`
💿 Disk Usage: `{disk.percent}%`

**🤖 Bot Statistics:**
━━━━━━━━━━━━━━━━
Total Bots: `{stats['total_bots']}`
🟢 Running: `{stats['running_bots']}`
🔴 Stopped: `{stats['stopped_bots']}`

**👥 User Statistics:**
━━━━━━━━━━━━━━━━
Total Users: `{stats['total_users']}`

**🏃 Currently Running Bots:**
━━━━━━━━━━━━━━━━
"""
    
    for idx, bot in enumerate(running_bots[:10], 1):
        text += f"{idx}. @{bot.get('bot_username', 'unknown')} (ID: `{bot['_id']}`)\n"
    
    if len(running_bots) > 10:
        text += f"\n... and {len(running_bots) - 10} more\n"
    
    text += f"""
━━━━━━━━━━━━━━━━
⚡ **Powered by Zero Dev Bro**
📢 **Updates:** @zerodevbro
"""
    
    await message.reply_text(text, parse_mode="markdown")
