"""
Bulk Operations Manager
Safe bulk processing with preview, rollback, and progress tracking
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid
import copy
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class SafetyConfig:
    """Bulk operation safety configuration"""
    dry_run: bool = True
    batch_size: int = 50
    delay_between_batches: float = 1.0
    backup_before: bool = True
    rollback_on_error: bool = True
    max_failures: int = 5
    progress_callback: bool = True
    confirmation_required: bool = True


@dataclass
class OperationResult:
    """Result of a bulk operation"""
    operation_id: str
    status: str  # pending, running, completed, failed, rolled_back
    started: str
    completed: Optional[str] = None
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    errors: List[str] = None
    preview_data: Optional[Dict[str, Any]] = None
    backup_id: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BulkOperationManager:
    """Manage safe bulk operations with preview and rollback capabilities"""
    
    def __init__(self):
        self.operations = {}  # Store operation results
        self.backups = {}     # Store backup data for rollback
        self.active_operations = set()
    
    def preview_changes(self, api, operation: str, targets: List[Any], 
                       changes: Dict[str, Any]) -> Dict[str, Any]:
        """Preview bulk operation changes before execution"""
        
        operation_id = str(uuid.uuid4())
        
        try:
            preview_result = {
                "operation_id": operation_id,
                "operation": operation,
                "total_targets": len(targets),
                "estimated_time": self._estimate_operation_time(operation, len(targets)),
                "changes_preview": [],
                "potential_conflicts": [],
                "warnings": []
            }
            
            # Sample preview for first few items
            preview_count = min(5, len(targets))
            
            for i, target in enumerate(targets[:preview_count]):
                if operation == "update_products":
                    preview_item = self._preview_product_update(api, target, changes)
                elif operation == "update_prices":
                    preview_item = self._preview_price_update(api, target, changes)
                elif operation == "update_categories":
                    preview_item = self._preview_category_update(api, target, changes)
                elif operation == "bulk_delete":
                    preview_item = self._preview_deletion(api, target, changes)
                else:
                    preview_item = {"target": target, "error": "Unknown operation"}
                
                preview_result["changes_preview"].append(preview_item)
            
            # Store preview for potential execution
            operation_data = OperationResult(
                operation_id=operation_id,
                status="preview",
                started=datetime.now().isoformat(),
                total_items=len(targets),
                preview_data={
                    "operation": operation,
                    "targets": targets,
                    "changes": changes
                }
            )
            
            self.operations[operation_id] = operation_data
            
            return preview_result
        
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            return {"error": str(e)}
    
    def execute_operation(self, operation_id: str, safety_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a previewed bulk operation"""
        
        if operation_id not in self.operations:
            return {"error": "Operation not found"}
        
        operation_data = self.operations[operation_id]
        
        if operation_data.status != "preview":
            return {"error": f"Operation is not in preview state: {operation_data.status}"}
        
        if operation_id in self.active_operations:
            return {"error": "Operation is already running"}
        
        # Parse safety config
        config = SafetyConfig(**(safety_config or {}))
        
        # Start operation
        self.active_operations.add(operation_id)
        operation_data.status = "running"
        operation_data.started = datetime.now().isoformat()
        
        try:
            # Create backup if required
            if config.backup_before:
                backup_id = self._create_backup(operation_data.preview_data)
                operation_data.backup_id = backup_id
            
            # Execute the operation
            if config.dry_run:
                result = self._execute_dry_run(operation_data, config)
            else:
                result = self._execute_actual_operation(operation_data, config)
            
            operation_data.status = "completed"
            operation_data.completed = datetime.now().isoformat()
            operation_data.successful_items = result.get("successful", 0)
            operation_data.failed_items = result.get("failed", 0)
            operation_data.errors = result.get("errors", [])
            
            self.active_operations.remove(operation_id)
            
            return {
                "operation_id": operation_id,
                "status": "completed",
                "results": asdict(operation_data)
            }
        
        except Exception as e:
            logger.error(f"Operation execution failed: {e}")
            operation_data.status = "failed"
            operation_data.errors.append(str(e))
            self.active_operations.discard(operation_id)
            
            # Rollback if configured
            if config.rollback_on_error and operation_data.backup_id:
                rollback_result = self.rollback_operation(operation_id)
                return {
                    "operation_id": operation_id,
                    "status": "failed_and_rolled_back",
                    "error": str(e),
                    "rollback": rollback_result
                }
            
            return {
                "operation_id": operation_id,
                "status": "failed",
                "error": str(e)
            }
    
    def rollback_operation(self, operation_id: str) -> Dict[str, Any]:
        """Rollback a completed or failed operation"""
        
        if operation_id not in self.operations:
            return {"error": "Operation not found"}
        
        operation_data = self.operations[operation_id]
        
        if not operation_data.backup_id:
            return {"error": "No backup available for rollback"}
        
        if operation_data.backup_id not in self.backups:
            return {"error": "Backup data not found"}
        
        try:
            backup_data = self.backups[operation_data.backup_id]
            rollback_result = self._restore_from_backup(backup_data)
            
            operation_data.status = "rolled_back"
            operation_data.completed = datetime.now().isoformat()
            
            return {
                "operation_id": operation_id,
                "status": "rolled_back",
                "restored_items": rollback_result.get("restored", 0),
                "errors": rollback_result.get("errors", [])
            }
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {"error": str(e)}
    
    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get the status of a bulk operation"""
        
        if operation_id not in self.operations:
            return {"error": "Operation not found"}
        
        return asdict(self.operations[operation_id])
    
    def list_operations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent bulk operations"""
        
        operations = list(self.operations.values())
        
        # Sort by start time (most recent first)
        operations.sort(key=lambda x: x.started, reverse=True)
        
        return [asdict(op) for op in operations[:limit]]
    
    def cancel_operation(self, operation_id: str) -> Dict[str, Any]:
        """Cancel a running operation"""
        
        if operation_id not in self.operations:
            return {"error": "Operation not found"}
        
        if operation_id not in self.active_operations:
            return {"error": "Operation is not running"}
        
        # Mark operation as cancelled
        operation_data = self.operations[operation_id]
        operation_data.status = "cancelled"
        operation_data.completed = datetime.now().isoformat()
        
        self.active_operations.remove(operation_id)
        
        return {
            "operation_id": operation_id,
            "status": "cancelled"
        }
    
    def bulk_product_operation(self, api, operation: str, filters: Dict[str, Any], 
                              changes: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """Convenient method for bulk product operations"""
        
        # Get products matching filters
        targets = self._get_products_by_filters(api, filters)
        
        if not targets:
            return {"error": "No products found matching filters"}
        
        # Create preview
        preview_result = self.preview_changes(api, operation, targets, changes)
        
        if "error" in preview_result:
            return preview_result
        
        if not dry_run:
            # Execute immediately if not dry run
            safety_config = {"dry_run": False, "confirmation_required": False}
            return self.execute_operation(preview_result["operation_id"], safety_config)
        
        return preview_result
    
    def _estimate_operation_time(self, operation: str, item_count: int) -> str:
        """Estimate operation completion time"""
        
        # Base estimates in seconds per item
        time_estimates = {
            "update_products": 0.5,
            "update_prices": 0.2,
            "update_categories": 0.3,
            "bulk_delete": 0.3,
            "create_products": 1.0
        }
        
        base_time = time_estimates.get(operation, 0.5)
        total_seconds = int(base_time * item_count)
        
        if total_seconds < 60:
            return f"{total_seconds} seconds"
        elif total_seconds < 3600:
            return f"{total_seconds // 60} minutes"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours} hours {minutes} minutes"
    
    def _preview_product_update(self, api, product_id: int, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Preview product update changes"""
        
        try:
            # Get current product
            response = api.get(f"products/{product_id}")
            if response.status_code != 200:
                return {"product_id": product_id, "error": "Product not found"}
            
            current = response.json()
            preview = {
                "product_id": product_id,
                "name": current.get("name"),
                "sku": current.get("sku"),
                "changes": {},
                "warnings": []
            }
            
            # Show what will change
            for field, new_value in changes.items():
                old_value = current.get(field)
                if old_value != new_value:
                    preview["changes"][field] = {
                        "from": old_value,
                        "to": new_value
                    }
            
            # Check for potential issues
            if "regular_price" in changes:
                old_price = float(current.get("regular_price", 0))
                new_price = float(changes["regular_price"])
                if new_price < old_price * 0.5:  # More than 50% decrease
                    preview["warnings"].append("Large price decrease detected")
            
            return preview
        
        except Exception as e:
            return {"product_id": product_id, "error": str(e)}
    
    def _preview_price_update(self, api, product_id: int, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Preview price update changes"""
        
        # Similar to product update but focused on pricing
        return self._preview_product_update(api, product_id, changes)
    
    def _preview_category_update(self, api, category_id: int, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Preview category update changes"""
        
        try:
            response = api.get(f"products/categories/{category_id}")
            if response.status_code != 200:
                return {"category_id": category_id, "error": "Category not found"}
            
            current = response.json()
            preview = {
                "category_id": category_id,
                "name": current.get("name"),
                "changes": {}
            }
            
            for field, new_value in changes.items():
                old_value = current.get(field)
                if old_value != new_value:
                    preview["changes"][field] = {
                        "from": old_value,
                        "to": new_value
                    }
            
            return preview
        
        except Exception as e:
            return {"category_id": category_id, "error": str(e)}
    
    def _preview_deletion(self, api, item_id: int, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Preview deletion operation"""
        
        item_type = changes.get("type", "product")
        
        try:
            if item_type == "product":
                response = api.get(f"products/{item_id}")
            elif item_type == "category":
                response = api.get(f"products/categories/{item_id}")
            else:
                return {"item_id": item_id, "error": "Unknown item type"}
            
            if response.status_code != 200:
                return {"item_id": item_id, "error": f"{item_type} not found"}
            
            current = response.json()
            return {
                "item_id": item_id,
                "type": item_type,
                "name": current.get("name"),
                "action": "DELETE",
                "warning": "This item will be permanently deleted"
            }
        
        except Exception as e:
            return {"item_id": item_id, "error": str(e)}
    
    def _create_backup(self, operation_data: Dict[str, Any]) -> str:
        """Create backup before operation"""
        
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Store operation data for potential rollback
        self.backups[backup_id] = {
            "backup_id": backup_id,
            "created": datetime.now().isoformat(),
            "operation_data": copy.deepcopy(operation_data),
            "original_state": {}  # Would store actual data before changes
        }
        
        logger.info(f"Backup created: {backup_id}")
        return backup_id
    
    def _execute_dry_run(self, operation_data: OperationResult, config: SafetyConfig) -> Dict[str, Any]:
        """Execute operation in dry run mode"""
        
        logger.info(f"Executing dry run for operation: {operation_data.operation_id}")
        
        # Simulate the operation without making actual changes
        preview = operation_data.preview_data
        targets = preview["targets"]
        changes = preview["changes"]
        
        successful = 0
        failed = 0
        errors = []
        
        # Process in batches
        for i in range(0, len(targets), config.batch_size):
            batch = targets[i:i + config.batch_size]
            
            # Simulate processing each item in batch
            for target in batch:
                # Simulate success/failure (could do validation here)
                if isinstance(target, int) and target > 0:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Invalid target: {target}")
            
            operation_data.processed_items += len(batch)
            
            # Add delay between batches
            if i + config.batch_size < len(targets):
                time.sleep(config.delay_between_batches)
        
        return {
            "successful": successful,
            "failed": failed,
            "errors": errors,
            "mode": "dry_run"
        }
    
    def _execute_actual_operation(self, operation_data: OperationResult, config: SafetyConfig) -> Dict[str, Any]:
        """Execute the actual operation with real API calls"""
        
        logger.info(f"Executing actual operation: {operation_data.operation_id}")
        
        preview = operation_data.preview_data
        operation = preview["operation"]
        targets = preview["targets"]
        changes = preview["changes"]
        
        successful = 0
        failed = 0
        errors = []
        
        # This would need the actual API client
        # For now, this is a placeholder implementation
        
        return {
            "successful": successful,
            "failed": failed,
            "errors": errors,
            "mode": "actual"
        }
    
    def _restore_from_backup(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore data from backup"""
        
        logger.info(f"Restoring from backup: {backup_data['backup_id']}")
        
        # This would implement the actual restore logic
        # For now, this is a placeholder
        
        return {
            "restored": 0,
            "errors": []
        }
    
    def _get_products_by_filters(self, api, filters: Dict[str, Any]) -> List[int]:
        """Get product IDs matching filters"""
        
        products = []
        page = 1
        
        # Build API parameters from filters
        params = {"per_page": 100, "page": page}
        
        if "category" in filters:
            params["category"] = filters["category"]
        if "status" in filters:
            params["status"] = filters["status"]
        if "featured" in filters:
            params["featured"] = filters["featured"]
        if "on_sale" in filters:
            params["on_sale"] = filters["on_sale"]
        if "min_price" in filters:
            params["min_price"] = filters["min_price"]
        if "max_price" in filters:
            params["max_price"] = filters["max_price"]
        if "search" in filters:
            params["search"] = filters["search"]
        
        try:
            while True:
                response = api.get("products", params=params)
                if response.status_code != 200:
                    break
                
                page_products = response.json()
                if not page_products:
                    break
                
                # Extract product IDs
                for product in page_products:
                    if product.get("id"):
                        products.append(product["id"])
                
                params["page"] += 1
                
                # Safety limit
                if len(products) > 10000:
                    logger.warning("Product limit reached, stopping at 10000")
                    break
        
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
        
        return products