"""
Enhanced database service for ScrapeCraft with proper persistence layer.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import settings
import asyncio
from contextlib import asynccontextmanager

# Import shared base and models
from app.models.sqlalchemy.base import Base

logger = logging.getLogger(__name__)

# Create engine with better configuration
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def get_async_db():
    """Async context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


class DatabasePersistenceService:
    """
    Enhanced database persistence service that replaces in-memory storage.
    
    This service provides methods for persisting investigation data,
    workflow states, task results, and other critical data that was
    previously stored only in memory.
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        # Rate limiting to prevent database spam
        self._last_store_time = {}
        self._pending_states = {}
        self._store_lock = asyncio.Lock()
        self._min_store_interval = 0.5  # Minimum 0.5 seconds between stores per investigation
        
    def initialize_database(self):
        """Initialize database tables and create indexes."""
        try:
            # Create tables manually using raw SQL to avoid import issues
            with self.engine.connect() as conn:
                # Create persistence tables from migration 002
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS investigation_states (
                        id INTEGER PRIMARY KEY,
                        investigation_id TEXT NOT NULL UNIQUE,
                        state_data TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS workflow_states (
                        id INTEGER PRIMARY KEY,
                        workflow_id TEXT NOT NULL UNIQUE,
                        workflow_data TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS websocket_connections (
                        id INTEGER PRIMARY KEY,
                        connection_id TEXT NOT NULL UNIQUE,
                        pipeline_id TEXT,
                        metadata TEXT,
                        connected_at DATETIME NOT NULL,
                        last_activity DATETIME NOT NULL
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS task_results (
                        id INTEGER PRIMARY KEY,
                        task_id TEXT NOT NULL UNIQUE,
                        task_data TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        user_id TEXT,
                        session_id TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        action TEXT NOT NULL,
                        resource_type TEXT,
                        resource_id TEXT,
                        details TEXT,
                        timestamp DATETIME NOT NULL,
                        severity TEXT NOT NULL DEFAULT 'info',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        deleted_at DATETIME NULL
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY,
                        session_id TEXT NOT NULL UNIQUE,
                        user_id TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at DATETIME NOT NULL,
                        last_activity DATETIME NOT NULL,
                        expires_at DATETIME NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        session_data TEXT
                    )
                """))
                
                conn.commit()
                
            logger.info("Database tables initialized successfully")
            
            # Create additional indexes for performance
            with self.engine.connect() as conn:
                # Check if tables exist before creating indexes
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='investigations'"))
                if result.fetchone():
                    # Investigation indexes
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_investigation_status ON investigations (status)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_investigation_created_at ON investigations (created_at)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_investigation_priority ON investigations (priority)"))
                
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"))
                if result.fetchone():
                    # Task indexes
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_task_status ON tasks (status)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_task_created_at ON tasks (created_at)"))
                
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='websocket_connections'"))
                if result.fetchone():
                    # WebSocket connection indexes
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_websocket_connection_id ON websocket_connections (connection_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_websocket_pipeline_id ON websocket_connections (pipeline_id)"))
                
                # Persistence tables indexes (from migration 002)
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"))
                if result.fetchone():
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs (timestamp)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs (user_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs (event_type)"))
                
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def store_investigation_state(self, investigation_id: str, state_data: Dict[str, Any]) -> bool:
        """Store investigation state data with rate limiting to prevent database spam."""
        try:
            async with self._store_lock:
                current_time = asyncio.get_event_loop().time()
                last_time = self._last_store_time.get(investigation_id, 0)
                
                # Check if enough time has passed since last store
                time_since_last = current_time - last_time
                
                if time_since_last < self._min_store_interval:
                    # Store in pending states for later
                    self._pending_states[investigation_id] = state_data
                    logger.debug(f"Rate limited investigation state store for {investigation_id}, keeping pending")
                    return True
                
                # Store the state (either pending or current)
                state_to_store = self._pending_states.pop(investigation_id, state_data)
                
                with SessionLocal() as db:
                    # Check if investigation state already exists
                    existing = db.execute(
                        text("SELECT * FROM investigation_states WHERE investigation_id = :investigation_id"),
                        {"investigation_id": investigation_id}
                    ).fetchone()
                    
                    state_json = json.dumps(state_to_store, default=str)
                    
                    if existing:
                        # Update existing record
                        db.execute(
                            text("""
                                UPDATE investigation_states 
                                SET state_data = :state_data, updated_at = :updated_at
                                WHERE investigation_id = :investigation_id
                            """),
                            {
                                "investigation_id": investigation_id,
                                "state_data": state_json,
                                "updated_at": datetime.utcnow()
                            }
                        )
                    else:
                        # Insert new record
                        db.execute(
                            text("""
                                INSERT INTO investigation_states 
                                (investigation_id, state_data, created_at, updated_at)
                                VALUES (:investigation_id, :state_data, :created_at, :updated_at)
                            """),
                            {
                                "investigation_id": investigation_id,
                                "state_data": state_json,
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow()
                            }
                        )
                    
                    db.commit()
                    
                    # Update last store time
                    self._last_store_time[investigation_id] = current_time
                    
                    logger.debug(f"Stored investigation state for {investigation_id}")
                    
                return True
                
        except Exception as e:
            logger.error(f"Failed to store investigation state for {investigation_id}: {e}")
            return False
    
    async def get_investigation_state(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve investigation state data."""
        try:
            with SessionLocal() as db:
                result = db.execute(
                    text("SELECT state_data FROM investigation_states WHERE investigation_id = :investigation_id"),
                    {"investigation_id": investigation_id}
                ).fetchone()
                
                if result:
                    return json.loads(result[0])
                return None
                
        except Exception as e:
            logger.error(f"Failed to get investigation state for {investigation_id}: {e}")
            return None
    
    async def store_workflow_state(self, workflow_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Store workflow state data."""
        try:
            with SessionLocal() as db:
                # Check if workflow state already exists
                existing = db.execute(
                    text("SELECT * FROM workflow_states WHERE workflow_id = :workflow_id"),
                    {"workflow_id": workflow_id}
                ).fetchone()
                
                workflow_json = json.dumps(workflow_data, default=str)
                
                if existing:
                    # Update existing record
                    db.execute(
                        text("""
                            UPDATE workflow_states 
                            SET workflow_data = :workflow_data, updated_at = :updated_at
                            WHERE workflow_id = :workflow_id
                        """),
                        {
                            "workflow_id": workflow_id,
                            "workflow_data": workflow_json,
                            "updated_at": datetime.utcnow()
                        }
                    )
                else:
                    # Insert new record
                    db.execute(
                        text("""
                            INSERT INTO workflow_states 
                            (workflow_id, workflow_data, created_at, updated_at)
                            VALUES (:workflow_id, :workflow_data, :created_at, :updated_at)
                        """),
                        {
                            "workflow_id": workflow_id,
                            "workflow_data": workflow_json,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    )
                
                db.commit()
                logger.info(f"Stored workflow state for {workflow_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store workflow state for {workflow_id}: {e}")
            return False
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow state data."""
        try:
            with SessionLocal() as db:
                result = db.execute(
                    text("SELECT workflow_data FROM workflow_states WHERE workflow_id = :workflow_id"),
                    {"workflow_id": workflow_id}
                ).fetchone()
                
                if result:
                    return json.loads(result[0])
                return None
                
        except Exception as e:
            logger.error(f"Failed to get workflow state for {workflow_id}: {e}")
            return None
    
    async def store_websocket_connection(self, connection_id: str, pipeline_id: str, metadata: Dict[str, Any]) -> bool:
        """Store WebSocket connection metadata."""
        try:
            with SessionLocal() as db:
                metadata_json = json.dumps(metadata, default=str)
                
                db.execute(
                    text("""
                        INSERT OR REPLACE INTO websocket_connections 
                        (connection_id, pipeline_id, metadata, connected_at, last_activity)
                        VALUES (:connection_id, :pipeline_id, :metadata, :connected_at, :last_activity)
                    """),
                    {
                        "connection_id": connection_id,
                        "pipeline_id": pipeline_id,
                        "metadata": metadata_json,
                        "connected_at": datetime.utcnow(),
                        "last_activity": datetime.utcnow()
                    }
                )
                
                db.commit()
                logger.debug(f"Stored WebSocket connection {connection_id} for pipeline {pipeline_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store WebSocket connection {connection_id}: {e}")
            return False
    
    async def remove_websocket_connection(self, connection_id: str) -> bool:
        """Remove WebSocket connection metadata."""
        try:
            with SessionLocal() as db:
                db.execute(
                    text("DELETE FROM websocket_connections WHERE connection_id = :connection_id"),
                    {"connection_id": connection_id}
                )
                
                db.commit()
                logger.debug(f"Removed WebSocket connection {connection_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove WebSocket connection {connection_id}: {e}")
            return False
    
    async def get_websocket_connections(self, pipeline_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get WebSocket connections, optionally filtered by pipeline_id."""
        try:
            with SessionLocal() as db:
                if pipeline_id:
                    results = db.execute(
                        text("""
                            SELECT connection_id, pipeline_id, metadata, connected_at, last_activity
                            FROM websocket_connections 
                            WHERE pipeline_id = :pipeline_id
                            ORDER BY connected_at DESC
                        """),
                        {"pipeline_id": pipeline_id}
                    ).fetchall()
                else:
                    results = db.execute(
                        text("""
                            SELECT connection_id, pipeline_id, metadata, connected_at, last_activity
                            FROM websocket_connections 
                            ORDER BY connected_at DESC
                        """)
                    ).fetchall()
                
                connections = []
                for row in results:
                    connections.append({
                        "connection_id": row[0],
                        "pipeline_id": row[1],
                        "metadata": json.loads(row[2]) if row[2] else {},
                        "connected_at": row[3],
                        "last_activity": row[4]
                    })
                
                return connections
                
        except Exception as e:
            logger.error(f"Failed to get WebSocket connections: {e}")
            return []
    
    async def store_task_result(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Store task result."""
        try:
            with SessionLocal() as db:
                # Import here to avoid circular imports
                from app.models.sqlalchemy.task import TaskResult
                
                task_result = TaskResult(
                    task_id=task_id,
                    task_data=json.dumps(task_data) if isinstance(task_data, dict) else task_data
                )
                
                db.merge(task_result)
                db.commit()
                
                logger.debug(f"Task result stored: {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store task result: {e}")
            return False
    
    async def store_audit_event(self, event_data: Dict[str, Any]) -> bool:
        """Store audit event."""
        try:
            with SessionLocal() as db:
                # Import here to avoid circular imports
                from app.models.sqlalchemy.audit import AuditLog
                
                # Serialize details to JSON for database storage
                details_data = event_data.get("details")
                if isinstance(details_data, dict):
                    details_data = json.dumps(details_data, default=str)
                
                audit_event = AuditLog(
                    event_type=event_data.get("event_type"),
                    user_id=event_data.get("user_id"),
                    session_id=event_data.get("session_id"),
                    ip_address=event_data.get("ip_address"),
                    user_agent=event_data.get("user_agent"),
                    action=event_data.get("action"),
                    resource_type=event_data.get("resource_type"),
                    resource_id=event_data.get("resource_id"),
                    details=details_data,
                    severity=event_data.get("severity", "info")
                )
                
                db.add(audit_event)
                db.commit()
                
                logger.debug(f"Audit event stored: {event_data.get('event_type')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
            return False
    
    async def get_audit_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit events."""
        try:
            with SessionLocal() as db:
                # Import here to avoid circular imports
                from app.models.sqlalchemy.audit import AuditLog
                
                events = db.query(AuditLog).order_by(
                    AuditLog.timestamp.desc()
                ).limit(limit).all()
                
                events_data = []
                for event in events:
                    event_dict = event.to_dict()
                    events_data.append(event_dict)
                
                logger.debug(f"Retrieved {len(events_data)} audit events")
                return events_data
                
        except Exception as e:
            logger.error(f"Failed to get audit events: {e}")
            return []
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task execution results."""
        try:
            with SessionLocal() as db:
                result = db.execute(
                    text("SELECT task_data FROM task_results WHERE task_id = :task_id"),
                    {"task_id": task_id}
                ).fetchone()
                
                if result:
                    return json.loads(result[0])
                return None
                
        except Exception as e:
            logger.error(f"Failed to get task result for {task_id}: {e}")
            return None
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Clean up old data to prevent database bloat."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with SessionLocal() as db:
                # Clean up old WebSocket connections
                db.execute(
                    text("DELETE FROM websocket_connections WHERE last_activity < :cutoff_date"),
                    {"cutoff_date": cutoff_date}
                )
                
                # Clean up old task results (keep successful tasks longer)
                task_cutoff = datetime.utcnow() - timedelta(days=days_to_keep * 3)
                db.execute(
                    text("""
                        DELETE FROM task_results 
                        WHERE created_at < :task_cutoff 
                        AND json_extract(task_data, '$.status') != 'completed'
                    """),
                    {"task_cutoff": task_cutoff}
                )
                
                db.commit()
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    async def backup_data(self, backup_path: str) -> bool:
        """Create a backup of critical data."""
        try:
            import shutil
            
            # For SQLite, just copy the database file
            if settings.DATABASE_URL.startswith("sqlite"):
                db_path = settings.DATABASE_URL.replace("sqlite:///", "")
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backed up to {backup_path}")
                return True
            else:
                # For PostgreSQL, you'd use pg_dump or similar
                logger.warning("Backup not implemented for PostgreSQL yet")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup data: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                
                # Get table counts
                with SessionLocal() as db:
                    investigation_count = db.execute(text("SELECT COUNT(*) FROM investigation_states")).scalar()
                    workflow_count = db.execute(text("SELECT COUNT(*) FROM workflow_states")).scalar()
                    task_count = db.execute(text("SELECT COUNT(*) FROM task_results")).scalar()
                    connection_count = db.execute(text("SELECT COUNT(*) FROM websocket_connections")).scalar()
                
                return {
                    "status": "healthy",
                    "database_connected": True,
                    "tables": {
                        "investigation_states": investigation_count,
                        "workflow_states": workflow_count,
                        "task_results": task_count,
                        "websocket_connections": connection_count
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "database_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global instance
db_persistence = DatabasePersistenceService()