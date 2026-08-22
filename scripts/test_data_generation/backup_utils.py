"""
Backup utility functions for YouTrack test data.
"""
import logging
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from youtrack_api import YouTrackAPIClient
from config import BACKUP_DIR, BACKUP_NAME_PREFIX

logger = logging.getLogger(__name__)


def create_backup_with_monitor(
    api: YouTrackAPIClient,
    max_wait_minutes: int = 60,
    poll_interval_seconds: int = 10
) -> bool:
    """
    Create a database backup and monitor completion.
    
    Args:
        api: YouTrackAPIClient instance
        max_wait_minutes: Maximum time to wait for backup to complete
        poll_interval_seconds: How often to check backup status
        
    Returns:
        True if backup completed successfully, False otherwise
    """
    try:
        logger.info("Initiating database backup...")
        backup_result = api.create_backup()
        logger.info(f"Backup initiated: {backup_result}")
        
        # Monitor backup progress
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                status = api.get_backup_status()
                logger.debug(f"Backup status: {status}")
                
                # Check if backup is complete
                if status.get('isRunning') is False:
                    logger.info("Database backup completed successfully")
                    return True
                    
            except Exception as e:
                logger.debug(f"Status check failed (will retry): {e}")
            
            # Wait before next check
            time.sleep(poll_interval_seconds)
        
        logger.warning(f"Backup did not complete within {max_wait_minutes} minutes")
        return False
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False


def generate_backup_filename() -> str:
    """Generate backup filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{BACKUP_NAME_PREFIX}_{timestamp}.backup"


def save_backup_metadata(filename: str, metadata: dict) -> Path:
    """Save backup metadata to file."""
    backup_path = BACKUP_DIR / filename
    metadata_path = backup_path.with_suffix('.json')
    
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    logger.info(f"Backup metadata saved to {metadata_path}")
    return metadata_path


def list_backups() -> list:
    """List all available backups."""
    backups = list(BACKUP_DIR.glob(f"{BACKUP_NAME_PREFIX}*.backup"))
    return sorted(backups, reverse=True)


def cleanup_old_backups(keep_count: int = 3) -> int:
    """
    Delete old backups keeping only most recent ones.
    
    Args:
        keep_count: Number of recent backups to keep
        
    Returns:
        Number of backups deleted
    """
    backups = list_backups()
    deleted = 0
    
    for backup in backups[keep_count:]:
        try:
            backup.unlink()
            # Also delete metadata file
            metadata = backup.with_suffix('.json')
            if metadata.exists():
                metadata.unlink()
            deleted += 1
            logger.info(f"Deleted old backup: {backup.name}")
        except Exception as e:
            logger.error(f"Failed to delete backup {backup.name}: {e}")
    
    return deleted
