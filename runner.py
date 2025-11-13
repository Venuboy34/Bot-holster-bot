"""
Bot Runner - Manages hosted bot processes (Enhanced Multi-Language Support)
Developer: @Zeroboy216
Channel: @zerodevbro
Version: 2.0 - Now supports Python, JavaScript, Shell, Ruby, PHP, Go
"""

import asyncio
import os
import sys
import tempfile
import logging
import subprocess
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from config import BLOCKED_IMPORTS, BOT_FOOTER, AUTO_RESTART, API_ID, API_HASH

logger = logging.getLogger(__name__)

class BotRunner:
    def __init__(self, db):
        self.db = db
        self.running_bots = {}  # bot_id -> process info
        self.bot_clients = {}   # bot_id -> Client (for Python bots)
        self.bot_tasks = {}     # bot_id -> asyncio.Task
        self.bot_processes = {} # bot_id -> subprocess.Process (for non-Python bots)
        self.bot_start_times = {} # bot_id -> start timestamp
        
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
            
            logger.info(f"✅ Token verified for bot: @{me.username}")
            
            return True, {
                "username": me.username,
                "first_name": me.first_name,
                "id": me.id
            }
        except Exception as e:
            logger.error(f"❌ Token verification failed: {e}")
            return False, None
    
    async def validate_script(self, script: str, file_type: str = "py"):
        """Validate script for security issues based on file type"""
        try:
            # Common security checks for all file types
            dangerous_patterns = [
                'rm -rf /', 'format c:', 'del /f /s /q',  # Destructive commands
                '__import__("os").system', 'eval(', 'exec(',  # Dangerous functions
                'subprocess.call', 'os.system',  # System access
            ]
            
            # Check for dangerous patterns
            script_lower = script.lower()
            for pattern in dangerous_patterns:
                if pattern.lower() in script_lower:
                    return False, f"Security violation: Dangerous pattern detected: {pattern}"
            
            # File type specific validation
            if file_type == "py":
                return await self._validate_python(script)
            elif file_type == "js":
                return await self._validate_javascript(script)
            elif file_type == "sh":
                return await self._validate_shell(script)
            elif file_type == "rb":
                return await self._validate_ruby(script)
            elif file_type == "php":
                return await self._validate_php(script)
            elif file_type == "go":
                return await self._validate_go(script)
            else:
                return True, None  # Allow other file types with basic checks
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def _validate_python(self, script: str):
        """Validate Python script"""
        # Check for blocked imports
        for blocked in BLOCKED_IMPORTS:
            if blocked in script:
                return False, f"Blocked import/function: {blocked}"
        
        # Check if script has message handlers (recommended but not required)
        has_handlers = any(pattern in script for pattern in [
            "@bot.on_message", "@app.on_message",
            "filters.command", "on_message"
        ])
        
        if not has_handlers:
            logger.warning("Script has no obvious message handlers")
        
        # Try to compile the script
        try:
            compile(script, "<string>", "exec")
            return True, None
        except SyntaxError as e:
            return False, f"Python syntax error: {str(e)}"
    
    async def _validate_javascript(self, script: str):
        """Validate JavaScript/Node.js script"""
        # Check for required bot library
        required_patterns = ['require(', 'import ', 'bot.on', '.sendMessage']
        
        has_bot_code = any(pattern in script for pattern in required_patterns)
        if not has_bot_code:
            return False, "JavaScript script must include bot library (telegraf, node-telegram-bot-api, etc.)"
        
        # Basic syntax check (if node is available)
        try:
            result = subprocess.run(
                ['node', '--check', '-'],
                input=script.encode(),
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                error_msg = result.stderr.decode()
                return False, f"JavaScript syntax error: {error_msg[:200]}"
        except FileNotFoundError:
            logger.warning("Node.js not found, skipping syntax check")
        except Exception as e:
            logger.warning(f"JS validation warning: {e}")
        
        return True, None
    
    async def _validate_shell(self, script: str):
        """Validate Shell script"""
        # Check for shebang
        if not script.strip().startswith('#!'):
            logger.info("Adding default shebang to shell script")
        
        # Check for extremely dangerous commands
        extremely_dangerous = [
            'rm -rf /',
            'mkfs.',
            'dd if=/dev/zero',
            '> /dev/sda',
            'chmod 777 /',
        ]
        
        for cmd in extremely_dangerous:
            if cmd in script:
                return False, f"Extremely dangerous command blocked: {cmd}"
        
        return True, None
    
    async def _validate_ruby(self, script: str):
        """Validate Ruby script"""
        # Check for Telegram bot patterns
        bot_patterns = ['Telegram::Bot', 'telegram-bot-ruby', 'bot.listen']
        
        has_bot_code = any(pattern in script for pattern in bot_patterns)
        if not has_bot_code:
            logger.warning("Ruby script may not contain Telegram bot code")
        
        # Basic syntax check (if ruby is available)
        try:
            result = subprocess.run(
                ['ruby', '-c', '-'],
                input=script.encode(),
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                error_msg = result.stderr.decode()
                return False, f"Ruby syntax error: {error_msg[:200]}"
        except FileNotFoundError:
            logger.warning("Ruby not found, skipping syntax check")
        except Exception as e:
            logger.warning(f"Ruby validation warning: {e}")
        
        return True, None
    
    async def _validate_php(self, script: str):
        """Validate PHP script"""
        # Check for PHP opening tag
        if '<?php' not in script:
            return False, "PHP script must contain <?php opening tag"
        
        # Basic syntax check (if php is available)
        try:
            result = subprocess.run(
                ['php', '-l', '-'],
                input=script.encode(),
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                error_msg = result.stderr.decode()
                return False, f"PHP syntax error: {error_msg[:200]}"
        except FileNotFoundError:
            logger.warning("PHP not found, skipping syntax check")
        except Exception as e:
            logger.warning(f"PHP validation warning: {e}")
        
        return True, None
    
    async def _validate_go(self, script: str):
        """Validate Go script"""
        # Check for package declaration
        if 'package main' not in script:
            return False, "Go script must contain 'package main'"
        
        if 'func main()' not in script:
            return False, "Go script must contain 'func main()'"
        
        return True, None
    
    async def start_bot(self, bot_id: str, token: str, script: str, file_type: str = "py"):
        """Start a hosted bot (supports multiple languages)"""
        try:
            # Stop if already running
            if bot_id in self.bot_clients or bot_id in self.bot_processes:
                await self.stop_bot(bot_id)
            
            logger.info(f"🚀 Starting {file_type.upper()} bot {bot_id}")
            
            # Record start time
            self.bot_start_times[bot_id] = time.time()
            
            # Route to appropriate starter based on file type
            if file_type == "py":
                return await self._start_python_bot(bot_id, token, script)
            elif file_type == "js":
                return await self._start_javascript_bot(bot_id, token, script)
            elif file_type == "sh":
                return await self._start_shell_bot(bot_id, token, script)
            elif file_type == "rb":
                return await self._start_ruby_bot(bot_id, token, script)
            elif file_type == "php":
                return await self._start_php_bot(bot_id, token, script)
            elif file_type == "go":
                return await self._start_go_bot(bot_id, token, script)
            else:
                logger.error(f"Unsupported file type: {file_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start bot {bot_id}: {e}")
            try:
                await self.db.increment_error_count(bot_id)
            except:
                pass
            return False
    
    async def _start_python_bot(self, bot_id: str, token: str, script: str):
        """Start a Python bot using Pyrogram"""
        try:
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
            logger.info(f"✅ Python bot client {bot_id} connected")
            
            # Import required modules for the script
            from pyrogram import filters
            from pyrogram.types import (
                InlineKeyboardMarkup, InlineKeyboardButton,
                ReplyKeyboardMarkup, KeyboardButton
            )
            
            # Create a safe namespace for script execution
            namespace = {
                'bot': bot_client,
                'app': bot_client,  # Support both @bot and @app decorators
                'Client': Client,
                'filters': filters,
                'InlineKeyboardMarkup': InlineKeyboardMarkup,
                'InlineKeyboardButton': InlineKeyboardButton,
                'ReplyKeyboardMarkup': ReplyKeyboardMarkup,
                'KeyboardButton': KeyboardButton,
                'Message': Message,
                'asyncio': asyncio,
                'logger': logger,
                'BOT_FOOTER': BOT_FOOTER,
                '__builtins__': __builtins__,
            }
            
            # Execute the user script
            try:
                exec(script, namespace)
                logger.info(f"✅ Python script executed for bot {bot_id}")
            except Exception as e:
                logger.error(f"❌ Script execution error for bot {bot_id}: {e}")
                await bot_client.stop()
                return False
            
            # Store the client
            self.bot_clients[bot_id] = bot_client
            self.running_bots[bot_id] = {
                'type': 'python',
                'client': bot_client,
                'start_time': time.time()
            }
            
            # Create a task to keep bot running
            task = asyncio.create_task(
                self._keep_bot_alive(bot_id, bot_client, token, script, 'py')
            )
            self.bot_tasks[bot_id] = task
            
            logger.info(f"✅ Python bot {bot_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Python bot {bot_id}: {e}")
            return False
    
    async def _start_javascript_bot(self, bot_id: str, token: str, script: str):
        """Start a JavaScript/Node.js bot"""
        try:
            # Create temporary file for the script
            temp_dir = tempfile.mkdtemp()
            script_path = os.path.join(temp_dir, f"bot_{bot_id}.js")
            
            # Add token as environment variable in script
            full_script = f"""
// Bot Token (injected)
const BOT_TOKEN = '{token}';

{script}
"""
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(full_script)
            
            # Start Node.js process
            process = await asyncio.create_subprocess_exec(
                'node', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'BOT_TOKEN': token}
            )
            
            self.bot_processes[bot_id] = process
            self.running_bots[bot_id] = {
                'type': 'javascript',
                'process': process,
                'script_path': script_path,
                'temp_dir': temp_dir,
                'start_time': time.time()
            }
            
            # Monitor process
            task = asyncio.create_task(
                self._monitor_process(bot_id, process, token, script, 'js')
            )
            self.bot_tasks[bot_id] = task
            
            logger.info(f"✅ JavaScript bot {bot_id} started")
            return True
            
        except FileNotFoundError:
            logger.error("Node.js not installed on server")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start JS bot {bot_id}: {e}")
            return False
    
    async def _start_shell_bot(self, bot_id: str, token: str, script: str):
        """Start a Shell script bot"""
        try:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            script_path = os.path.join(temp_dir, f"bot_{bot_id}.sh")
            
            # Ensure shebang
            if not script.strip().startswith('#!'):
                script = '#!/bin/bash\n\n' + script
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            # Make executable
            os.chmod(script_path, 0o755)
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                'bash', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'BOT_TOKEN': token}
            )
            
            self.bot_processes[bot_id] = process
            self.running_bots[bot_id] = {
                'type': 'shell',
                'process': process,
                'script_path': script_path,
                'temp_dir': temp_dir,
                'start_time': time.time()
            }
            
            task = asyncio.create_task(
                self._monitor_process(bot_id, process, token, script, 'sh')
            )
            self.bot_tasks[bot_id] = task
            
            logger.info(f"✅ Shell bot {bot_id} started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Shell bot {bot_id}: {e}")
            return False
    
    async def _start_ruby_bot(self, bot_id: str, token: str, script: str):
        """Start a Ruby bot"""
        try:
            temp_dir = tempfile.mkdtemp()
            script_path = os.path.join(temp_dir, f"bot_{bot_id}.rb")
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            process = await asyncio.create_subprocess_exec(
                'ruby', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'BOT_TOKEN': token}
            )
            
            self.bot_processes[bot_id] = process
            self.running_bots[bot_id] = {
                'type': 'ruby',
                'process': process,
                'script_path': script_path,
                'temp_dir': temp_dir,
                'start_time': time.time()
            }
            
            task = asyncio.create_task(
                self._monitor_process(bot_id, process, token, script, 'rb')
            )
            self.bot_tasks[bot_id] = task
            
            logger.info(f"✅ Ruby bot {bot_id} started")
            return True
            
        except FileNotFoundError:
            logger.error("Ruby not installed on server")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start Ruby bot {bot_id}: {e}")
            return False
    
    async def _start_php_bot(self, bot_id: str, token: str, script: str):
        """Start a PHP bot"""
        try:
            temp_dir = tempfile.mkdtemp()
            script_path = os.path.join(temp_dir, f"bot_{bot_id}.php")
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            process = await asyncio.create_subprocess_exec(
                'php', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'BOT_TOKEN': token}
            )
            
            self.bot_processes[bot_id] = process
            self.running_bots[bot_id] = {
                'type': 'php',
                'process': process,
                'script_path': script_path,
                'temp_dir': temp_dir,
                'start_time': time.time()
            }
            
            task = asyncio.create_task(
                self._monitor_process(bot_id, process, token, script, 'php')
            )
            self.bot_tasks[bot_id] = task
            
            logger.info(f"✅ PHP bot {bot_id} started")
            return True
            
        except FileNotFoundError:
            logger.error("PHP not installed on server")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start PHP bot {bot_id}: {e}")
            return False
    
    async def _start_go_bot(self, bot_id: str, token: str, script: str):
        """Start a Go bot"""
        try:
            temp_dir = tempfile.mkdtemp()
            script_path = os.path.join(temp_dir, f"bot_{bot_id}.go")
            binary_path = os.path.join(temp_dir, f"bot_{bot_id}")
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            # Compile Go program
            compile_result = await asyncio.create_subprocess_exec(
                'go', 'build', '-o', binary_path, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await compile_result.wait()
            
            if compile_result.returncode != 0:
                stderr = await compile_result.stderr.read()
                logger.error(f"Go compilation failed: {stderr.decode()}")
                return False
            
            # Run compiled binary
            process = await asyncio.create_subprocess_exec(
                binary_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'BOT_TOKEN': token}
            )
            
            self.bot_processes[bot_id] = process
            self.running_bots[bot_id] = {
                'type': 'go',
                'process': process,
                'script_path': script_path,
                'binary_path': binary_path,
                'temp_dir': temp_dir,
                'start_time': time.time()
            }
            
            task = asyncio.create_task(
                self._monitor_process(bot_id, process, token, script, 'go')
            )
            self.bot_tasks[bot_id] = task
            
            logger.info(f"✅ Go bot {bot_id} started")
            return True
            
        except FileNotFoundError:
            logger.error("Go not installed on server")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start Go bot {bot_id}: {e}")
            return False
    
    async def _keep_bot_alive(self, bot_id: str, bot_client: Client, token: str, script: str, file_type: str):
        """Keep Python bot alive and handle auto-restart"""
        try:
            # Keep the bot running indefinitely
            while bot_id in self.bot_clients:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info(f"⏹️ Bot {bot_id} task cancelled")
            
        except Exception as e:
            logger.error(f"❌ Error in bot {bot_id}: {e}")
            
            # Auto-restart if enabled
            if AUTO_RESTART and bot_id in self.bot_clients:
                logger.info(f"🔄 Auto-restarting bot {bot_id}")
                try:
                    await self.db.increment_restart_count(bot_id)
                except:
                    pass
                await asyncio.sleep(5)
                await self.start_bot(bot_id, token, script, file_type)
    
    async def _monitor_process(self, bot_id: str, process, token: str, script: str, file_type: str):
        """Monitor subprocess-based bots"""
        try:
            # Wait for process to complete
            returncode = await process.wait()
            
            logger.warning(f"⚠️ Bot {bot_id} process exited with code {returncode}")
            
            # Auto-restart if enabled and bot still registered
            if AUTO_RESTART and bot_id in self.bot_processes:
                logger.info(f"🔄 Auto-restarting bot {bot_id}")
                try:
                    await self.db.increment_restart_count(bot_id)
                except:
                    pass
                await asyncio.sleep(5)
                await self.start_bot(bot_id, token, script, file_type)
                
        except asyncio.CancelledError:
            logger.info(f"⏹️ Bot {bot_id} monitor cancelled")
        except Exception as e:
            logger.error(f"❌ Monitor error for bot {bot_id}: {e}")
    
    async def stop_bot(self, bot_id: str):
        """Stop a hosted bot (any language)"""
        try:
            logger.info(f"⏹️ Stopping bot {bot_id}")
            
            # Cancel the task
            if bot_id in self.bot_tasks:
                task = self.bot_tasks[bot_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.bot_tasks[bot_id]
            
            # Stop Python client
            if bot_id in self.bot_clients:
                client = self.bot_clients[bot_id]
                try:
                    await client.stop()
                except:
                    pass
                del self.bot_clients[bot_id]
            
            # Stop subprocess
            if bot_id in self.bot_processes:
                process = self.bot_processes[bot_id]
                try:
                    process.terminate()
                    await asyncio.sleep(1)
                    if process.returncode is None:
                        process.kill()
                except:
                    pass
                del self.bot_processes[bot_id]
            
            # Clean up running bots info and temp files
            if bot_id in self.running_bots:
                bot_info = self.running_bots[bot_id]
                if 'temp_dir' in bot_info:
                    try:
                        import shutil
                        shutil.rmtree(bot_info['temp_dir'], ignore_errors=True)
                    except:
                        pass
                del self.running_bots[bot_id]
            
            # Remove start time
            if bot_id in self.bot_start_times:
                del self.bot_start_times[bot_id]
            
            logger.info(f"✅ Bot {bot_id} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot {bot_id}: {e}")
            return False
    
    async def restart_bot(self, bot_id: str):
        """Restart a hosted bot"""
        try:
            bot = await self.db.get_bot(bot_id)
            if not bot:
                logger.error(f"Bot {bot_id} not found in database")
                return False
            
            file_type = bot.get('file_metadata', {}).get('file_type', 'py')
            
            logger.info(f"🔄 Restarting {file_type.upper()} bot {bot_id}")
            await self.stop_bot(bot_id)
            await asyncio.sleep(2)
            
            success = await self.start_bot(bot_id, bot["token"], bot["script"], file_type)
            
            if success:
                logger.info(f"✅ Bot {bot_id} restarted successfully")
                try:
                    await self.db.increment_restart_count(bot_id)
                except:
                    pass
            else:
                logger.error(f"❌ Failed to restart bot {bot_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error restarting bot {bot_id}: {e}")
            return False
    
    async def stop_all_bots(self):
        """Stop all running bots"""
        logger.info("🛑 Stopping all bots...")
        
        # Get all bot IDs from both sources
        all_bot_ids = set()
        all_bot_ids.update(self.bot_clients.keys())
        all_bot_ids.update(self.bot_processes.keys())
        
        stopped_count = 0
        for bot_id in all_bot_ids:
            try:
                await self.stop_bot(bot_id)
                stopped_count += 1
            except Exception as e:
                logger.error(f"Error stopping bot {bot_id}: {e}")
        
        logger.info(f"✅ Stopped {stopped_count} bots")
    
    async def get_bot_stats(self, bot_id: str):
        """Get statistics for a specific bot"""
        is_running = bot_id in self.bot_clients or bot_id in self.bot_processes
        
        if not is_running:
            return {
                "status": "stopped",
                "uptime": 0,
                "uptime_readable": "0 seconds"
            }
        
        # Calculate uptime
        start_time = self.bot_start_times.get(bot_id, time.time())
        uptime_seconds = int(time.time() - start_time)
        
        # Format uptime
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        if hours > 0:
            uptime_readable = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            uptime_readable = f"{minutes}m {seconds}s"
        else:
            uptime_readable = f"{seconds}s"
        
        bot_type = self.running_bots.get(bot_id, {}).get('type', 'unknown')
        
        return {
            "status": "running",
            "uptime": uptime_seconds,
            "uptime_readable": uptime_readable,
            "bot_type": bot_type,
            "client_status": "connected"
        }
    
    async def restart_all_bots(self):
        """Restart all bots from database"""
        try:
            logger.info("🔄 Restarting all bots from database...")
            
            # Get all bots with running status
            all_bots = await self.db.get_all_bots()
            
            started_count = 0
            failed_count = 0
            
            for bot in all_bots:
                if bot.get("status") == "running":
                    bot_id = str(bot["_id"])
                    file_type = bot.get('file_metadata', {}).get('file_type', 'py')
                    
                    try:
                        success = await self.start_bot(
                            bot_id, 
                            bot["token"], 
                            bot["script"],
                            file_type
                        )
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
            logger.error(f"❌ Error restarting all bots: {e}")
            return 0, 0
    
    def is_bot_running(self, bot_id: str):
        """Check if a bot is currently running"""
        return bot_id in self.bot_clients or bot_id in self.bot_processes
    
    def get_running_bots_count(self):
        """Get count of currently running bots"""
        return len(set(list(self.bot_clients.keys()) + list(self.bot_processes.keys())))
    
    def get_running_bot_ids(self):
        """Get list of running bot IDs"""
        return list(set(list(self.bot_clients.keys()) + list(self.bot_processes.keys())))
    
    def get_bots_by_type(self):
        """Get count of bots grouped by language"""
        type_counts = {}
        for bot_id, info in self.running_bots.items():
            bot_type = info.get('type', 'unknown')
            type_counts[bot_type] = type_counts.get(bot_type, 0) + 1
        return type_counts
    
    async def get_bot_logs(self, bot_id: str, lines: int = 50):
        """Get recent logs for a bot (for subprocess bots)"""
        if bot_id not in self.bot_processes:
            return "Bot not running or no logs available"
        
        try:
            process = self.bot_processes[bot_id]
            # Get stdout and stderr
            stdout_data = ""
            stderr_data = ""
            
            if process.stdout:
                try:
                    stdout_data = await asyncio.wait_for(
                        process.stdout.read(4096),
                        timeout=1.0
                    )
                    stdout_data = stdout_data.decode('utf-8', errors='ignore')
                except asyncio.TimeoutError:
                    pass
            
            if process.stderr:
                try:
                    stderr_data = await asyncio.wait_for(
                        process.stderr.read(4096),
                        timeout=1.0
                    )
                    stderr_data = stderr_data.decode('utf-8', errors='ignore')
                except asyncio.TimeoutError:
                    pass
            
            logs = ""
            if stdout_data:
                logs += f"STDOUT:\n{stdout_data}\n"
            if stderr_data:
                logs += f"STDERR:\n{stderr_data}\n"
            
            return logs if logs else "No recent logs"
            
        except Exception as e:
            logger.error(f"Error getting logs for bot {bot_id}: {e}")
            return f"Error retrieving logs: {str(e)}"
    
    async def health_check(self):
        """Perform health check on all running bots"""
        results = {
            'total_running': 0,
            'healthy': 0,
            'unhealthy': 0,
            'by_type': {}
        }
        
        all_bot_ids = set(list(self.bot_clients.keys()) + list(self.bot_processes.keys()))
        results['total_running'] = len(all_bot_ids)
        
        for bot_id in all_bot_ids:
            bot_info = self.running_bots.get(bot_id, {})
            bot_type = bot_info.get('type', 'unknown')
            
            # Check if bot is healthy
            is_healthy = False
            
            if bot_type == 'python':
                # Check if client is connected
                if bot_id in self.bot_clients:
                    client = self.bot_clients[bot_id]
                    is_healthy = client.is_connected
            else:
                # Check if process is still running
                if bot_id in self.bot_processes:
                    process = self.bot_processes[bot_id]
                    is_healthy = process.returncode is None
            
            if is_healthy:
                results['healthy'] += 1
            else:
                results['unhealthy'] += 1
            
            # Count by type
            if bot_type not in results['by_type']:
                results['by_type'][bot_type] = {'total': 0, 'healthy': 0}
            results['by_type'][bot_type]['total'] += 1
            if is_healthy:
                results['by_type'][bot_type]['healthy'] += 1
        
        return results
    
    async def cleanup_temp_files(self):
        """Clean up temporary files from stopped bots"""
        try:
            logger.info("🧹 Cleaning up temporary files...")
            cleaned = 0
            
            # This would be called periodically
            # For now, it's a placeholder for future implementation
            
            logger.info(f"✅ Cleaned {cleaned} temporary files")
            return cleaned
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
    
    def get_system_stats(self):
        """Get system statistics for the bot runner"""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'running_bots': self.get_running_bots_count(),
                'bots_by_type': self.get_bots_by_type()
            }
        except ImportError:
            # psutil not installed
            return {
                'running_bots': self.get_running_bots_count(),
                'bots_by_type': self.get_bots_by_type()
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {'error': str(e)}
    
    async def graceful_shutdown(self):
        """Gracefully shutdown all bots"""
        logger.info("🛑 Initiating graceful shutdown...")
        
        try:
            # Stop all bots
            await self.stop_all_bots()
            
            # Clean up temp files
            await self.cleanup_temp_files()
            
            logger.info("✅ Graceful shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
    
    async def get_detailed_bot_info(self, bot_id: str):
        """Get detailed information about a specific bot"""
        try:
            is_running = self.is_bot_running(bot_id)
            bot_info = self.running_bots.get(bot_id, {})
            
            info = {
                'bot_id': bot_id,
                'is_running': is_running,
                'type': bot_info.get('type', 'unknown'),
                'status': 'running' if is_running else 'stopped'
            }
            
            if is_running:
                stats = await self.get_bot_stats(bot_id)
                info.update(stats)
                
                # Add type-specific info
                if info['type'] == 'python':
                    client = self.bot_clients.get(bot_id)
                    if client:
                        info['is_connected'] = client.is_connected
                        info['client_type'] = 'Pyrogram'
                elif info['type'] in ['javascript', 'shell', 'ruby', 'php', 'go']:
                    process = self.bot_processes.get(bot_id)
                    if process:
                        info['pid'] = process.pid
                        info['returncode'] = process.returncode
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting detailed bot info for {bot_id}: {e}")
            return {'error': str(e)}
    
    async def validate_runtime_available(self, file_type: str):
        """Check if the required runtime is available on the system"""
        runtime_map = {
            'py': ['python3', '--version'],
            'js': ['node', '--version'],
            'sh': ['bash', '--version'],
            'rb': ['ruby', '--version'],
            'php': ['php', '--version'],
            'go': ['go', 'version']
        }
        
        if file_type not in runtime_map:
            return True, "Unknown runtime"
        
        try:
            result = subprocess.run(
                runtime_map[file_type],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.decode().strip()
                return True, version
            else:
                return False, "Runtime not available"
                
        except FileNotFoundError:
            return False, f"{file_type.upper()} runtime not installed"
        except Exception as e:
            return False, str(e)
    
    async def get_available_runtimes(self):
        """Get list of available programming language runtimes"""
        runtimes = {}
        file_types = ['py', 'js', 'sh', 'rb', 'php', 'go']
        
        for file_type in file_types:
            available, info = await self.validate_runtime_available(file_type)
            runtimes[file_type] = {
                'available': available,
                'info': info,
                'name': {
                    'py': 'Python',
                    'js': 'Node.js',
                    'sh': 'Bash',
                    'rb': 'Ruby',
                    'php': 'PHP',
                    'go': 'Go'
                }.get(file_type, file_type.upper())
            }
        
        return runtimes
    
    async def export_bot_config(self, bot_id: str):
        """Export bot configuration for backup"""
        try:
            bot = await self.db.get_bot(bot_id)
            if not bot:
                return None
            
            config = {
                'bot_id': str(bot['_id']),
                'bot_username': bot.get('bot_username'),
                'created_at': bot.get('created_at'),
                'file_type': bot.get('file_metadata', {}).get('file_type', 'py'),
                'file_name': bot.get('file_metadata', {}).get('file_name', 'script.py'),
                'script': bot.get('script'),
                'status': bot.get('status')
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Error exporting bot config: {e}")
            return None
    
    def __del__(self):
        """Cleanup when runner is destroyed"""
        try:
            # This will be called when the object is garbage collected
            # In production, use graceful_shutdown instead
            logger.info("BotRunner destructor called")
        except:
            pass


# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"⏱️ {func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ {func.__name__} failed after {elapsed:.2f}s: {e}")
            raise
    return wrapper


# Usage example in main file:
"""
# Initialize runner
runner = BotRunner(db)

# Start a Python bot
await runner.start_bot(bot_id, token, script, 'py')

# Start a JavaScript bot
await runner.start_bot(bot_id, token, script, 'js')

# Start a Shell script bot
await runner.start_bot(bot_id, token, script, 'sh')

# Get bot statistics
stats = await runner.get_bot_stats(bot_id)

# Health check
health = await runner.health_check()

# Get available runtimes
runtimes = await runner.get_available_runtimes()

# Graceful shutdown
await runner.graceful_shutdown()
"""
