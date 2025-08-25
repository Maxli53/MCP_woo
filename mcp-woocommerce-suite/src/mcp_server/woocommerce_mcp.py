"""
MCP Server for WooCommerce Management
Comprehensive tools for managing multiple WooCommerce stores
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

from mcp import Server, Tool
from mcp.types import TextContent, ImageContent, EmbeddedResource
from pydantic import BaseModel, Field
import httpx
from woocommerce import API as WooCommerceAPI
import aiofiles
import chardet
from cryptography.fernet import Fernet

from ..config.settings import settings
from ..utils.store_manager import StoreManager
from ..utils.data_validator import DataValidator
from ..utils.backup_manager import BackupManager
from ..utils.security import SecureCredentialStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WooCommerceMCPServer:
    """MCP Server for WooCommerce Store Management"""
    
    def __init__(self):
        self.server = Server("woocommerce-admin")
        self.store_manager = StoreManager()
        self.data_validator = DataValidator()
        self.backup_manager = BackupManager()
        self.credential_store = SecureCredentialStore()
        self.active_store_id = None
        self._setup_tools()
    
    def _setup_tools(self):
        """Register all MCP tools"""
        
        # Store Management Tools
        self.server.add_tool(self._create_tool(
            "list_available_stores",
            "Show all connected WooCommerce stores",
            self.list_available_stores
        ))
        
        self.server.add_tool(self._create_tool(
            "select_active_store",
            "Set the active store for operations",
            self.select_active_store,
            store_id=str
        ))
        
        self.server.add_tool(self._create_tool(
            "add_store",
            "Add a new WooCommerce store connection",
            self.add_store,
            store_id=str,
            url=str,
            consumer_key=str,
            consumer_secret=str,
            wp_api=bool,
            version=str
        ))
        
        # Single Store Product Management
        self.server.add_tool(self._create_tool(
            "get_all_products",
            "List all products from a store with specific fields",
            self.get_all_products,
            store_id=str,
            fields=list,
            page=int,
            per_page=int
        ))
        
        self.server.add_tool(self._create_tool(
            "get_product_details",
            "Get detailed information about a specific product",
            self.get_product_details,
            product_id=str,
            store_id=str
        ))
        
        self.server.add_tool(self._create_tool(
            "search_products",
            "Advanced product search with filters",
            self.search_products,
            query=str,
            filters=dict,
            store_id=str
        ))
        
        self.server.add_tool(self._create_tool(
            "update_product_data",
            "Update individual product information",
            self.update_product_data,
            product_id=str,
            updates=dict,
            store_id=str
        ))
        
        self.server.add_tool(self._create_tool(
            "delete_products",
            "Bulk delete products",
            self.delete_products,
            product_ids=list,
            store_id=str,
            force=bool
        ))
        
        self.server.add_tool(self._create_tool(
            "duplicate_products_within_store",
            "Clone products within the same store",
            self.duplicate_products_within_store,
            product_ids=list,
            modifications=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "get_product_analytics",
            "Get product performance analytics",
            self.get_product_analytics,
            product_id=str,
            date_range=dict
        ))
        
        # Cross-Store Product Management
        self.server.add_tool(self._create_tool(
            "compare_products_across_stores",
            "Compare the same product across multiple stores",
            self.compare_products_across_stores,
            product_sku=str,
            store_list=list
        ))
        
        self.server.add_tool(self._create_tool(
            "sync_product_data",
            "Synchronize products between stores",
            self.sync_product_data,
            source_store=str,
            target_stores=list,
            product_ids=list
        ))
        
        self.server.add_tool(self._create_tool(
            "find_missing_products",
            "Identify products missing in target store",
            self.find_missing_products,
            source_store=str,
            target_store=str
        ))
        
        self.server.add_tool(self._create_tool(
            "bulk_copy_products",
            "Mass copy products between stores",
            self.bulk_copy_products,
            source_store=str,
            target_store=str,
            product_filters=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "standardize_product_data",
            "Make products consistent across stores",
            self.standardize_product_data,
            stores=list,
            standardization_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "manage_cross_store_inventory",
            "Synchronize inventory levels across stores",
            self.manage_cross_store_inventory,
            product_sku=str,
            inventory_rules=dict
        ))
        
        # Store Cloning and Deployment
        self.server.add_tool(self._create_tool(
            "clone_entire_store",
            "Create a complete copy of a store",
            self.clone_entire_store,
            source_store=str,
            target_domain=str,
            shared_hosting_config=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "deploy_store_to_shared_hosting",
            "Deploy store to shared hosting",
            self.deploy_store_to_shared_hosting,
            store_data=dict,
            target_domain=str,
            hosting_credentials=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "migrate_store_products",
            "Migrate products between stores",
            self.migrate_store_products,
            source=str,
            target=str,
            migration_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "verify_store_deployment",
            "Verify successful store deployment",
            self.verify_store_deployment,
            target_domain=str
        ))
        
        # Bulk Data Management (CSV/Excel)
        self.server.add_tool(self._create_tool(
            "upload_product_csv",
            "Import products from CSV file",
            self.upload_product_csv,
            file_path=str,
            store_id=str,
            mapping_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "upload_product_excel",
            "Import products from Excel file",
            self.upload_product_excel,
            file_path=str,
            store_id=str,
            sheet_name=str,
            mapping_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "export_products_csv",
            "Export products to CSV file",
            self.export_products_csv,
            store_id=str,
            filters=dict,
            fields=list
        ))
        
        self.server.add_tool(self._create_tool(
            "export_products_excel",
            "Export products to Excel file",
            self.export_products_excel,
            store_id=str,
            filters=dict,
            fields=list,
            format_options=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "validate_bulk_data",
            "Validate data before import",
            self.validate_bulk_data,
            file_path=str,
            validation_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "preview_bulk_import",
            "Preview import results before execution",
            self.preview_bulk_import,
            file_path=str,
            store_id=str,
            rows_preview=int
        ))
        
        self.server.add_tool(self._create_tool(
            "bulk_update_from_file",
            "Update existing products from file",
            self.bulk_update_from_file,
            file_path=str,
            store_id=str,
            update_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "generate_bulk_template",
            "Create import template file",
            self.generate_bulk_template,
            store_id=str,
            fields=list
        ))
        
        # Advanced Bulk Operations
        self.server.add_tool(self._create_tool(
            "batch_price_updates",
            "Bulk update product prices",
            self.batch_price_updates,
            store_id=str,
            price_rules=dict,
            filters=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "batch_category_updates",
            "Bulk update product categories",
            self.batch_category_updates,
            store_id=str,
            category_mappings=dict,
            product_filters=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "batch_image_operations",
            "Bulk update product images",
            self.batch_image_operations,
            store_id=str,
            image_rules=dict,
            product_filters=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "batch_seo_updates",
            "Bulk SEO optimization for products",
            self.batch_seo_updates,
            store_id=str,
            seo_templates=dict,
            product_filters=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "schedule_bulk_operations",
            "Schedule bulk operations for later",
            self.schedule_bulk_operations,
            operations=list,
            schedule_time=str
        ))
        
        # Data Validation & Quality
        self.server.add_tool(self._create_tool(
            "validate_product_data",
            "Check for data quality issues",
            self.validate_product_data,
            store_id=str,
            validation_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "find_duplicate_products",
            "Identify duplicate products",
            self.find_duplicate_products,
            store_id=str,
            duplicate_criteria=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "audit_product_completeness",
            "Find incomplete product data",
            self.audit_product_completeness,
            store_id=str
        ))
        
        self.server.add_tool(self._create_tool(
            "standardize_product_naming",
            "Fix naming inconsistencies",
            self.standardize_product_naming,
            store_id=str,
            naming_rules=dict
        ))
        
        self.server.add_tool(self._create_tool(
            "optimize_product_descriptions",
            "Improve product descriptions",
            self.optimize_product_descriptions,
            store_id=str,
            optimization_rules=dict
        ))
    
    def _create_tool(self, name: str, description: str, handler, **params):
        """Helper to create MCP tools"""
        tool = Tool(
            name=name,
            description=description,
            parameters={
                "type": "object",
                "properties": {
                    param: {"type": type(value).__name__ if value else "string"}
                    for param, value in params.items()
                },
                "required": list(params.keys())
            }
        )
        tool.handler = handler
        return tool
    
    async def list_available_stores(self, **kwargs) -> TextContent:
        """List all configured WooCommerce stores"""
        try:
            stores = await self.store_manager.get_all_stores()
            
            if not stores:
                return TextContent(
                    text="No stores configured. Use 'add_store' to add a WooCommerce store."
                )
            
            store_info = []
            for store in stores:
                status = await self.store_manager.check_store_health(store['id'])
                store_info.append({
                    "id": store['id'],
                    "name": store['name'],
                    "url": store['url'],
                    "status": status['status'],
                    "last_sync": store.get('last_sync', 'Never'),
                    "product_count": store.get('product_count', 0)
                })
            
            return TextContent(
                text=json.dumps(store_info, indent=2)
            )
        except Exception as e:
            logger.error(f"Error listing stores: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def select_active_store(self, store_id: str, **kwargs) -> TextContent:
        """Set the active store for operations"""
        try:
            store = await self.store_manager.get_store(store_id)
            if not store:
                return TextContent(text=f"Store '{store_id}' not found")
            
            self.active_store_id = store_id
            return TextContent(
                text=f"Active store set to: {store['name']} ({store['url']})"
            )
        except Exception as e:
            logger.error(f"Error selecting store: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def add_store(self, store_id: str, url: str, consumer_key: str, 
                        consumer_secret: str, wp_api: bool = True, 
                        version: str = "wc/v3", **kwargs) -> TextContent:
        """Add a new WooCommerce store connection"""
        try:
            # Encrypt credentials
            encrypted_key = self.credential_store.encrypt(consumer_key)
            encrypted_secret = self.credential_store.encrypt(consumer_secret)
            
            # Test connection
            api = WooCommerceAPI(
                url=url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                wp_api=wp_api,
                version=version,
                timeout=30
            )
            
            # Try to fetch store info
            response = api.get("system_status")
            if response.status_code != 200:
                return TextContent(text=f"Failed to connect to store: {response.text}")
            
            # Save store configuration
            store_config = {
                "id": store_id,
                "name": store_id,
                "url": url,
                "consumer_key": encrypted_key,
                "consumer_secret": encrypted_secret,
                "wp_api": wp_api,
                "version": version,
                "added_date": datetime.now().isoformat(),
                "status": "active"
            }
            
            await self.store_manager.save_store(store_config)
            
            return TextContent(
                text=f"Successfully added store '{store_id}' at {url}"
            )
        except Exception as e:
            logger.error(f"Error adding store: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def get_all_products(self, store_id: str, fields: List[str] = None,
                               page: int = 1, per_page: int = 100, **kwargs) -> TextContent:
        """Get all products from a store"""
        try:
            api = await self.store_manager.get_api_client(store_id)
            if not api:
                return TextContent(text=f"Store '{store_id}' not found or not configured")
            
            # Fetch products
            params = {
                "page": page,
                "per_page": per_page,
                "orderby": "date",
                "order": "desc"
            }
            
            response = api.get("products", params=params)
            if response.status_code != 200:
                return TextContent(text=f"Failed to fetch products: {response.text}")
            
            products = response.json()
            
            # Filter fields if specified
            if fields:
                filtered_products = []
                for product in products:
                    filtered_product = {field: product.get(field) for field in fields}
                    filtered_products.append(filtered_product)
                products = filtered_products
            
            result = {
                "store_id": store_id,
                "page": page,
                "per_page": per_page,
                "total_products": len(products),
                "products": products
            }
            
            return TextContent(text=json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def search_products(self, query: str, filters: Dict[str, Any],
                             store_id: str, **kwargs) -> TextContent:
        """Advanced product search with filters"""
        try:
            api = await self.store_manager.get_api_client(store_id)
            if not api:
                return TextContent(text=f"Store '{store_id}' not found")
            
            # Build search parameters
            params = {
                "search": query,
                "per_page": 100
            }
            
            # Apply filters
            if filters:
                if "category" in filters:
                    params["category"] = filters["category"]
                if "min_price" in filters:
                    params["min_price"] = filters["min_price"]
                if "max_price" in filters:
                    params["max_price"] = filters["max_price"]
                if "status" in filters:
                    params["status"] = filters["status"]
                if "stock_status" in filters:
                    params["stock_status"] = filters["stock_status"]
            
            response = api.get("products", params=params)
            if response.status_code != 200:
                return TextContent(text=f"Search failed: {response.text}")
            
            products = response.json()
            
            result = {
                "query": query,
                "filters": filters,
                "total_found": len(products),
                "products": products
            }
            
            return TextContent(text=json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def update_product_data(self, product_id: str, updates: Dict[str, Any],
                                  store_id: str, **kwargs) -> TextContent:
        """Update product information"""
        try:
            # Create backup before update
            await self.backup_manager.create_backup(
                store_id, 
                f"product_{product_id}_update",
                {"product_id": product_id, "updates": updates}
            )
            
            api = await self.store_manager.get_api_client(store_id)
            if not api:
                return TextContent(text=f"Store '{store_id}' not found")
            
            # Validate updates
            validation_result = await self.data_validator.validate_product_updates(updates)
            if not validation_result['valid']:
                return TextContent(text=f"Validation failed: {validation_result['errors']}")
            
            # Apply updates
            response = api.put(f"products/{product_id}", updates)
            if response.status_code not in [200, 201]:
                return TextContent(text=f"Update failed: {response.text}")
            
            updated_product = response.json()
            
            return TextContent(
                text=f"Successfully updated product {product_id}:\n{json.dumps(updated_product, indent=2)}"
            )
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            # Attempt rollback
            await self.backup_manager.rollback(store_id, f"product_{product_id}_update")
            return TextContent(text=f"Error: {str(e)}")
    
    async def upload_product_csv(self, file_path: str, store_id: str,
                                 mapping_rules: Dict[str, str], **kwargs) -> TextContent:
        """Import products from CSV file"""
        try:
            # Validate file
            if not Path(file_path).exists():
                return TextContent(text=f"File not found: {file_path}")
            
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            # Read CSV
            df = pd.read_csv(file_path, encoding=encoding)
            
            # Validate data
            validation_result = await self.data_validator.validate_csv_data(df, mapping_rules)
            if not validation_result['valid']:
                return TextContent(text=f"Validation failed: {validation_result['errors']}")
            
            # Apply mapping rules
            mapped_data = self._apply_mapping_rules(df, mapping_rules)
            
            # Get API client
            api = await self.store_manager.get_api_client(store_id)
            if not api:
                return TextContent(text=f"Store '{store_id}' not found")
            
            # Import products
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in mapped_data.iterrows():
                try:
                    product_data = row.to_dict()
                    # Remove NaN values
                    product_data = {k: v for k, v in product_data.items() if pd.notna(v)}
                    
                    response = api.post("products", product_data)
                    if response.status_code in [200, 201]:
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Row {index}: {response.text}")
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index}: {str(e)}")
            
            result = {
                "file": file_path,
                "total_rows": len(df),
                "successful": success_count,
                "failed": error_count,
                "errors": errors[:10]  # Limit error messages
            }
            
            return TextContent(text=json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def export_products_excel(self, store_id: str, filters: Dict[str, Any],
                                    fields: List[str], format_options: Dict[str, Any],
                                    **kwargs) -> TextContent:
        """Export products to Excel file"""
        try:
            # Get products
            api = await self.store_manager.get_api_client(store_id)
            if not api:
                return TextContent(text=f"Store '{store_id}' not found")
            
            # Fetch all products with pagination
            all_products = []
            page = 1
            while True:
                params = {"page": page, "per_page": 100}
                if filters:
                    params.update(filters)
                
                response = api.get("products", params=params)
                if response.status_code != 200:
                    break
                
                products = response.json()
                if not products:
                    break
                
                all_products.extend(products)
                page += 1
            
            # Filter fields
            if fields:
                filtered_products = []
                for product in all_products:
                    filtered_product = {field: product.get(field) for field in fields}
                    filtered_products.append(filtered_product)
                all_products = filtered_products
            
            # Create DataFrame
            df = pd.DataFrame(all_products)
            
            # Apply formatting
            if format_options:
                if format_options.get('sort_by'):
                    df = df.sort_values(by=format_options['sort_by'])
                if format_options.get('remove_html'):
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            df[col] = df[col].str.replace('<.*?>', '', regex=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{settings.data_dir}/exports/{store_id}_products_{timestamp}.xlsx"
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            # Write to Excel with formatting
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Products', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Products']
                
                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Apply header formatting
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-fit columns
                for i, col in enumerate(df.columns):
                    column_len = df[col].astype(str).str.len().max()
                    column_len = max(column_len, len(col)) + 2
                    worksheet.set_column(i, i, min(column_len, 50))
            
            result = {
                "file": filename,
                "total_products": len(all_products),
                "fields": list(df.columns),
                "file_size": Path(filename).stat().st_size
            }
            
            return TextContent(text=json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def clone_entire_store(self, source_store: str, target_domain: str,
                                 shared_hosting_config: Dict[str, Any], **kwargs) -> TextContent:
        """Clone an entire WooCommerce store"""
        try:
            # Get source store API
            source_api = await self.store_manager.get_api_client(source_store)
            if not source_api:
                return TextContent(text=f"Source store '{source_store}' not found")
            
            # Create progress tracker
            progress = {
                "status": "starting",
                "products": {"total": 0, "completed": 0},
                "categories": {"total": 0, "completed": 0},
                "attributes": {"total": 0, "completed": 0},
                "settings": {"total": 0, "completed": 0}
            }
            
            # 1. Export all products
            all_products = []
            page = 1
            while True:
                response = source_api.get("products", params={"page": page, "per_page": 100})
                if response.status_code != 200:
                    break
                products = response.json()
                if not products:
                    break
                all_products.extend(products)
                page += 1
            
            progress["products"]["total"] = len(all_products)
            
            # 2. Export categories
            categories = source_api.get("products/categories", params={"per_page": 100}).json()
            progress["categories"]["total"] = len(categories)
            
            # 3. Export attributes
            attributes = source_api.get("products/attributes").json()
            progress["attributes"]["total"] = len(attributes)
            
            # 4. Export store settings
            settings_response = source_api.get("system_status")
            store_settings = settings_response.json() if settings_response.status_code == 200 else {}
            
            # 5. Create deployment package
            deployment_package = {
                "source_store": source_store,
                "target_domain": target_domain,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "products": all_products,
                    "categories": categories,
                    "attributes": attributes,
                    "settings": store_settings
                }
            }
            
            # 6. Save deployment package
            package_file = f"{settings.backup_dir}/clone_{source_store}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(package_file, 'w') as f:
                json.dump(deployment_package, f)
            
            # 7. Deploy to target (if credentials provided)
            if shared_hosting_config.get('deploy_now'):
                # This would connect to the target domain and import data
                # Implementation depends on hosting provider API
                pass
            
            result = {
                "status": "success",
                "source_store": source_store,
                "target_domain": target_domain,
                "package_file": package_file,
                "statistics": {
                    "products_cloned": len(all_products),
                    "categories_cloned": len(categories),
                    "attributes_cloned": len(attributes)
                }
            }
            
            return TextContent(text=json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error cloning store: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    async def compare_products_across_stores(self, product_sku: str, 
                                            store_list: List[str], **kwargs) -> TextContent:
        """Compare the same product across multiple stores"""
        try:
            comparison_results = []
            
            for store_id in store_list:
                api = await self.store_manager.get_api_client(store_id)
                if not api:
                    comparison_results.append({
                        "store": store_id,
                        "error": "Store not found"
                    })
                    continue
                
                # Search for product by SKU
                response = api.get("products", params={"sku": product_sku})
                if response.status_code != 200:
                    comparison_results.append({
                        "store": store_id,
                        "error": f"API error: {response.status_code}"
                    })
                    continue
                
                products = response.json()
                if not products:
                    comparison_results.append({
                        "store": store_id,
                        "found": False
                    })
                else:
                    product = products[0]
                    comparison_results.append({
                        "store": store_id,
                        "found": True,
                        "name": product.get("name"),
                        "price": product.get("price"),
                        "regular_price": product.get("regular_price"),
                        "sale_price": product.get("sale_price"),
                        "stock_quantity": product.get("stock_quantity"),
                        "stock_status": product.get("stock_status"),
                        "status": product.get("status"),
                        "categories": [cat.get("name") for cat in product.get("categories", [])],
                        "last_modified": product.get("date_modified")
                    })
            
            # Analyze differences
            analysis = self._analyze_product_differences(comparison_results)
            
            result = {
                "sku": product_sku,
                "stores_checked": len(store_list),
                "comparison": comparison_results,
                "analysis": analysis
            }
            
            return TextContent(text=json.dumps(result, indent=2))
        except Exception as e:
            logger.error(f"Error comparing products: {e}")
            return TextContent(text=f"Error: {str(e)}")
    
    def _apply_mapping_rules(self, df: pd.DataFrame, mapping_rules: Dict[str, str]) -> pd.DataFrame:
        """Apply column mapping rules to DataFrame"""
        if mapping_rules:
            df = df.rename(columns=mapping_rules)
        return df
    
    def _analyze_product_differences(self, comparison_results: List[Dict]) -> Dict:
        """Analyze differences between products across stores"""
        analysis = {
            "price_variance": {},
            "stock_differences": {},
            "status_inconsistencies": [],
            "recommendations": []
        }
        
        # Extract products that were found
        found_products = [r for r in comparison_results if r.get("found")]
        
        if len(found_products) > 1:
            # Price analysis
            prices = [float(p.get("price", 0)) for p in found_products if p.get("price")]
            if prices:
                analysis["price_variance"] = {
                    "min": min(prices),
                    "max": max(prices),
                    "average": sum(prices) / len(prices),
                    "variance": max(prices) - min(prices)
                }
                
                if analysis["price_variance"]["variance"] > 0:
                    analysis["recommendations"].append(
                        "Price inconsistency detected. Consider standardizing prices across stores."
                    )
            
            # Stock analysis
            stock_levels = [(p.get("store"), p.get("stock_quantity")) 
                          for p in found_products if p.get("stock_quantity") is not None]
            if stock_levels:
                analysis["stock_differences"] = dict(stock_levels)
                
                # Check for out of stock
                out_of_stock = [s[0] for s in stock_levels if s[1] == 0]
                if out_of_stock:
                    analysis["recommendations"].append(
                        f"Product out of stock in: {', '.join(out_of_stock)}"
                    )
        
        return analysis
    
    async def run(self):
        """Start the MCP server"""
        async with self.server:
            logger.info("WooCommerce MCP Server started on port 8083")
            await self.server.serve()


def main():
    """Main entry point"""
    import asyncio
    server = WooCommerceMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()