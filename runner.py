"""
Bot Runner - Manages hosted bot processes
Developer: @Zeroboy216
Channel: @zerodevbro
"""

import asyncio
import os
import sys
import tempfile
import logging
from pyrogram import Client
from config import BLOCKED_IMPORTS, BOT_FOOTER, AUTO_RESTART, API_ID, API_HASH

logger = logging.getLogger(__name__)

class BotRunner:
    def __init__(self, db):
        self.db = db
        self.running_bots = {}  # bot_id -> process
        self.bot_clients = {}   # bot_id -> Client
        
    async def verify_token(self, token: str):
        """Verify if bot token is valid"""
        try:
            # Create temporary client
            temp_client = Client(
                f"temp_{token.split(':')[0]}",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                in_memory=True
            )
            
            await temp_client.start()
            me = await temp_client.get_me()
            await temp_client.stop()
            
            return True, {
                "username": me.username,
                "first_name": me.first_name,
                "id": me.id
            }
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return False, None
    
    async def validate_script(self, script: str):
        """Validate script for security issues"""
        # Check for blocked imports
        for blocked in BLOCKED_IMPORTS:
            if blocked in script:
                return False, f"Blocked import/function detected: {blocked}"
        
        # Check if script has basic structure
        if "def " not in script:
            return False, "Script must contain at least one function definition"
        
        # Try to compile the script
        try:
            compile(script, "<string>", "exec")
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        return True, None
    
    async def start_bot(self, bot_id: str, token: str, script: str):
        """Start a hosted bot"""
        try:
            # Stop if already running
            if bot_id in self.bot_clients:
                await self.stop_bot(bot_id)
            
            # Create bot client
            session_name = f"bot_{bot_id}"
            bot_client = Client(
                session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=token,
                in_memory=True
            )
            
            # Create a wrapper script with error handling
            wrapped_script = self._wrap_script(script, bot_id)
            
            # Start the bot
            await bot_client.start()
            
            # Execute the user script in a safe namespace
            namespace = {
                'bot': bot_client,
                'Client': Client,
                'asyncio': asyncio,
                'logger': logger,
                'BOT_FOOTER': BOT_FOOTER
            }
            
            exec(wrapped_script, namespace)
            
            # Store the client
            self.bot_clients[bot_id] = bot_client
            
            # Start message handler
            asyncio.create_task(self._handle_bot_messages(bot_id, bot_client, namespace))
            
            logger.info(f"✅ Bot {bot_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot {bot_id}: {e}")
            await self.db.increment_error_count(bot_id)
            return False
    
    def _wrap_script(self, script: str, bot_id: str):
        """Wrap user script with error handling and footer"""
        wrapper = f"""
import asyncio
from pyrogram import filters

# User script
{script}

# Add footer to all messages
def add_footer(text):
    return text + "\\n" + BOT_FOOTER

# Wrap message handler
original_on_message = on_message if 'on_message' in dir() else None

if original_on_message:
    async def wrapped_on_message(client, message):
        try:
            await original_on_message(client, message)
        except Exception as e:
            logger.error(f"Error in bot {bot_id}: {{e}}")
            await message.reply_text("❌ An error occurred processing your message.")
    
    # Register handler
    from pyrogram import filters
    @bot.on_message(filters.private)
    async def message_handler(client, message):
        await wrapped_on_message(client, message)
"""
        return wrapper
    
    async def _handle_bot_messages(self, bot_id: str, bot_client: Client, namespace: dict):
        """Handle messages for a hosted bot"""
        try:
            # Keep the bot running
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            logger.info(f"Bot {bot_id} message handler cancelled")
        except Exception as e:
            logger.error(f"Error in bot {bot_id} message handler: {e}")
            
            if AUTO_RESTART:
                logger.info(f"Auto-restarting bot {bot_id}")
                bot = await self.db.get_bot(bot_id)
                if bot:
                    await asyncio.sleep(5)  # Wait before restart
                    await self.start_bot(bot_id, bot["token"], bot["script"])
    
    async def stop_bot(self, bot_id: str):
        """Stop a hosted bot"""
        try:
            if bot_id in self.bot_clients:
                client = self.bot_clients[bot_id]
                await client.stop()
                del self.bot_clients[bot_id]
                logger.info(f"⏹️ Bot {bot_id} stopped")
                return True
        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {e}")
        return False
    
    async def restart_bot(self, bot_id: str):
        """Restart a hosted bot"""
        bot = await self.db.get_bot(bot_id)
        if not bot:
            return False
        
        await self.stop_bot(bot_id)
        await asyncio.sleep(2)
        return await self.start_bot(bot_id, bot["token"], bot["script"])
    
    async def stop_all_bots(self):
        """Stop all running bots"""
        bot_ids = list(self.bot_clients.keys())
        for bot_id in bot_ids:
            await self.stop_bot(bot_id)
        logger.info("All bots stopped")
    
    async def get_bot_stats(self, bot_id: str):
        """Get statistics for a specific bot"""
        if bot_id not in self.bot_clients:
            return {"status": "stopped"}
        
        return {
            "status": "running",
            "uptime": "N/A"  # Can be extended with more metrics
        }
