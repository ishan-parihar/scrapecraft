from typing import List, Dict, Optional, Any
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List as ListType
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class UserDatabase:
    """Real file-based user database for authentication system."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to data/users.json in the backend directory
            backend_dir = Path(__file__).parent.parent.parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "users.json"
        
        self.db_path = Path(db_path)
        self._ensure_database_exists()
        self._load_users()
    
    def _ensure_database_exists(self):
        """Ensure the database file and directory exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.db_path.exists():
            # Initialize with empty database structure
            initial_data = {
                "users": {},
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
            }
            with open(self.db_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
            logger.info(f"Created user database at {self.db_path}")
    
    def _load_users(self):
        """Load users from database file."""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.users_db = data.get("users", {})
                self.metadata = data.get("metadata", {})
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to load user database: {e}")
            self.users_db = {}
            self.metadata = {"created_at": datetime.utcnow().isoformat(), "version": "1.0"}
    
    def _save_users(self):
        """Save users to database file."""
        try:
            data = {
                "users": self.users_db,
                "metadata": {
                    **self.metadata,
                    "updated_at": datetime.utcnow().isoformat(),
                    "user_count": len(self.users_db)
                }
            }
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user database: {e}")
            raise
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user from database."""
        return self.users_db.get(username)
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user in the database."""
        username = user_data.get("username")
        if username in self.users_db:
            logger.warning(f"User {username} already exists")
            return False
        
        try:
            # Add metadata
            user_data.update({
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "disabled": False,
                "id": f"user-{hashlib.md5(username.encode()).hexdigest()[:8]}"
            })
            
            self.users_db[username] = user_data
            self._save_users()
            logger.info(f"Created user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            return False
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """Update user data in database."""
        if username not in self.users_db:
            logger.warning(f"User {username} not found for update")
            return False
        
        try:
            self.users_db[username].update({
                **updates,
                "updated_at": datetime.utcnow().isoformat()
            })
            self._save_users()
            logger.info(f"Updated user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to update user {username}: {e}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """Delete user from database."""
        if username not in self.users_db:
            logger.warning(f"User {username} not found for deletion")
            return False
        
        try:
            del self.users_db[username]
            self._save_users()
            logger.info(f"Deleted user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user {username}: {e}")
            return False
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (without sensitive data)."""
        users = []
        for username, user_data in self.users_db.items():
            safe_user = {
                "username": username,
                "email": user_data.get("email", ""),
                "full_name": user_data.get("full_name", ""),
                "disabled": user_data.get("disabled", False),
                "created_at": user_data.get("created_at", ""),
                "updated_at": user_data.get("updated_at", ""),
                "id": user_data.get("id", "")
            }
            users.append(safe_user)
        return users
    
    def authenticate_user(self, username: str, password: str, password_hasher) -> Optional[Dict[str, Any]]:
        """Authenticate user with password."""
        user_data = self.get_user(username)
        if not user_data:
            logger.warning(f"Authentication failed: user {username} not found")
            return None
        
        if user_data.get("disabled", False):
            logger.warning(f"Authentication failed: user {username} is disabled")
            return None
        
        hashed_password = user_data.get("hashed_password")
        if not hashed_password:
            logger.error(f"User {username} has no hashed password")
            return None
        
        try:
            if password_hasher.verify(password, hashed_password):
                logger.info(f"User {username} authenticated successfully")
                return user_data
            else:
                logger.warning(f"Authentication failed: invalid password for {username}")
                return None
        except Exception as e:
            logger.error(f"Password verification error for {username}: {e}")
            return None
    
    def change_password(self, username: str, new_password: str, password_hasher) -> bool:
        """Change user password."""
        user_data = self.get_user(username)
        if not user_data:
            return False
        
        try:
            hashed_password = password_hasher.hash(new_password)
            return self.update_user(username, {
                "hashed_password": hashed_password,
                "password_changed_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to change password for {username}: {e}")
            return False
    
    def get_user_count(self) -> int:
        """Get total number of users."""
        return len(self.users_db)
    
    def get_active_users(self) -> int:
        """Get number of active (non-disabled) users."""
        return sum(1 for user in self.users_db.values() if not user.get("disabled", False))

# Global database instance
_user_db = None

def get_user_database() -> UserDatabase:
    """Get the global user database instance."""
    global _user_db
    if _user_db is None:
        _user_db = UserDatabase()
    return _user_db

# Compatibility functions to replace the old in-memory database system
def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user from real database (replaces in-memory database)."""
    db = get_user_database()
    return db.get_user(username)

def create_user_in_db(user_data: Dict[str, Any]) -> bool:
    """Create user in real database."""
    db = get_user_database()
    return db.create_user(user_data)

def update_user_in_db(username: str, updates: Dict[str, Any]) -> bool:
    """Update user in real database."""
    db = get_user_database()
    return db.update_user(username, updates)

def authenticate_user_in_db(username: str, password: str, password_hasher) -> Optional[Dict[str, Any]]:
    """Authenticate user using real database."""
    db = get_user_database()
    return db.authenticate_user(username, password, password_hasher)

def list_all_users() -> List[Dict[str, Any]]:
    """List all users from real database."""
    db = get_user_database()
    return db.list_users()

# Initialize with a default user if the database is empty
def initialize_default_user():
    """Initialize database with a default admin user if empty."""
    db = get_user_database()
    
    if db.get_user_count() == 0:
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
            
            default_user = {
                "username": "admin",
                "email": "admin@scrapecraft.local",
                "full_name": "Default Admin User",
                "hashed_password": pwd_context.hash("admin123"),
                "disabled": False,
                "role": "admin",
                "is_default": True
            }
            
            db.create_user(default_user)
            logger.info("Created default admin user: admin/admin123")
            logger.warning("Please change the default admin password after first login!")
        except Exception as e:
            logger.error(f"Failed to create default user: {e}")
            # Create without password for now
            default_user = {
                "username": "admin",
                "email": "admin@scrapecraft.local",
                "full_name": "Default Admin User",
                "hashed_password": "",
                "disabled": False,
                "role": "admin",
                "is_default": True
            }
            db.create_user(default_user)

# Initialize the database
initialize_default_user()