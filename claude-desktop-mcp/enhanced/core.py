"""
Enhanced MCP Server Core
Full WooCommerce REST API coverage with advanced features
"""

import os
import sys
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from mcp.server.fastmcp import FastMCP
from woocommerce import API as WooCommerceAPI

# Import enhanced tool modules
try:
    # Try relative imports first (when run as module)
    from .tools import (
        products_enhanced,
        orders_enhanced,
        customers,
        store_config,
        multi_language,
        theme_manager,
        content_manager,
        seo_marketing,
        monitoring,
        document_manager,
        database_integration,
        excel_processor,
        data_consolidator,
        ai_descriptions,
        vps_manager  # Real VPS management
    )
    from .multi_store import MultiStoreManager
    from .store_cloner import StoreCloner
    from .bulk_operations import BulkOperationManager
except ImportError:
    # Fall back to absolute imports (when run directly)
    from tools import (
        products_enhanced,
        orders_enhanced,
        customers,
        store_config,
        multi_language,
        theme_manager,
        content_manager,
        seo_marketing,
        monitoring,
        document_manager,
        database_integration,
        excel_processor,
        data_consolidator,
        ai_descriptions,
        vps_manager  # Real VPS management
    )
    from multi_store import MultiStoreManager
    from store_cloner import StoreCloner
    from bulk_operations import BulkOperationManager

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
        
        # VPS Management & Deployment
        self._register_vps_tools()
        
        # Document Management & Product Pipeline
        self._register_document_management_tools()
    
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
    
    def _register_vps_tools(self):
        """Register VPS management and deployment tools"""
        
        @self.mcp.tool()
        def test_vps_environment() -> str:
            """Test VPS environment configuration and diagnose connection issues"""
            import os
            import logging
            
            # Setup logging to capture debug info
            logging.basicConfig(level=logging.INFO)
            
            env_info = {
                "environment_variables": {
                    "DEFAULT_VPS_IP": os.getenv('DEFAULT_VPS_IP'),
                    "VPS_SSH_PORT": os.getenv('VPS_SSH_PORT'),
                    "VPS_SSH_KEY_PATH": os.getenv('VPS_SSH_KEY_PATH'),
                    "VPS_SSH_PASSWORD": "***" if os.getenv('VPS_SSH_PASSWORD') else None
                },
                "path_checks": {
                    "ssh_key_exists": os.path.exists(os.getenv('VPS_SSH_KEY_PATH', '')),
                    "ssh_key_path": os.getenv('VPS_SSH_KEY_PATH', 'NOT_SET'),
                    "working_directory": os.getcwd(),
                    "python_executable": sys.executable
                },
                "test_connection": None
            }
            
            # Try a test connection
            try:
                from tools import vps_manager
                test_result = vps_manager.get_vps_resources()
                env_info["test_connection"] = {
                    "success": test_result.get("success", False),
                    "hostname": test_result.get("hostname") if test_result.get("success") else None,
                    "error": test_result.get("error") if not test_result.get("success") else None
                }
            except Exception as e:
                env_info["test_connection"] = {"error": str(e)}
            
            return json.dumps(env_info, indent=2)
        
        @self.mcp.tool()
        def provision_ubuntu_vps(ip_address: str = None, ssh_key_path: str = None, 
                                ssh_password: str = None, ubuntu_version: str = "22.04",
                                hostname: str = None, php_version: str = "8.1") -> str:
            """Provision Ubuntu VPS with LEMP stack for WooCommerce hosting
            
            Args:
                ip_address: VPS IP address
                ssh_key_path: Path to SSH private key
                ssh_password: SSH password (if not using key)
                ubuntu_version: Ubuntu version (22.04 or 24.04)
                hostname: Server hostname
                php_version: PHP version to install
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.provision_ubuntu_vps(
                ip_address=ip_address,
                ssh_key_path=ssh_key_path,
                ssh_password=ssh_password,
                ubuntu_version=ubuntu_version,
                hostname=hostname,
                php_version=php_version
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def deploy_store_to_vps(vps_ip: str = None, domain: str = None, store_name: str = None,
                               admin_email: str = None, admin_user: str = "admin",
                               admin_password: str = None, ssl_enabled: bool = True,
                               php_version: str = "8.1", ssh_key_path: str = None) -> str:
            """Deploy new WooCommerce store to VPS
            
            Args:
                vps_ip: VPS IP address
                domain: Store domain name
                store_name: Store name/title
                admin_email: Administrator email
                admin_user: Admin username (default: admin)
                admin_password: Admin password (generated if not provided)
                ssl_enabled: Enable SSL certificate
                php_version: PHP version
                ssh_key_path: SSH key path
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.deploy_store_to_vps(
                vps_ip=vps_ip,
                domain=domain,
                store_name=store_name,
                admin_email=admin_email,
                admin_user=admin_user,
                admin_password=admin_password,
                ssl_enabled=ssl_enabled,
                php_version=php_version,
                ssh_key_path=ssh_key_path
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def list_stores_on_vps(vps_ip: str = None, ssh_key_path: str = None) -> str:
            """List all WooCommerce stores deployed on VPS
            
            Args:
                vps_ip: VPS IP address
                ssh_key_path: SSH key path
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.list_stores_on_vps(
                vps_ip=vps_ip,
                ssh_key_path=ssh_key_path
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def get_vps_resources(vps_ip: str = None, ssh_key_path: str = None) -> str:
            """Get VPS resource usage and system information
            
            Args:
                vps_ip: VPS IP address
                ssh_key_path: SSH key path
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.get_vps_resources(
                vps_ip=vps_ip,
                ssh_key_path=ssh_key_path
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool() 
        def monitor_store_on_vps(vps_ip: str = None, domain: str = None, ssh_key_path: str = None) -> str:
            """Monitor specific store resource usage on VPS
            
            Args:
                vps_ip: VPS IP address
                domain: Store domain to monitor
                ssh_key_path: SSH key path
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.monitor_store_on_vps(
                vps_ip=vps_ip,
                domain=domain,
                ssh_key_path=ssh_key_path
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def backup_vps_store(vps_ip: str = None, domain: str = None, include_database: bool = True,
                           ssh_key_path: str = None) -> str:
            """Create backup of WooCommerce store on VPS
            
            Args:
                vps_ip: VPS IP address
                domain: Store domain to backup
                include_database: Include database in backup
                ssh_key_path: SSH key path
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.backup_vps_store(
                vps_ip=vps_ip,
                domain=domain,
                include_database=include_database,
                ssh_key_path=ssh_key_path
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def execute_vps_command(vps_ip: str = None, command: str = None, ssh_key_path: str = None) -> str:
            """Execute command on VPS (use with caution)
            
            Args:
                vps_ip: VPS IP address
                command: Command to execute
                ssh_key_path: SSH key path
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.execute_vps_command(
                vps_ip=vps_ip,
                command=command,
                ssh_key_path=ssh_key_path
            )
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def optimize_vps_performance(vps_ip: str = None, ssh_key_path: str = None) -> str:
            """Optimize VPS performance for WooCommerce stores
            
            Args:
                vps_ip: VPS IP address
                ssh_key_path: SSH key path
            """
            # Use REAL VPS manager for actual SSH operations
            result = vps_manager.optimize_vps_performance(
                vps_ip=vps_ip,
                ssh_key_path=ssh_key_path
            )
            return json.dumps(result, indent=2)
    
    def _register_document_management_tools(self):
        """Register document management and product data pipeline tools"""
        
        @self.mcp.tool()
        def store_document(file_data: str, category: str = "auto", metadata: Dict[str, Any] = None) -> str:
            """Store uploaded documents in appropriate repository folders
            
            Args:
                file_data: Base64 encoded file content or file path
                category: Document category (auto-detect if not specified)
                metadata: Optional document metadata
            """
            result = document_manager.store_document(file_data, category, metadata)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def process_catalogue(document_id: str) -> str:
            """Extract product data from uploaded catalogues by SKU
            
            Args:
                document_id: ID of stored catalogue document
            """
            result = document_manager.process_catalogue(document_id)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def review_products(sku_list: List[str], review_mode: str = "individual") -> str:
            """Simple review interface for manual validation
            
            Args:
                sku_list: List of SKUs to review
                review_mode: Review mode (individual, batch)
            """
            result = document_manager.review_products(sku_list, review_mode)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def query_database(query_type: str, parameters: Dict[str, Any] = None) -> str:
            """Query the fragmented SQL database for product data
            
            Args:
                query_type: Type of query (get_product, list_skus, incomplete_products, ai_template, custom)
                parameters: Query parameters (sku, template_type, language, etc.)
            """
            result = database_integration.query_database(query_type, parameters or {})
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def import_excel_data(file_path: str, sheet_name: str = None, sku_column: str = "auto") -> str:
            """Import and process pricing Excel files with automatic SKU detection
            
            Args:
                file_path: Path to Excel file or document ID from stored documents
                sheet_name: Specific sheet name to process (optional)
                sku_column: SKU column name or "auto" for automatic detection
            """
            result = excel_processor.import_excel_data(file_path, sheet_name, sku_column)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def consolidate_product_data(sku: str, sources: List[str] = None) -> str:
            """Consolidate product data from multiple sources (database, Excel, catalogues)
            
            Args:
                sku: Product SKU to consolidate data for
                sources: List of data sources to include ["database", "excel", "catalogue", "all"]
            """
            result = data_consolidator.consolidate_product_data(sku, sources)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def generate_descriptions(sku_list: List[str], template_type: str = "auto", language: str = "en") -> str:
            """Generate AI-powered product descriptions using database templates
            
            Args:
                sku_list: List of SKUs to generate descriptions for
                template_type: Template type to use ("auto", "technical", "marketing", "basic")
                language: Language code for descriptions ("en", "no", "se", "dk")
            """
            result = ai_descriptions.generate_descriptions(sku_list, template_type, language)
            return json.dumps(result, indent=2)
        
        # Additional helper tools
        @self.mcp.tool()
        def get_excel_sheet_names(file_path: str) -> str:
            """Get available sheet names from Excel file"""
            result = excel_processor.get_excel_sheet_names(file_path)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def preview_excel_structure(file_path: str, sheet_name: str = None, rows: int = 5) -> str:
            """Preview Excel file structure and data"""
            result = excel_processor.preview_excel_structure(file_path, sheet_name, rows)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def batch_consolidate_products(sku_list: List[str], sources: List[str] = None) -> str:
            """Consolidate data for multiple SKUs in batch"""
            result = data_consolidator.batch_consolidate_products(sku_list, sources)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def batch_review_descriptions(sku_list: List[str], action: str = "preview") -> str:
            """Review and manage generated descriptions in batch"""
            result = ai_descriptions.batch_review_descriptions(sku_list, action)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def list_available_templates() -> str:
            """List all available description templates"""
            result = ai_descriptions.list_available_templates()
            return json.dumps(result, indent=2)
        
        # Enhanced Avito Description Tools
        @self.mcp.tool()
        def generate_avito_xml_description(sku: str) -> str:
            """Generate complete Avito XML description using existing database template for a single SKU
            
            Args:
                sku: Product SKU to generate Avito XML description for
            """
            avito_template = ai_descriptions.get_avito_template("avito", "en")
            if avito_template and not avito_template.get("error"):
                result = ai_descriptions.generate_avito_xml_description(sku, avito_template, {})
            else:
                result = avito_template or {"error": "No Avito template available"}
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def regenerate_all_avito_descriptions(sku_filter: List[str] = None) -> str:
            """Regenerate all Avito descriptions for SKUs in price lists using all available document repository data
            
            This is the natural language function the user requested:
            "Dear Claude, regenerate all product descriptions for SKUs in price lists. Utilize all available data in the document repository."
            
            Args:
                sku_filter: Optional list of specific SKUs to process. If None, processes all SKUs with price data.
            """
            result = ai_descriptions.regenerate_all_avito_descriptions(sku_filter)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool() 
        def get_avito_template_info() -> str:
            """Get information about available Avito templates in the database"""
            avito_template = ai_descriptions.get_avito_template("avito", "en")
            if avito_template and not avito_template.get("error"):
                template_info = {
                    "template_found": True,
                    "template_name": avito_template.get("template_name"),
                    "template_version": avito_template.get("template_version"),
                    "template_purpose": avito_template.get("template_purpose"),
                    "has_gpt_integration": bool(avito_template.get("gpt_system_prompt")),
                    "has_xml_template": bool(avito_template.get("complete_xml_template")),
                    "available_sections": list(avito_template.get("sections", {}).keys()),
                    "template_source": avito_template.get("template_info", {}).get("source")
                }
            else:
                template_info = {
                    "template_found": False,
                    "error": avito_template.get("error") if avito_template else "No template data available"
                }
            return json.dumps(template_info, indent=2)
        
        # NEW: Business Intelligence & Data Sync Tools
        @self.mcp.tool()
        def execute_sql_query(sql: str) -> str:
            """Execute custom SQL query on business database (SELECT only for safety)"""
            result = database_integration.query_database("execute_sql", {"sql": sql})
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def sync_database_from_documents() -> str:
            """Sync database with latest document data (price lists, Excel, catalogues)"""
            result = database_integration.query_database("sync_from_documents", {})
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def update_product_data(sku: str, data: Dict[str, Any]) -> str:
            """Update product data in database with validation"""
            result = database_integration.query_database("update_product_data", {"sku": sku, "data": data})
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def detect_data_changes() -> str:
            """Detect changes between documents and database"""
            result = database_integration.query_database("detect_data_changes", {})
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def backup_database() -> str:
            """Create safe backup of business database"""
            result = database_integration.query_database("backup_database", {})
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def get_sync_status() -> str:
            """Get current sync status between documents and database"""
            result = database_integration.query_database("get_sync_status", {})
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def sync_to_woocommerce(sku_list: List[str] = None, update_type: str = "all") -> str:
            """Sync product data to WooCommerce store
            
            Args:
                sku_list: List of SKUs to sync (all if None)
                update_type: Type of update (all, pricing, descriptions, inventory)
            """
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active WooCommerce store"})
            
            result = self._sync_to_woocommerce_internal(api, sku_list, update_type)
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def get_woocommerce_sync_status() -> str:
            """Check sync status between database and WooCommerce"""
            api = self.get_active_api()
            if not api:
                return json.dumps({"error": "No active WooCommerce store"})
            
            result = self._get_woocommerce_sync_status_internal(api)
            return json.dumps(result, indent=2)
        
        # NEW: Database Schema Management Tools
        @self.mcp.tool()
        def alter_database_schema(operation: str, table: str, changes: Dict[str, Any]) -> str:
            """Safely modify database schema with automatic backup
            
            Args:
                operation: Schema operation (ADD_COLUMN, RENAME_COLUMN)
                table: Target table name
                changes: Dictionary with operation parameters
            """
            result = database_integration.query_database("alter_schema", {
                "operation": operation,
                "table": table, 
                "changes": changes
            })
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def create_new_table(table_name: str, schema: Dict[str, Any]) -> str:
            """Create new database table with validation
            
            Args:
                table_name: Name for the new table
                schema: Dictionary mapping column names to data types
            """
            result = database_integration.query_database("create_table", {
                "table_name": table_name,
                "schema": schema
            })
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def add_database_column(table: str, column_name: str, data_type: str) -> str:
            """Add new column to existing table
            
            Args:
                table: Target table name
                column_name: New column name
                data_type: SQL data type (TEXT, INTEGER, REAL, BLOB)
            """
            result = database_integration.query_database("add_column", {
                "table": table,
                "column_name": column_name,
                "data_type": data_type
            })
            return json.dumps(result, indent=2)
        
        @self.mcp.tool()
        def add_database_index(table: str, columns: List[str], index_name: str = None) -> str:
            """Add database index for performance optimization
            
            Args:
                table: Target table name
                columns: List of columns to index
                index_name: Optional custom index name
            """
            result = database_integration.query_database("add_index", {
                "table": table,
                "columns": columns,
                "index_name": index_name
            })
            return json.dumps(result, indent=2)
    
    def _sync_to_woocommerce_internal(self, api, sku_list: List[str] = None, update_type: str = "all") -> Dict[str, Any]:
        """Internal WooCommerce sync implementation"""
        
        try:
            from datetime import datetime
            
            # Get products to sync
            if sku_list:
                products_to_sync = sku_list
            else:
                # Get all SKUs from database
                db_result = database_integration.query_database("list_skus", {})
                if "error" in db_result:
                    return {"error": "Could not retrieve SKUs from database"}
                products_to_sync = db_result.get("results", [])[:20]  # Limit to 20 for safety
            
            sync_results = {
                "requested_skus": len(products_to_sync),
                "processed": 0,
                "updated": 0,
                "created": 0,
                "errors": [],
                "details": []
            }
            
            for sku in products_to_sync:
                try:
                    # Get consolidated product data
                    product_data = data_consolidator.consolidate_product_data(sku)
                    if "error" in product_data:
                        sync_results["errors"].append(f"{sku}: {product_data['error']}")
                        continue
                    
                    # Check if product exists in WooCommerce (by SKU)
                    wc_products = api.get("products", params={"sku": sku})
                    
                    consolidated_data = product_data.get("consolidated_data", {})
                    
                    # Prepare WooCommerce product data
                    wc_product_data = {
                        "sku": sku,
                        "name": consolidated_data.get("name", f"Product {sku}"),
                        "regular_price": str(consolidated_data.get("price", 0)),
                        "description": consolidated_data.get("description", ""),
                        "short_description": consolidated_data.get("short_description", ""),
                        "manage_stock": True,
                        "stock_quantity": consolidated_data.get("stock_quantity", 0),
                        "status": "publish"
                    }
                    
                    # Update or create product
                    if wc_products.json() and len(wc_products.json()) > 0:
                        # Update existing product
                        wc_product_id = wc_products.json()[0]["id"]
                        response = api.put(f"products/{wc_product_id}", wc_product_data)
                        if response.status_code == 200:
                            sync_results["updated"] += 1
                            sync_results["details"].append(f"{sku}: Updated WC product #{wc_product_id}")
                        else:
                            sync_results["errors"].append(f"{sku}: Update failed - {response.status_code}")
                    else:
                        # Create new product
                        response = api.post("products", wc_product_data)
                        if response.status_code == 201:
                            new_id = response.json().get("id")
                            sync_results["created"] += 1
                            sync_results["details"].append(f"{sku}: Created new WC product #{new_id}")
                        else:
                            sync_results["errors"].append(f"{sku}: Creation failed - {response.status_code}")
                    
                    sync_results["processed"] += 1
                    
                except Exception as e:
                    sync_results["errors"].append(f"{sku}: Exception - {str(e)}")
            
            return {
                "success": True,
                "sync_results": sync_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"WooCommerce sync error: {e}")
            return {"error": str(e)}
    
    def _get_woocommerce_sync_status_internal(self, api) -> Dict[str, Any]:
        """Internal WooCommerce sync status check"""
        
        try:
            from datetime import datetime
            
            # Get database product count
            db_result = database_integration.query_database("list_skus", {})
            db_count = len(db_result.get("results", [])) if "error" not in db_result else 0
            
            # Get WooCommerce product count
            wc_response = api.get("products", params={"per_page": 1})
            if wc_response.status_code == 200:
                wc_total = int(wc_response.headers.get("X-WP-Total", 0))
                
                # Sample check - get a few products with SKUs
                wc_with_skus = api.get("products", params={"per_page": 10})
                if wc_with_skus.status_code == 200:
                    wc_products = wc_with_skus.json()
                    products_with_skus = [p for p in wc_products if p.get("sku")]
                    
                    sync_status = {
                        "database_products": db_count,
                        "woocommerce_products": wc_total,
                        "wc_products_with_skus": len(products_with_skus),
                        "sync_ratio": f"{len(products_with_skus)}/{db_count}",
                        "recommendations": []
                    }
                    
                    if len(products_with_skus) < db_count * 0.8:
                        sync_status["recommendations"].append("Many database products may not be synced to WooCommerce")
                    
                    if wc_total > db_count * 1.5:
                        sync_status["recommendations"].append("WooCommerce has more products than database - manual review needed")
                    
                    return {
                        "success": True,
                        "sync_status": sync_status,
                        "timestamp": datetime.now().isoformat()
                    }
            
            return {"error": "Could not retrieve WooCommerce product data"}
            
        except Exception as e:
            logger.error(f"WooCommerce sync status error: {e}")
            return {"error": str(e)}
    
    def run(self):
        """Run the enhanced MCP server"""
        self.mcp.run()


if __name__ == "__main__":
    server = EnhancedMCPServer()
    server.run()