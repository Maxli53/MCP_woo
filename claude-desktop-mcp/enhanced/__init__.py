"""
Enhanced MCP WooCommerce Suite
Enterprise-level multi-store management with full REST API coverage
"""

__version__ = "2.0.0"
__author__ = "MCP WooCommerce Suite Team"

from .core import EnhancedMCPServer
from .multi_store import MultiStoreManager
from .store_cloner import StoreCloner
from .bulk_operations import BulkOperationManager

__all__ = [
    'EnhancedMCPServer',
    'MultiStoreManager', 
    'StoreCloner',
    'BulkOperationManager'
]