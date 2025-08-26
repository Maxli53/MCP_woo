"""
Enhanced MCP Server Core
Full WooCommerce REST API coverage with advanced features
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from mcp.server.fastmcp import FastMCP
from woocommerce import API as WooCommerceAPI

# Import enhanced tool modules
from .tools import (
    products_enhanced,
    orders_enhanced,
    customers,
    store_config,
    multi_language,
    theme_manager,
    content_manager,
    seo_marketing,
    monitoring
)

from .multi_store import MultiStoreManager
from .store_cloner import StoreCloner
from .bulk_operations import BulkOperationManager

logger = logging.getLogger(__name__)


class EnhancedMCPServer:
    """Enhanced MCP Server with full WooCommerce REST API coverage"""
    
    def __init__(self):
        self.mcp = FastMCP("WooCommerce Enterprise Suite")
        self.stores = {}
        self.active_store_id = None
        self.multi_store_manager = MultiStoreManager()
        self.store_cloner = StoreCloner()
        self.bulk_manager = BulkOperationManager()
        
        # Initialize from environment or config
        self._initialize_default_store()
        self._register_all_tools()
    
    def _initialize_default_store(self):
        """Initialize default store from environment variables"""
        store_url = os.getenv('STORE_URL')
        consumer_key = os.getenv('WOOCOMMERCE_KEY')
        consumer_secret = os.getenv('WOOCOMMERCE_SECRET')
        
        if all([store_url, consumer_key, consumer_secret]):
            self.add_store({
                'id': 'default',
                'name': 'Default Store',
                'url': store_url,
                'consumer_key': consumer_key,
                'consumer_secret': consumer_secret,
                'language': os.getenv('STORE_LANGUAGE', 'en'),
                'currency': os.getenv('STORE_CURRENCY', 'EUR'),
                'timezone': os.getenv('STORE_TIMEZONE', 'Europe/Helsinki')
            })
    
    def add_store(self, store_config: Dict[str, Any]) -> bool:
        """Add a new store connection"""
        store_id = store_config.get('id')
        
        try:
            api_client = WooCommerceAPI(
                url=store_config['url'],
                consumer_key=store_config['consumer_key'],
                consumer_secret=store_config['consumer_secret'],
                wp_api=True,
                version="wc/v3",
                timeout=30
            )
            
            # Test connection
            response = api_client.get("system_status")
            if response.status_code == 200:
                self.stores[store_id] = {
                    'config': store_config,
                    'api': api_client,
                    'connected': True,
                    'last_sync': datetime.now().isoformat()
                }
                
                if not self.active_store_id:
                    self.active_store_id = store_id
                
                logger.info(f"Successfully connected to store: {store_config['name']}")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to store {store_id}: {e}")
            return False
    
    def get_active_api(self):
        """Get the active store's API client"""
        if self.active_store_id and self.active_store_id in self.stores:
            return self.stores[self.active_store_id]['api']
        return None
    
    def switch_store(self, store_id: str) -> bool:
        """Switch active store"""
        if store_id in self.stores:
            self.active_store_id = store_id
            logger.info(f"Switched to store: {store_id}")
            return True
        return False
    
    def _register_all_tools(self):
        """Register all enhanced MCP tools"""
        
        # Enhanced Product Management
        self._register_product_tools()
        
        # Order Management
        self._register_order_tools()
        
        # Customer Management
        self._register_customer_tools()
        
        # Store Configuration
        self._register_store_config_tools()
        
        # Multi-Store Management
        self._register_multi_store_tools()
        
        # Store Cloning
        self._register_cloning_tools()
        
        # Bulk Operations
        self._register_bulk_operation_tools()
        
        # Multi-Language & Currency
        self._register_language_tools()
        
        # Theme & Branding
        self._register_theme_tools()
        
        # Content & SEO
        self._register_content_tools()
        
        # Monitoring & Health
        self._register_monitoring_tools()
    
    def _register_product_tools(self):
        """Register enhanced product management tools"""
        
        @self.mcp.tool()
        def get_product_variations(product_id: int) -> str:
            """Get all variations of a variable product"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = products_enhanced.get_product_variations(api, product_id)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_product_attributes(product_id: int, attributes: Dict[str, Any]) -> str:
            """Manage product custom fields and specifications"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = products_enhanced.manage_product_attributes(api, product_id, attributes)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def bulk_product_operations(operation: str, filters: Dict[str, Any], 
                                   changes: Dict[str, Any], dry_run: bool = True) -> str:
            """Perform bulk product operations with safety checks"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = self.bulk_manager.bulk_product_operation(
                api, operation, filters, changes, dry_run
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def import_products_from_file(file_data: str, mapping_rules: Dict[str, Any]) -> str:
            """Import products from CSV/Excel with mapping rules"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = products_enhanced.import_products(api, file_data, mapping_rules)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def export_products_to_file(filters: Dict[str, Any] = None, 
                                  format: str = "csv", columns: List[str] = None) -> str:
            """Export products with custom formatting"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = products_enhanced.export_products(api, filters, format, columns)
            return json.dumps(result, indent=2)
    
    def _register_order_tools(self):
        """Register order management tools"""
        
        @self.mcp.tool()
        def get_order_details(order_id: int) -> str:
            """Get complete order information"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = orders_enhanced.get_order_details(api, order_id)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def update_order_status(order_id: int, status: str, notes: str = "") -> str:
            """Update order status with notes"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = orders_enhanced.update_order_status(api, order_id, status, notes)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_order_items(order_id: int, items: List[Dict[str, Any]]) -> str:
            """Add, remove, or modify order items"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = orders_enhanced.manage_order_items(api, order_id, items)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def process_refund(order_id: int, amount: float, reason: str) -> str:
            """Process order refund"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = orders_enhanced.process_refund(api, order_id, amount, reason)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def get_sales_analytics(date_range: str = "last_30_days", 
                               grouping: str = "day") -> str:
            """Get sales analytics and revenue reports"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = orders_enhanced.get_sales_analytics(api, date_range, grouping)
            return json.dumps(result, indent=2)
    
    def _register_customer_tools(self):
        """Register customer management tools"""
        
        @self.mcp.tool()
        def get_customers(page: int = 1, per_page: int = 50, 
                         search: str = "", role: str = "") -> str:
            """Get customer list with search and filters"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = customers.get_customers(api, page, per_page, search, role)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def get_customer_details(customer_id: int) -> str:
            """Get full customer profile and order history"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = customers.get_customer_details(api, customer_id)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_customer_data(customer_id: int, updates: Dict[str, Any]) -> str:
            """Update customer profile information"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = customers.manage_customer_data(api, customer_id, updates)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def get_customer_analytics(filters: Dict[str, Any] = None) -> str:
            """Get customer insights and analytics"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            result = customers.get_customer_analytics(api, filters)
            return json.dumps(result, indent=2)
    
    def _register_multi_store_tools(self):
        """Register multi-store management tools"""
        
        @self.mcp.tool()
        def add_store(store_config: Dict[str, Any]) -> str:
            """Add a new store connection"""
            success = self.add_store(store_config)
            return json.dumps({"success": success, "store_id": store_config.get('id')})
        
        @self.mcp.tool()
        def list_stores() -> str:
            """List all connected stores with status"""
            stores_info = []
            for store_id, store_data in self.stores.items():
                stores_info.append({
                    'id': store_id,
                    'name': store_data['config']['name'],
                    'url': store_data['config']['url'],
                    'language': store_data['config'].get('language', 'en'),
                    'currency': store_data['config'].get('currency', 'EUR'),
                    'timezone': store_data['config'].get('timezone'),
                    'connected': store_data['connected'],
                    'last_sync': store_data['last_sync'],
                    'is_active': store_id == self.active_store_id
                })
            return json.dumps(stores_info, indent=2)
        
        @self.mcp.tool()
        def switch_active_store(store_id: str) -> str:
            """Switch to a different store"""
            success = self.switch_store(store_id)
            return json.dumps({"success": success, "active_store": self.active_store_id})
        
        @self.mcp.tool()
        def sync_stores(source_store: str, target_stores: List[str], 
                       sync_config: Dict[str, Any]) -> str:
            """Synchronize data between stores"""
            result = self.multi_store_manager.sync_stores(
                self.stores, source_store, target_stores, sync_config
            )
            return json.dumps(result, indent=2)
    
    def _register_cloning_tools(self):
        """Register store cloning tools"""
        
        @self.mcp.tool()
        def clone_store(source_store: str, target_config: Dict[str, Any], 
                       clone_options: Dict[str, Any]) -> str:
            """Clone complete store to new domain"""
            source_api = self.stores.get(source_store, {}).get('api')
            if not source_api:
                return json.dumps({"error": "Source store not found"})
            
            result = self.store_cloner.clone_store(
                source_api, target_config, clone_options
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def export_store_data(store_id: str = None, 
                            export_config: Dict[str, Any] = None) -> str:
            """Export complete store data"""
            if not store_id:
                store_id = self.active_store_id
            
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = self.store_cloner.export_store_data(api, export_config)
            return json.dumps(result, indent=2)
    
    def _register_bulk_operation_tools(self):
        """Register bulk operation tools"""
        
        @self.mcp.tool()
        def preview_bulk_changes(operation: str, targets: List[Any], 
                                changes: Dict[str, Any]) -> str:
            """Preview bulk operation changes before execution"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active store"})
            
            result = self.bulk_manager.preview_changes(api, operation, targets, changes)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def execute_bulk_operation(operation_id: str, confirmed: bool = False) -> str:
            """Execute a previewed bulk operation"""
            if not confirmed:
                return json.dumps({"error": "Operation must be confirmed"})
            
            result = self.bulk_manager.execute_operation(operation_id)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def rollback_bulk_operation(operation_id: str) -> str:
            """Rollback a bulk operation"""
            result = self.bulk_manager.rollback_operation(operation_id)
            return json.dumps(result, indent=2)
    
    def _register_language_tools(self):
        """Register multi-language and currency tools"""
        
        @self.mcp.tool()
        def get_supported_languages(store_id: str = None) -> str:
            """Get supported languages for a store"""
            if not store_id:
                store_id = self.active_store_id
            
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = multi_language.get_supported_languages(api)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_translations(store_id: str, translation_data: Dict[str, Any]) -> str:
            """Manage store translations"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = multi_language.manage_translations(api, translation_data)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_multi_currency(store_id: str, currency_config: Dict[str, Any]) -> str:
            """Configure multi-currency support"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = multi_language.manage_multi_currency(api, currency_config)
            return json.dumps(result, indent=2)
    
    def _register_theme_tools(self):
        """Register theme and branding tools"""
        
        @self.mcp.tool()
        def get_active_theme(store_id: str = None) -> str:
            """Get active theme information"""
            if not store_id:
                store_id = self.active_store_id
            
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = theme_manager.get_active_theme(api)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_store_branding(store_id: str, branding_config: Dict[str, Any]) -> str:
            """Manage store branding and visual identity"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = theme_manager.manage_store_branding(api, branding_config)
            return json.dumps(result, indent=2)
    
    def _register_content_tools(self):
        """Register content and SEO tools"""
        
        @self.mcp.tool()
        def manage_static_pages(store_id: str, page_operations: Dict[str, Any]) -> str:
            """Manage static content pages"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = content_manager.manage_static_pages(api, page_operations)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_seo_settings(store_id: str, seo_config: Dict[str, Any]) -> str:
            """Configure SEO settings"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = seo_marketing.manage_seo_settings(api, seo_config)
            return json.dumps(result, indent=2)
    
    def _register_monitoring_tools(self):
        """Register monitoring and health tools"""
        
        @self.mcp.tool()
        def monitor_store_health(store_id: str = None) -> str:
            """Monitor store health and performance"""
            if not store_id:
                store_id = self.active_store_id
            
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = monitoring.monitor_store_health(api)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_store_backups(store_id: str, backup_config: Dict[str, Any]) -> str:
            """Manage store backup configuration"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = monitoring.manage_store_backups(api, backup_config)
            return json.dumps(result, indent=2)
    
    def _register_store_config_tools(self):
        """Register store configuration tools"""
        
        @self.mcp.tool()
        def get_store_settings(store_id: str = None) -> str:
            """Get all store configuration settings"""
            if not store_id:
                store_id = self.active_store_id
            
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = store_config.get_store_settings(api)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def update_store_settings(store_id: str, section: str, 
                                settings: Dict[str, Any]) -> str:
            """Update store configuration settings"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = store_config.update_store_settings(api, section, settings)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_shipping_zones(store_id: str, action: str, 
                                zone_data: Dict[str, Any]) -> str:
            """Manage shipping zones and methods"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = store_config.manage_shipping_zones(api, action, zone_data)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_payment_gateways(store_id: str, gateway_id: str, 
                                   settings: Dict[str, Any]) -> str:
            """Configure payment gateway settings"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = store_config.manage_payment_gateways(api, gateway_id, settings)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def manage_tax_settings(store_id: str, tax_data: Dict[str, Any]) -> str:
            """Configure tax settings and rates"""
            api = self.stores.get(store_id, {}).get('api')
            if not api:
                return json.dumps({"error": "Store not found"})
            
            result = store_config.manage_tax_settings(api, tax_data)
            return json.dumps(result, indent=2)
    
    def run(self):
        """Run the enhanced MCP server"""
        self.mcp.run()


if __name__ == "__main__":
    server = EnhancedMCPServer()
    server.run()