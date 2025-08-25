"""
Backup Manager - Handles data backups and recovery
"""

import json
import asyncio
import shutil
import zipfile
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import aiofiles
import logging
import hashlib

from ..config.settings import settings

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backups for WooCommerce operations"""
    
    def __init__(self):
        self.backup_dir = settings.backup_dir
        self.max_backups = settings.backup.max_backups
        self.compress = settings.backup.compress_backups
        self.encrypt = settings.backup.encrypt_backups
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, store_id: str, operation: str, 
                           data: Any, metadata: Dict[str, Any] = None) -> str:
        """Create a backup before an operation"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{store_id}_{operation}_{timestamp}"
            backup_path = self.backup_dir / backup_id
            
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Save data
            data_file = backup_path / "data.json"
            async with aiofiles.open(data_file, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            
            # Save metadata
            meta = {
                "backup_id": backup_id,
                "store_id": store_id,
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
                "data_file": str(data_file),
                "metadata": metadata or {}
            }
            
            meta_file = backup_path / "metadata.json"
            async with aiofiles.open(meta_file, 'w') as f:
                await f.write(json.dumps(meta, indent=2))
            
            # Compress if enabled
            if self.compress:
                await self._compress_backup(backup_path, backup_id)
            
            # Clean old backups
            await self._cleanup_old_backups(store_id)
            
            logger.info(f"Created backup: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    async def _compress_backup(self, backup_path: Path, backup_id: str):
        """Compress backup directory"""
        try:
            zip_file = self.backup_dir / f"{backup_id}.zip"
            
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in backup_path.rglob('*'):
                    if file.is_file():
                        zf.write(file, file.relative_to(backup_path))
            
            # Remove uncompressed directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Compressed backup: {backup_id}.zip")
        except Exception as e:
            logger.error(f"Error compressing backup: {e}")
    
    async def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore data from a backup"""
        try:
            # Check for compressed backup
            zip_file = self.backup_dir / f"{backup_id}.zip"
            backup_path = self.backup_dir / backup_id
            
            if zip_file.exists():
                # Extract compressed backup
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    zf.extractall(backup_path)
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_id}")
            
            # Load metadata
            meta_file = backup_path / "metadata.json"
            async with aiofiles.open(meta_file, 'r') as f:
                metadata = json.loads(await f.read())
            
            # Load data
            data_file = backup_path / "data.json"
            async with aiofiles.open(data_file, 'r') as f:
                data = json.loads(await f.read())
            
            logger.info(f"Restored backup: {backup_id}")
            
            return {
                "backup_id": backup_id,
                "metadata": metadata,
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            raise
    
    async def list_backups(self, store_id: str = None, 
                          operation: str = None) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        try:
            for item in self.backup_dir.iterdir():
                if item.is_file() and item.suffix == '.zip':
                    # Compressed backup
                    backup_id = item.stem
                elif item.is_dir():
                    # Uncompressed backup
                    backup_id = item.name
                else:
                    continue
                
                # Filter by store_id or operation if provided
                if store_id and not backup_id.startswith(store_id):
                    continue
                if operation and operation not in backup_id:
                    continue
                
                # Get metadata
                try:
                    if item.suffix == '.zip':
                        # Read metadata from zip
                        with zipfile.ZipFile(item, 'r') as zf:
                            with zf.open('metadata.json') as mf:
                                metadata = json.loads(mf.read())
                    else:
                        meta_file = item / "metadata.json"
                        with open(meta_file, 'r') as f:
                            metadata = json.load(f)
                    
                    backups.append({
                        "backup_id": backup_id,
                        "store_id": metadata.get("store_id"),
                        "operation": metadata.get("operation"),
                        "timestamp": metadata.get("timestamp"),
                        "size": item.stat().st_size if item.is_file() else 
                               sum(f.stat().st_size for f in item.rglob('*') if f.is_file()),
                        "compressed": item.suffix == '.zip'
                    })
                except Exception as e:
                    logger.warning(f"Could not read metadata for {backup_id}: {e}")
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a specific backup"""
        try:
            # Check for compressed backup
            zip_file = self.backup_dir / f"{backup_id}.zip"
            if zip_file.exists():
                zip_file.unlink()
                logger.info(f"Deleted backup: {backup_id}.zip")
                return True
            
            # Check for uncompressed backup
            backup_path = self.backup_dir / backup_id
            if backup_path.exists():
                shutil.rmtree(backup_path)
                logger.info(f"Deleted backup: {backup_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False
    
    async def _cleanup_old_backups(self, store_id: str):
        """Remove old backups exceeding max_backups limit"""
        try:
            backups = await self.list_backups(store_id=store_id)
            
            if len(backups) > self.max_backups:
                # Delete oldest backups
                to_delete = backups[self.max_backups:]
                for backup in to_delete:
                    await self.delete_backup(backup['backup_id'])
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    async def rollback(self, store_id: str, operation: str) -> bool:
        """Rollback to the most recent backup for an operation"""
        try:
            # Find most recent backup
            backups = await self.list_backups(store_id=store_id, operation=operation)
            
            if not backups:
                logger.warning(f"No backup found for rollback: {store_id}/{operation}")
                return False
            
            # Restore most recent backup
            latest_backup = backups[0]
            restored_data = await self.restore_backup(latest_backup['backup_id'])
            
            # Here you would apply the restored data to the store
            # This would depend on the specific operation type
            
            logger.info(f"Rolled back to backup: {latest_backup['backup_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False
    
    async def create_full_store_backup(self, store_id: str, 
                                       store_data: Dict[str, Any]) -> str:
        """Create a complete backup of a store"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{store_id}_full_{timestamp}"
            backup_path = self.backup_dir / backup_id
            
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Save different data types in separate files
            for data_type, data in store_data.items():
                file_path = backup_path / f"{data_type}.json"
                async with aiofiles.open(file_path, 'w') as f:
                    await f.write(json.dumps(data, indent=2, default=str))
            
            # Create manifest
            manifest = {
                "backup_id": backup_id,
                "store_id": store_id,
                "backup_type": "full",
                "timestamp": datetime.now().isoformat(),
                "data_types": list(store_data.keys()),
                "checksum": self._calculate_checksum(store_data)
            }
            
            manifest_file = backup_path / "manifest.json"
            async with aiofiles.open(manifest_file, 'w') as f:
                await f.write(json.dumps(manifest, indent=2))
            
            # Compress
            if self.compress:
                await self._compress_backup(backup_path, backup_id)
            
            logger.info(f"Created full store backup: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Error creating full store backup: {e}")
            raise
    
    def _calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for data integrity"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify backup integrity"""
        try:
            # Restore backup temporarily
            restored = await self.restore_backup(backup_id)
            
            # Check if manifest exists
            if 'manifest' in restored['metadata']:
                manifest = restored['metadata']['manifest']
                
                # Verify checksum
                calculated_checksum = self._calculate_checksum(restored['data'])
                expected_checksum = manifest.get('checksum')
                
                if calculated_checksum == expected_checksum:
                    return {
                        "valid": True,
                        "message": "Backup integrity verified"
                    }
                else:
                    return {
                        "valid": False,
                        "message": "Checksum mismatch - backup may be corrupted"
                    }
            
            return {
                "valid": True,
                "message": "Backup exists but no integrity check available"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error verifying backup: {str(e)}"
            }
    
    async def schedule_automatic_backup(self, store_id: str, interval_hours: int):
        """Schedule automatic backups for a store"""
        # This would integrate with APScheduler or similar
        # Implementation depends on the scheduling system used
        pass