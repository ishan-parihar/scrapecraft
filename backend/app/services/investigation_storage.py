import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..models.osint import Investigation

logger = logging.getLogger(__name__)

# File-based storage for investigations
class InvestigationStorage:
    """File-based storage for investigations when database is not available."""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            backend_dir = Path(__file__).parent.parent.parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(exist_ok=True)
            storage_path = data_dir / "investigations.json"
        
        self.storage_path = Path(storage_path)
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Ensure the storage file and directory exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.storage_path.exists():
            initial_data = {
                "investigations": [],
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
            }
            with open(self.storage_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
            logger.info(f"Created investigation storage at {self.storage_path}")
    
    def load_investigations(self) -> List[Investigation]:
        """Load all investigations from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
            investigations = []
            for inv_data in data.get("investigations", []):
                try:
                    investigation = Investigation(**inv_data)
                    investigations.append(investigation)
                except Exception as e:
                    logger.error(f"Failed to load investigation {inv_data.get('id', 'unknown')}: {e}")
            
            return investigations
        except Exception as e:
            logger.error(f"Failed to load investigations: {e}")
            return []
    
    def save_investigation(self, investigation: Investigation) -> bool:
        """Save a single investigation to storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Update or add investigation
            investigations = data.get("investigations", [])
            investigation_dict = investigation.dict()
            
            # Find and update existing investigation or add new one
            for i, inv in enumerate(investigations):
                if inv.get("id") == investigation.id:
                    investigations[i] = investigation_dict
                    break
            else:
                investigations.append(investigation_dict)
            
            data["investigations"] = investigations
            data["metadata"]["updated_at"] = datetime.utcnow().isoformat()
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save investigation {investigation.id}: {e}")
            return False
    
    def delete_investigation(self, investigation_id: str) -> bool:
        """Delete an investigation from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            investigations = data.get("investigations", [])
            investigations = [inv for inv in investigations if inv.get("id") != investigation_id]
            
            data["investigations"] = investigations
            data["metadata"]["updated_at"] = datetime.utcnow().isoformat()
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete investigation {investigation_id}: {e}")
            return False
    
    def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        """Get a specific investigation by ID."""
        investigations = self.load_investigations()
        for investigation in investigations:
            if investigation.id == investigation_id:
                return investigation
        return None

# Global storage instance
_investigation_storage = None

def get_investigation_storage() -> InvestigationStorage:
    """Get the global investigation storage instance."""
    global _investigation_storage
    if _investigation_storage is None:
        _investigation_storage = InvestigationStorage()
    return _investigation_storage

# Convenience functions
def load_investigations() -> List[Investigation]:
    """Load all investigations from storage."""
    storage = get_investigation_storage()
    return storage.load_investigations()

def save_investigation(investigation: Investigation) -> bool:
    """Save an investigation to storage."""
    storage = get_investigation_storage()
    return storage.save_investigation(investigation)

def delete_investigation(investigation_id: str) -> bool:
    """Delete an investigation from storage."""
    storage = get_investigation_storage()
    return storage.delete_investigation(investigation_id)

def get_investigation(investigation_id: str) -> Optional[Investigation]:
    """Get a specific investigation by ID."""
    storage = get_investigation_storage()
    return storage.get_investigation(investigation_id)