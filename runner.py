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
from pyrogram import Client, filters
from pyrogram.types import Message
from config import BLOCKED_IMPORTS, BOT_FOOTER, AUTO_RESTART, API_ID, API_HASH

logger = logging.getLogger(__name__)

class BotRunner:
    def __init__(self, db):
        self.db = db
        self.running_bots = {}  # bot_id -> process
        self.bot_clients = {}   # bot_id -> Client
        self.bot_tasks = {}     # bot_id -> asyncio.Task
        
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
        
        # Check if script has message handlers
        if "@bot.on_message" not in script and "filters.command" not in script:
            return False, "Script must contain at least one message handler (@bot.on_message)"
        
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
            
            # Start the bot client
            await bot_client.start()
            logger.info(f"✅ Bot client {bot_id} connected")
            
            # Import required modules for the script
            from pyrogram import filters
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # Create a safe namespace for script execution
            namespace = {
                'bot': bot_client,
                'app': bot_client,  # Support both @bot and @app decorators
                'Client': Client,
                'filters': filters,
                'InlineKeyboardMarkup': InlineKeyboardMarkup,
                'InlineKeyboardButton': InlineKeyboardButton,
                'Message': Message,
                'asyncio': asyncio,
                'logger': logger,
                'BOT_FOOTER': BOT_FOOTER,
                '__builtins__': __builtins__,
            }
            
            # Execute the user script
            try:
                exec(script, namespace)
                logger.info(f"✅ Script executed for bot {bot_id}")
            except Exception as e:
                logger.error(f"❌ Script execution error for bot {bot_id}: {e}")
                await bot_client.stop()
                return False
            
            # Store the client
            self.bot_clients[bot_id] = bot_client
            
            # Create a task to keep bot running
            task = asyncio.create_task(self._keep_bot_alive(bot_id, bot_client, token, script))
            self.bot_tasks[bot_id] = task
            
            logger.info(f"✅ Bot {bot_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot {bot_id}: {e}")
            try:
                await self.db.increment_error_count(bot_id)
            except:
                pass
            return False
    
    async def _keep_bot_alive(self, bot_id: str, bot_client: Client, token: str, script: str):
        """Keep bot alive and handle auto-restart"""
        try:
            # Keep the bot running indefinitely
            while bot_id in self.bot_clients:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info(f"Bot {bot_id} task cancelled")
            
        except Exception as e:
            logger.error(f"Error in bot {bot_id}: {e}")
            
            # Auto-restart if enabled
            if AUTO_RESTART and bot_id in self.bot_clients:
                logger.info(f"🔄 Auto-restarting bot {bot_id}")
                await asyncio.sleep(5)
                await self.start_bot(bot_id, token, script)
    
    async def stop_bot(self, bot_id: str):
        """Stop a hosted bot"""
        try:
            # Cancel the task
            if bot_id in self.bot_tasks:
                task = self.bot_tasks[bot_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.bot_tasks[bot_id]
            
            # Stop the client
            if bot_id in self.bot_clients:
                client = self.bot_clients[bot_id]
                try:
                    await client.stop()
                except:
                    pass
                del self.bot_clients[bot_id]
                
            logger.info(f"⏹️ Bot {bot_id} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {e}")
            return False
    
    async def restart_bot(self, bot_id: str):
        """Restart a hosted bot"""
        try:
            bot = await self.db.get_bot(bot_id)
            if not bot:
                logger.error(f"Bot {bot_id} not found in database")
                return False
            
            logger.info(f"🔄 Restarting bot {bot_id}")
            await self.stop_bot(bot_id)
            await asyncio.sleep(2)
            
            success = await self.start_bot(bot_id, bot["token"], bot["script"])
            
            if success:
                logger.info(f"✅ Bot {bot_id} restarted successfully")
            else:
                logger.error(f"❌ Failed to restart bot {bot_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error restarting bot {bot_id}: {e}")
            return False
    
    async def stop_all_bots(self):
        """Stop all running bots"""
        logger.info("Stopping all bots...")
        bot_ids = list(self.bot_clients.keys())
        
        for bot_id in bot_ids:
            try:
                await self.stop_bot(bot_id)
            except Exception as e:
                logger.error(f"Error stopping bot {bot_id}: {e}")
        
        logger.info("✅ All bots stopped")
    
    async def get_bot_stats(self, bot_id: str):
        """Get statistics for a specific bot"""
        if bot_id not in self.bot_clients:
            return {
                "status": "stopped",
                "uptime": 0
            }
        
        return {
            "status": "running",
            "uptime": "N/A",  # Can be extended with actual uptime tracking
            "client_status": "connected"
        }
    
    async def restart_all_bots(self):
        """Restart all bots from database"""
        try:
            # Get all bots with running status
            all_bots = await self.db.get_all_bots()
            
            started_count = 0
            failed_count = 0
            
            for bot in all_bots:
                if bot.get("status") == "running":
                    bot_id = str(bot["_id"])
                    try:
                        success = await self.start_bot(bot_id, bot["token"], bot["script"])
                        if success:
                            started_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to restart bot {bot_id}: {e}")
                        failed_count += 1
            
            logger.info(f"✅ Restarted {started_count} bots, {failed_count} failed")
            return started_count, failed_count
            
        except Exception as e:
            logger.error(f"Error restarting all bots: {e}")
            return 0, 0
    
    def is_bot_running(self, bot_id: str):
        """Check if a bot is currently running"""
        return bot_id in self.bot_clients
    
    def get_running_bots_count(self):
        """Get count of currently running bots"""
        return len(self.bot_clients)
    
    def get_running_bot_ids(self):
        """Get list of running bot IDs"""
        return list(self.bot_clients.keys())
