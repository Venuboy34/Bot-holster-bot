"""
Database Manager for Bot Hoster (Enhanced Multi-Language Support)
Developer: @Zeroboy216
Channel: @zerodevbro
Version: 2.0
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config import MONGO_URL, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DATABASE_NAME]
        self.bots = self.db.bots
        self.users = self.db.users
        self.states = self.db.states
        self.logs = self.db.logs  # New: Bot logs collection
        logger.info("✅ Database connected successfully!")
    
    # User methods
    async def add_user(self, user_id: int, name: str):
        """Add or update user in database"""
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "name": name,
                    "last_active": datetime.now()
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "joined_at": datetime.now(),
                    "total_bots_created": 0
                }
            },
            upsert=True
        )
    
    async def get_all_users(self):
        """Get all users"""
        return await self.users.find().to_list(length=None)
    
    async def get_user_count(self):
        """Get total user count"""
        return await self.users.count_documents({})
    
    async def get_active_users(self, days: int = 7):
        """Get users active in last N days"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        return await self.users.count_documents({"last_active": {"$gte": cutoff_date}})
    
    async def increment_user_bot_count(self, user_id: int):
        """Increment total bots created by user"""
        await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"total_bots_created": 1}}
        )
    
    # Bot methods
    async def add_bot(self, user_id: int, token: str, script: str, bot_info: dict, file_metadata: dict = None):
        """Add a new bot to database with file metadata"""
        bot_doc = {
            "user_id": user_id,
            "token": token,
            "script": script,
            "bot_username": bot_info.get("username", "unknown"),
            "bot_name": bot_info.get("first_name", "Unknown Bot"),
            "bot_id": bot_info.get("id"),
            "status": "stopped",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_restart": None,
            "error_count": 0,
            "restart_count": 0,
            "uptime": 0,
            "auto_restart": True,
            "file_metadata": file_metadata or {
                "file_name": "script.py",
                "file_type": "py",
                "file_size": len(script)
            }
        }
        result = await self.bots.insert_one(bot_doc)
        logger.info(f"✅ Bot added: {result.inserted_id} by user {user_id}")
        
        # Increment user's bot count
        await self.increment_user_bot_count(user_id)
        
        return str(result.inserted_id)
    
    async def get_bot(self, bot_id: str):
        """Get bot by ID"""
        from bson import ObjectId
        try:
            return await self.bots.find_one({"_id": ObjectId(bot_id)})
        except Exception as e:
            logger.error(f"Error getting bot {bot_id}: {e}")
            return None
    
    async def get_user_bots(self, user_id: int):
        """Get all bots owned by a user"""
        bots = await self.bots.find({"user_id": user_id}).to_list(length=None)
        for bot in bots:
            bot["_id"] = str(bot["_id"])
        return bots
    
    async def get_all_bots(self):
        """Get all bots"""
        bots = await self.bots.find().to_list(length=None)
        for bot in bots:
            bot["_id"] = str(bot["_id"])
        return bots
    
    async def get_running_bots(self):
        """Get all running bots"""
        bots = await self.bots.find({"status": "running"}).to_list(length=None)
        for bot in bots:
            bot["_id"] = str(bot["_id"])
        return bots
    
    async def update_bot_status(self, bot_id: str, status: str):
        """Update bot status"""
        from bson import ObjectId
        try:
            await self.bots.update_one(
                {"_id": ObjectId(bot_id)},
                {
                    "$set": {
                        "status": status,
                        "last_restart": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )
            logger.info(f"Bot {bot_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
    
    async def update_bot_script(self, bot_id: str, script: str):
        """Update bot script"""
        from bson import ObjectId
        try:
            await self.bots.update_one(
                {"_id": ObjectId(bot_id)},
                {
                    "$set": {
                        "script": script,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )
            logger.info(f"Bot {bot_id} script updated")
        except Exception as e:
            logger.error(f"Error updating bot script: {e}")
    
    async def delete_bot(self, bot_id: str):
        """Delete a bot"""
        from bson import ObjectId
        try:
            await self.bots.delete_one({"_id": ObjectId(bot_id)})
            logger.info(f"Bot {bot_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting bot: {e}")
    
    async def increment_error_count(self, bot_id: str):
        """Increment error count for a bot"""
        from bson import ObjectId
        try:
            await self.bots.update_one(
                {"_id": ObjectId(bot_id)},
                {"$inc": {"error_count": 1}}
            )
        except Exception as e:
            logger.error(f"Error incrementing error count: {e}")
    
    async def increment_restart_count(self, bot_id: str):
        """Increment restart count for a bot"""
        from bson import ObjectId
        try:
            await self.bots.update_one(
                {"_id": ObjectId(bot_id)},
                {
                    "$inc": {"restart_count": 1},
                    "$set": {"last_restart": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                }
            )
        except Exception as e:
            logger.error(f"Error incrementing restart count: {e}")
    
    async def update_bot_uptime(self, bot_id: str, uptime_seconds: int):
        """Update bot uptime"""
        from bson import ObjectId
        try:
            await self.bots.update_one(
                {"_id": ObjectId(bot_id)},
                {"$set": {"uptime": uptime_seconds}}
            )
        except Exception as e:
            logger.error(f"Error updating bot uptime: {e}")
    
    async def get_bot_count(self):
        """Get total bot count"""
        return await self.bots.count_documents({})
    
    async def get_running_bot_count(self):
        """Get running bot count"""
        return await self.bots.count_documents({"status": "running"})
    
    async def get_bots_by_type(self):
        """Get bot count grouped by file type"""
        pipeline = [
            {
                "$group": {
                    "_id": "$file_metadata.file_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        results = await self.bots.aggregate(pipeline).to_list(length=None)
        return {item["_id"]: item["count"] for item in results}
    
    async def get_user_bot_count(self, user_id: int):
        """Get number of bots owned by a user"""
        return await self.bots.count_documents({"user_id": user_id})
    
    # State management methods
    async def set_user_state(self, user_id: int, action: str, message_id: int = None, data: dict = None):
        """Set user state for multi-step operations"""
        await self.states.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "action": action,
                    "message_id": message_id,
                    "data": data or {},
                    "timestamp": datetime.now()
                }
            },
            upsert=True
        )
    
    async def get_user_state(self, user_id: int):
        """Get user state"""
        return await self.states.find_one({"user_id": user_id})
    
    async def clear_user_state(self, user_id: int):
        """Clear user state"""
        await self.states.delete_one({"user_id": user_id})
    
    # Log methods
    async def add_log(self, bot_id: str, log_type: str, message: str):
        """Add a log entry"""
        log_doc = {
            "bot_id": bot_id,
            "log_type": log_type,  # 'error', 'info', 'warning', 'restart'
            "message": message,
            "timestamp": datetime.now()
        }
        await self.logs.insert_one(log_doc)
    
    async def get_bot_logs(self, bot_id: str, limit: int = 50):
        """Get recent logs for a bot"""
        logs = await self.logs.find({"bot_id": bot_id}).sort("timestamp", -1).limit(limit).to_list(length=limit)
        return logs
    
    async def clear_old_logs(self, days: int = 30):
        """Clear logs older than N days"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        result = await self.logs.delete_many({"timestamp": {"$lt": cutoff_date}})
        logger.info(f"Cleared {result.deleted_count} old logs")
        return result.deleted_count
    
    # Statistics methods
    async def get_stats(self):
        """Get system statistics"""
        total_users = await self.get_user_count()
        total_bots = await self.get_bot_count()
        running_bots = await self.get_running_bot_count()
        active_users = await self.get_active_users(7)
        bots_by_type = await self.get_bots_by_type()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_bots": total_bots,
            "running_bots": running_bots,
            "stopped_bots": total_bots - running_bots,
            "bots_by_type": bots_by_type
        }
    
    async def get_detailed_stats(self):
        """Get detailed system statistics"""
        stats = await self.get_stats()
        
        # Get top users
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "bot_count": {"$sum": 1}
                }
            },
            {"$sort": {"bot_count": -1}},
            {"$limit": 10}
        ]
        top_users = await self.bots.aggregate(pipeline).to_list(length=10)
        
        # Get bots with most errors
        pipeline = [
            {"$sort": {"error_count": -1}},
            {"$limit": 10}
        ]
        error_prone_bots = await self.bots.aggregate(pipeline).to_list(length=10)
        
        # Get bots with most restarts
        pipeline = [
            {"$sort": {"restart_count": -1}},
            {"$limit": 10}
        ]
        restart_prone_bots = await self.bots.aggregate(pipeline).to_list(length=10)
        
        stats["top_users"] = top_users
        stats["error_prone_bots"] = error_prone_bots
        stats["restart_prone_bots"] = restart_prone_bots
        
        return stats
    
    # Backup methods
    async def export_bot_data(self, bot_id: str):
        """Export all data for a specific bot"""
        bot = await self.get_bot(bot_id)
        if not bot:
            return None
        
        logs = await self.get_bot_logs(bot_id, limit=100)
        
        return {
            "bot": bot,
            "logs": logs,
            "export_date": datetime.now().isoformat()
        }
    
    async def export_user_data(self, user_id: int):
        """Export all data for a specific user"""
        user = await self.users.find_one({"user_id": user_id})
        bots = await self.get_user_bots(user_id)
        
        return {
            "user": user,
            "bots": bots,
            "export_date": datetime.now().isoformat()
        }
    
    # Maintenance methods
    async def cleanup_orphaned_states(self, hours: int = 24):
        """Clean up old user states"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(hours=hours)
        result = await self.states.delete_many({"timestamp": {"$lt": cutoff_date}})
        logger.info(f"Cleaned up {result.deleted_count} orphaned states")
        return result.deleted_count
    
    async def get_database_stats(self):
        """Get database statistics"""
        return {
            "users_count": await self.users.count_documents({}),
            "bots_count": await self.bots.count_documents({}),
            "states_count": await self.states.count_documents({}),
            "logs_count": await self.logs.count_documents({})
        }
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users indexes
            await self.users.create_index("user_id", unique=True)
            await self.users.create_index("last_active")
            
            # Bots indexes
            await self.bots.create_index("user_id")
            await self.bots.create_index("status")
            await self.bots.create_index("bot_username")
            await self.bots.create_index("created_at")
            
            # States indexes
            await self.states.create_index("user_id", unique=True)
            await self.states.create_index("timestamp")
            
            # Logs indexes
            await self.logs.create_index("bot_id")
            await self.logs.create_index("timestamp")
            await self.logs.create_index("log_type")
            
            logger.info("✅ Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("Database connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.client.close()
        except:
            pass
