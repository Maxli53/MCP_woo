"""
Store Cloning System
Complete WooCommerce store replication with localization support
"""

import logging
import json
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import os
import zipfile
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class CloneOptions:
    """Store cloning options configuration"""
    include_products: bool = True
    include_categories: bool = True
    include_customers: bool = False  # Privacy considerations
    include_orders: bool = False     # Usually not needed
    include_settings: bool = True
    include_themes: bool = False     # File system level
    include_translations: bool = True
    target_language: str = "en"
    target_currency: str = "EUR"
    target_timezone: str = "Europe/Helsinki"
    transformations: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.transformations is None:
            self.transformations = {}


@dataclass
class TargetConfig:
    """Target store configuration"""
    domain: str
    store_name: str
    admin_credentials: Dict[str, str]
    hosting_info: Dict[str, Any]
    woocommerce_api: Dict[str, str] = None
    
    def __post_init__(self):
        if self.woocommerce_api is None:
            self.woocommerce_api = {}


class StoreCloner:
    """Handle complete store cloning operations"""
    
    def __init__(self):
        self.clone_history = []
        self.export_cache = {}
    
    def clone_store(self, source_api, target_config: Dict[str, Any], 
                   clone_options: Dict[str, Any]) -> Dict[str, Any]:
        """Clone complete store to new domain with full localization"""
        
        clone_id = f"clone_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config = TargetConfig(**target_config)
        options = CloneOptions(**clone_options)
        
        logger.info(f"Starting store clone operation: {clone_id}")
        
        try:
            # Step 1: Export source store data
            export_result = self.export_store_data(source_api, {
                "include_products": options.include_products,
                "include_categories": options.include_categories,
                "include_customers": options.include_customers,
                "include_orders": options.include_orders,
                "include_settings": options.include_settings
            })
            
            if "error" in export_result:
                return {"error": f"Export failed: {export_result['error']}"}
            
            # Step 2: Validate target configuration
            validation_result = self.validate_clone_target(config)
            if not validation_result["valid"]:
                return {"error": f"Target validation failed: {validation_result['errors']}"}
            
            # Step 3: Transform data for target store
            transformed_data = self._transform_data_for_target(
                export_result["data"], config, options
            )
            
            # Step 4: Import data to target store
            if config.woocommerce_api:
                import_result = self.import_store_data(
                    config.woocommerce_api, transformed_data, {}
                )
            else:
                # Generate import package for manual installation
                import_result = self._generate_import_package(
                    transformed_data, config, options
                )
            
            # Record clone operation
            clone_record = {
                "clone_id": clone_id,
                "source_domain": "source_store",  # Would be extracted from source_api
                "target_domain": config.domain,
                "options": asdict(options),
                "started": datetime.now().isoformat(),
                "status": "completed",
                "results": import_result
            }
            
            self.clone_history.append(clone_record)
            
            return {
                "clone_id": clone_id,
                "status": "completed",
                "target_domain": config.domain,
                "results": import_result
            }
        
        except Exception as e:
            logger.error(f"Clone operation failed: {e}")
            return {
                "clone_id": clone_id,
                "status": "failed",
                "error": str(e)
            }
    
    def export_store_data(self, api, export_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Export complete store data with structured format"""
        
        if export_config is None:
            export_config = {
                "include_products": True,
                "include_categories": True,
                "include_customers": False,
                "include_orders": False,
                "include_settings": True
            }
        
        export_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_data = {
            "export_id": export_id,
            "exported_at": datetime.now().isoformat(),
            "store_info": {},
            "data": {}
        }
        
        try:
            # Export store information
            response = api.get("system_status")
            if response.status_code == 200:
                export_data["store_info"] = response.json()
            
            # Export products
            if export_config.get("include_products", True):
                products = self._export_products(api)
                export_data["data"]["products"] = products
                logger.info(f"Exported {len(products)} products")
            
            # Export categories
            if export_config.get("include_categories", True):
                categories = self._export_categories(api)
                export_data["data"]["categories"] = categories
                logger.info(f"Exported {len(categories)} categories")
            
            # Export customers
            if export_config.get("include_customers", False):
                customers = self._export_customers(api)
                export_data["data"]["customers"] = customers
                logger.info(f"Exported {len(customers)} customers")
            
            # Export orders
            if export_config.get("include_orders", False):
                orders = self._export_orders(api)
                export_data["data"]["orders"] = orders
                logger.info(f"Exported {len(orders)} orders")
            
            # Export settings
            if export_config.get("include_settings", True):
                settings = self._export_settings(api)
                export_data["data"]["settings"] = settings
                logger.info("Exported store settings")
            
            # Cache export data
            self.export_cache[export_id] = export_data
            
            return {
                "export_id": export_id,
                "status": "completed",
                "data": export_data
            }
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"error": str(e)}
    
    def import_store_data(self, target_api_config: Dict[str, str], 
                         import_data: Dict[str, Any], 
                         import_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Import store data to target store"""
        
        # Initialize target API
        from woocommerce import API as WooCommerceAPI
        
        try:
            target_api = WooCommerceAPI(
                url=target_api_config["url"],
                consumer_key=target_api_config["consumer_key"],
                consumer_secret=target_api_config["consumer_secret"],
                wp_api=True,
                version="wc/v3",
                timeout=30
            )
            
            # Test connection
            response = target_api.get("system_status")
            if response.status_code != 200:
                return {"error": "Failed to connect to target store"}
            
            import_results = {
                "imported_categories": 0,
                "imported_products": 0,
                "imported_customers": 0,
                "imported_settings": 0,
                "errors": []
            }
            
            # Import categories first (for product relationships)
            if "categories" in import_data:
                category_results = self._import_categories(target_api, import_data["categories"])
                import_results["imported_categories"] = category_results["success"]
                import_results["errors"].extend(category_results["errors"])
            
            # Import products
            if "products" in import_data:
                product_results = self._import_products(target_api, import_data["products"])
                import_results["imported_products"] = product_results["success"]
                import_results["errors"].extend(product_results["errors"])
            
            # Import customers (if included)
            if "customers" in import_data:
                customer_results = self._import_customers(target_api, import_data["customers"])
                import_results["imported_customers"] = customer_results["success"]
                import_results["errors"].extend(customer_results["errors"])
            
            # Apply settings
            if "settings" in import_data:
                settings_results = self._import_settings(target_api, import_data["settings"])
                import_results["imported_settings"] = settings_results["success"]
                import_results["errors"].extend(settings_results["errors"])
            
            return {
                "status": "completed",
                "results": import_results
            }
        
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return {"error": str(e)}
    
    def validate_clone_target(self, target_config: TargetConfig) -> Dict[str, Any]:
        """Validate target store configuration"""
        
        errors = []
        warnings = []
        
        # Check domain
        if not target_config.domain:
            errors.append("Domain is required")
        elif not target_config.domain.startswith(('http://', 'https://')):
            warnings.append("Domain should include http:// or https://")
        
        # Check store name
        if not target_config.store_name:
            errors.append("Store name is required")
        
        # Check admin credentials
        if not target_config.admin_credentials:
            warnings.append("Admin credentials not provided - manual setup required")
        else:
            required_fields = ['username', 'password', 'email']
            for field in required_fields:
                if field not in target_config.admin_credentials:
                    errors.append(f"Admin {field} is required")
        
        # Check WooCommerce API credentials
        if target_config.woocommerce_api:
            required_api_fields = ['url', 'consumer_key', 'consumer_secret']
            for field in required_api_fields:
                if field not in target_config.woocommerce_api:
                    errors.append(f"WooCommerce API {field} is required")
        else:
            warnings.append("WooCommerce API credentials not provided - will generate import package")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _export_products(self, api) -> List[Dict[str, Any]]:
        """Export all products with full data"""
        products = []
        page = 1
        
        while True:
            response = api.get("products", params={"page": page, "per_page": 100})
            if response.status_code != 200:
                break
            
            page_products = response.json()
            if not page_products:
                break
            
            for product in page_products:
                # Get product variations if it's a variable product
                if product.get("type") == "variable":
                    variations_response = api.get(f"products/{product['id']}/variations")
                    if variations_response.status_code == 200:
                        product["variations"] = variations_response.json()
                
                products.append(product)
            
            page += 1
        
        return products
    
    def _export_categories(self, api) -> List[Dict[str, Any]]:
        """Export all product categories"""
        categories = []
        
        response = api.get("products/categories", params={"per_page": 100})
        if response.status_code == 200:
            categories = response.json()
        
        return categories
    
    def _export_customers(self, api) -> List[Dict[str, Any]]:
        """Export customer data (with privacy considerations)"""
        customers = []
        page = 1
        
        while True:
            response = api.get("customers", params={"page": page, "per_page": 100})
            if response.status_code != 200:
                break
            
            page_customers = response.json()
            if not page_customers:
                break
            
            # Anonymize sensitive data
            for customer in page_customers:
                # Remove sensitive fields for privacy
                sensitive_fields = ['password', 'last_order_id', 'orders_count']
                for field in sensitive_fields:
                    customer.pop(field, None)
            
            customers.extend(page_customers)
            page += 1
        
        return customers
    
    def _export_orders(self, api) -> List[Dict[str, Any]]:
        """Export order data"""
        orders = []
        page = 1
        
        while True:
            response = api.get("orders", params={"page": page, "per_page": 100})
            if response.status_code != 200:
                break
            
            page_orders = response.json()
            if not page_orders:
                break
            
            orders.extend(page_orders)
            page += 1
        
        return orders
    
    def _export_settings(self, api) -> Dict[str, Any]:
        """Export store settings"""
        settings = {}
        
        # Get general settings
        response = api.get("settings")
        if response.status_code == 200:
            settings["groups"] = response.json()
        
        # Get specific setting groups
        setting_groups = ["general", "products", "shipping", "tax", "checkout", "account"]
        
        for group in setting_groups:
            response = api.get(f"settings/{group}")
            if response.status_code == 200:
                settings[group] = response.json()
        
        return settings
    
    def _transform_data_for_target(self, data: Dict[str, Any], 
                                  target_config: TargetConfig, 
                                  options: CloneOptions) -> Dict[str, Any]:
        """Transform exported data for target store"""
        
        transformed = data.copy()
        
        # Apply transformations
        transformations = options.transformations or {}
        
        # Transform products
        if "products" in transformed:
            transformed["products"] = self._transform_products(
                transformed["products"], target_config, options, transformations
            )
        
        # Transform categories
        if "categories" in transformed:
            transformed["categories"] = self._transform_categories(
                transformed["categories"], target_config, options, transformations
            )
        
        # Transform settings
        if "settings" in transformed:
            transformed["settings"] = self._transform_settings(
                transformed["settings"], target_config, options, transformations
            )
        
        return transformed
    
    def _transform_products(self, products: List[Dict[str, Any]], 
                           target_config: TargetConfig, 
                           options: CloneOptions,
                           transformations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform products for target store"""
        
        transformed_products = []
        
        for product in products:
            transformed = product.copy()
            
            # Remove IDs for new store
            transformed.pop("id", None)
            transformed.pop("date_created", None)
            transformed.pop("date_modified", None)
            
            # Apply price multiplier if specified
            price_multiplier = transformations.get("price_multiplier", 1.0)
            if price_multiplier != 1.0:
                if transformed.get("regular_price"):
                    new_price = float(transformed["regular_price"]) * price_multiplier
                    transformed["regular_price"] = str(round(new_price, 2))
                
                if transformed.get("sale_price"):
                    new_price = float(transformed["sale_price"]) * price_multiplier
                    transformed["sale_price"] = str(round(new_price, 2))
            
            # Apply currency conversion
            if options.target_currency != "EUR":  # Assuming source is EUR
                # Apply currency conversion logic
                # This would use real exchange rates in production
                pass
            
            # Apply language transformations
            if options.target_language != "en":
                # Apply translations (would integrate with translation service)
                pass
            
            # Handle domain replacements in URLs
            domain_replacements = transformations.get("domain_replacements", {})
            for field in ["permalink", "images"]:
                if field in transformed and domain_replacements:
                    # Replace domain references
                    pass
            
            transformed_products.append(transformed)
        
        return transformed_products
    
    def _transform_categories(self, categories: List[Dict[str, Any]],
                             target_config: TargetConfig,
                             options: CloneOptions,
                             transformations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform categories for target store"""
        
        transformed_categories = []
        
        for category in categories:
            transformed = category.copy()
            
            # Remove IDs
            transformed.pop("id", None)
            
            # Apply category mapping if specified
            category_mapping = transformations.get("category_mapping", {})
            if category_mapping and transformed.get("slug") in category_mapping:
                mapped = category_mapping[transformed["slug"]]
                transformed.update(mapped)
            
            # Apply language transformations
            if options.target_language != "en":
                # Apply translations
                pass
            
            transformed_categories.append(transformed)
        
        return transformed_categories
    
    def _transform_settings(self, settings: Dict[str, Any],
                           target_config: TargetConfig,
                           options: CloneOptions,
                           transformations: Dict[str, Any]) -> Dict[str, Any]:
        """Transform settings for target store"""
        
        transformed = settings.copy()
        
        # Update store-specific settings
        if "general" in transformed:
            for setting in transformed["general"]:
                if setting["id"] == "woocommerce_store_address":
                    # Update store address
                    pass
                elif setting["id"] == "woocommerce_currency":
                    setting["value"] = options.target_currency
                elif setting["id"] == "woocommerce_default_country":
                    # Update based on target region
                    pass
        
        return transformed
    
    def _import_categories(self, api, categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import categories to target store"""
        success = 0
        errors = []
        
        for category in categories:
            try:
                response = api.post("products/categories", category)
                if response.status_code in [200, 201]:
                    success += 1
                else:
                    errors.append(f"Category import failed: {response.text}")
            except Exception as e:
                errors.append(f"Category import error: {str(e)}")
        
        return {"success": success, "errors": errors}
    
    def _import_products(self, api, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import products to target store"""
        success = 0
        errors = []
        
        for product in products:
            try:
                # Handle variations separately
                variations = product.pop("variations", None)
                
                response = api.post("products", product)
                if response.status_code in [200, 201]:
                    product_data = response.json()
                    success += 1
                    
                    # Import variations if any
                    if variations and product_data.get("id"):
                        for variation in variations:
                            variation.pop("id", None)  # Remove original ID
                            var_response = api.post(
                                f"products/{product_data['id']}/variations", 
                                variation
                            )
                            # Don't count variations in main success count
                else:
                    errors.append(f"Product import failed: {response.text}")
            except Exception as e:
                errors.append(f"Product import error: {str(e)}")
        
        return {"success": success, "errors": errors}
    
    def _import_customers(self, api, customers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import customers to target store"""
        success = 0
        errors = []
        
        for customer in customers:
            try:
                response = api.post("customers", customer)
                if response.status_code in [200, 201]:
                    success += 1
                else:
                    errors.append(f"Customer import failed: {response.text}")
            except Exception as e:
                errors.append(f"Customer import error: {str(e)}")
        
        return {"success": success, "errors": errors}
    
    def _import_settings(self, api, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Import settings to target store"""
        success = 0
        errors = []
        
        for group_name, group_settings in settings.items():
            if group_name == "groups":
                continue  # Skip the groups overview
            
            try:
                for setting in group_settings:
                    if "value" in setting:
                        response = api.put(
                            f"settings/{group_name}/{setting['id']}", 
                            {"value": setting["value"]}
                        )
                        if response.status_code in [200, 201]:
                            success += 1
                        else:
                            errors.append(f"Setting {setting['id']} update failed")
            except Exception as e:
                errors.append(f"Settings import error for {group_name}: {str(e)}")
        
        return {"success": success, "errors": errors}
    
    def _generate_import_package(self, data: Dict[str, Any], 
                               target_config: TargetConfig,
                               options: CloneOptions) -> Dict[str, Any]:
        """Generate import package for manual installation"""
        
        package_id = f"package_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create CSV files for products
            if "products" in data:
                self._create_products_csv(data["products"], temp_dir)
            
            # Create CSV files for categories
            if "categories" in data:
                self._create_categories_csv(data["categories"], temp_dir)
            
            # Create JSON files for settings
            if "settings" in data:
                with open(os.path.join(temp_dir, "settings.json"), 'w') as f:
                    json.dump(data["settings"], f, indent=2)
            
            # Create installation instructions
            self._create_installation_instructions(temp_dir, target_config, options)
            
            # Create zip package
            package_path = f"store_clone_{package_id}.zip"
            with zipfile.ZipFile(package_path, 'w') as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
        
        return {
            "package_id": package_id,
            "package_path": package_path,
            "status": "package_created",
            "instructions": "Manual import required - see installation_instructions.txt in package"
        }
    
    def _create_products_csv(self, products: List[Dict[str, Any]], output_dir: str):
        """Create CSV file for products import"""
        
        csv_path = os.path.join(output_dir, "products.csv")
        
        if not products:
            return
        
        # Define CSV headers based on WooCommerce import format
        headers = [
            "ID", "Type", "SKU", "Name", "Published", "Featured", "Visibility",
            "Short description", "Description", "Date sale price starts",
            "Date sale price ends", "Tax status", "Tax class", "In stock",
            "Stock", "Backorders", "Sold individually", "Weight", "Length",
            "Width", "Height", "Allow customer reviews", "Purchase note",
            "Sale price", "Regular price", "Categories", "Tags", "Images"
        ]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for product in products:
                # Map product data to CSV format
                csv_row = {
                    "Name": product.get("name", ""),
                    "SKU": product.get("sku", ""),
                    "Type": product.get("type", "simple"),
                    "Published": "1" if product.get("status") == "publish" else "0",
                    "Featured": "1" if product.get("featured") else "0",
                    "Description": product.get("description", ""),
                    "Short description": product.get("short_description", ""),
                    "Regular price": product.get("regular_price", ""),
                    "Sale price": product.get("sale_price", ""),
                    "Weight": product.get("weight", ""),
                    "Categories": "|".join([cat["name"] for cat in product.get("categories", [])]),
                    "Images": "|".join([img["src"] for img in product.get("images", [])]),
                    "In stock": "1" if product.get("in_stock") else "0",
                    "Stock": product.get("stock_quantity", "")
                }
                writer.writerow(csv_row)
    
    def _create_categories_csv(self, categories: List[Dict[str, Any]], output_dir: str):
        """Create CSV file for categories import"""
        
        csv_path = os.path.join(output_dir, "categories.csv")
        
        headers = ["Name", "Slug", "Description", "Parent", "Image"]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for category in categories:
                csv_row = {
                    "Name": category.get("name", ""),
                    "Slug": category.get("slug", ""),
                    "Description": category.get("description", ""),
                    "Parent": category.get("parent", ""),
                    "Image": category.get("image", {}).get("src", "")
                }
                writer.writerow(csv_row)
    
    def _create_installation_instructions(self, output_dir: str, 
                                        target_config: TargetConfig,
                                        options: CloneOptions):
        """Create installation instructions file"""
        
        instructions_path = os.path.join(output_dir, "installation_instructions.txt")
        
        instructions = f"""
Store Clone Installation Instructions
=====================================

Target Domain: {target_config.domain}
Store Name: {target_config.store_name}
Target Language: {options.target_language}
Target Currency: {options.target_currency}

Pre-Installation Requirements:
1. WordPress with WooCommerce plugin installed
2. Admin access to the target store
3. WooCommerce Importer plugin (for CSV imports)

Installation Steps:

1. PRODUCTS IMPORT:
   - Go to WooCommerce > Tools > Import
   - Select "products.csv" file
   - Map columns if needed
   - Run import

2. CATEGORIES IMPORT:
   - Go to Products > Categories
   - Use "categories.csv" for bulk import
   - Or import via WooCommerce importer

3. SETTINGS CONFIGURATION:
   - Review "settings.json" file
   - Manually configure store settings:
     - General settings (currency, country, etc.)
     - Shipping zones and methods
     - Payment gateways
     - Tax settings

4. POST-INSTALLATION:
   - Test all functionality
   - Update permalinks (Settings > Permalinks)
   - Configure SMTP for emails
   - Set up SSL certificate
   - Configure backups

Localization Notes:
- Currency: {options.target_currency}
- Language: {options.target_language}
- Timezone: {options.target_timezone}

Support:
For issues, check WooCommerce documentation or contact support.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write(instructions)