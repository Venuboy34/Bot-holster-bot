"""
Database Manager for Bot Hoster
Developer: @Zeroboy216
Channel: @zerodevbro
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
                    "joined_at": datetime.now()
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
    
    # Bot methods
    async def add_bot(self, user_id: int, token: str, script: str, bot_info: dict):
        """Add a new bot to database"""
        bot_doc = {
            "user_id": user_id,
            "token": token,
            "script": script,
            "bot_username": bot_info.get("username", "unknown"),
            "bot_name": bot_info.get("first_name", "Unknown Bot"),
            "status": "stopped",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_restart": None,
            "error_count": 0
        }
        result = await self.bots.insert_one(bot_doc)
        logger.info(f"✅ Bot added: {result.inserted_id} by user {user_id}")
        return str(result.inserted_id)
    
    async def get_bot(self, bot_id: str):
        """Get bot by ID"""
        from bson import ObjectId
        return await self.bots.find_one({"_id": ObjectId(bot_id)})
    
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
        await self.bots.update_one(
            {"_id": ObjectId(bot_id)},
            {"$set": {"status": status, "last_restart": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
        )
        logger.info(f"Bot {bot_id} status updated to {status}")
    
    async def update_bot_script(self, bot_id: str, script: str):
        """Update bot script"""
        from bson import ObjectId
        await self.bots.update_one(
            {"_id": ObjectId(bot_id)},
            {"$set": {"script": script}}
        )
        logger.info(f"Bot {bot_id} script updated")
    
    async def delete_bot(self, bot_id: str):
        """Delete a bot"""
        from bson import ObjectId
        await self.bots.delete_one({"_id": ObjectId(bot_id)})
        logger.info(f"Bot {bot_id} deleted")
    
    async def increment_error_count(self, bot_id: str):
        """Increment error count for a bot"""
        from bson import ObjectId
        await self.bots.update_one(
            {"_id": ObjectId(bot_id)},
            {"$inc": {"error_count": 1}}
        )
    
    async def get_bot_count(self):
        """Get total bot count"""
        return await self.bots.count_documents({})
    
    async def get_running_bot_count(self):
        """Get running bot count"""
        return await self.bots.count_documents({"status": "running"})
    
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
    
    # Statistics methods
    async def get_stats(self):
        """Get system statistics"""
        total_users = await self.get_user_count()
        total_bots = await self.get_bot_count()
        running_bots = await self.get_running_bot_count()
        
        return {
            "total_users": total_users,
            "total_bots": total_bots,
            "running_bots": running_bots,
            "stopped_bots": total_bots - running_bots
        }
