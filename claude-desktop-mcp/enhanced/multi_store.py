"""
Multi-Store Management System
Handle connections, synchronization, and operations across multiple WooCommerce stores
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class StoreConfig:
    """Store configuration data class"""
    id: str
    name: str
    url: str
    consumer_key: str
    consumer_secret: str
    store_type: str = "primary"  # primary, secondary, staging, etc.
    language: str = "en"
    currency: str = "EUR"
    timezone: str = "Europe/Helsinki"
    market_region: str = "EU"
    sync_rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.sync_rules is None:
            self.sync_rules = {}


@dataclass
class SyncConfig:
    """Synchronization configuration"""
    products: bool = True
    categories: bool = True
    orders: bool = False
    customers: bool = False
    settings: bool = False
    translations: bool = True
    currencies: bool = True
    regional_settings: bool = True
    direction: str = "one-way"  # one-way, bi-directional
    conflict_resolution: str = "source-wins"  # source-wins, manual, merge
    translation_rules: Dict[str, Any] = None
    currency_conversion: Dict[str, float] = None
    schedule: str = "manual"  # real-time, hourly, daily, manual
    
    def __post_init__(self):
        if self.translation_rules is None:
            self.translation_rules = {}
        if self.currency_conversion is None:
            self.currency_conversion = {}


class MultiStoreManager:
    """Manage multiple WooCommerce store connections and operations"""
    
    def __init__(self):
        self.sync_history = []
        self.sync_conflicts = []
        self.active_syncs = {}
    
    def sync_stores(self, stores: Dict[str, Any], source_store: str, 
                   target_stores: List[str], sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize data between stores"""
        
        sync_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        config = SyncConfig(**sync_config)
        
        # Validate stores
        if source_store not in stores:
            return {"error": f"Source store {source_store} not found"}
        
        for target in target_stores:
            if target not in stores:
                return {"error": f"Target store {target} not found"}
        
        # Initialize sync operation
        self.active_syncs[sync_id] = {
            "source": source_store,
            "targets": target_stores,
            "config": config,
            "status": "running",
            "started": datetime.now().isoformat(),
            "progress": {}
        }
        
        try:
            results = self._perform_sync(stores, source_store, target_stores, config)
            
            # Update sync status
            self.active_syncs[sync_id]["status"] = "completed"
            self.active_syncs[sync_id]["completed"] = datetime.now().isoformat()
            self.active_syncs[sync_id]["results"] = results
            
            # Add to history
            self.sync_history.append(self.active_syncs[sync_id])
            
            return {
                "sync_id": sync_id,
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Sync operation failed: {e}")
            self.active_syncs[sync_id]["status"] = "failed"
            self.active_syncs[sync_id]["error"] = str(e)
            
            return {
                "sync_id": sync_id,
                "status": "failed",
                "error": str(e)
            }
    
    def _perform_sync(self, stores: Dict[str, Any], source_store: str, 
                     target_stores: List[str], config: SyncConfig) -> Dict[str, Any]:
        """Perform the actual synchronization"""
        
        source_api = stores[source_store]['api']
        results = {
            "synced_items": {},
            "conflicts": [],
            "errors": []
        }
        
        for target_store in target_stores:
            target_api = stores[target_store]['api']
            target_config = stores[target_store]['config']
            
            # Sync products
            if config.products:
                product_results = self._sync_products(
                    source_api, target_api, target_config, config
                )
                results["synced_items"][f"{target_store}_products"] = product_results
            
            # Sync categories
            if config.categories:
                category_results = self._sync_categories(
                    source_api, target_api, target_config, config
                )
                results["synced_items"][f"{target_store}_categories"] = category_results
            
            # Sync translations
            if config.translations:
                translation_results = self._sync_translations(
                    source_api, target_api, target_config, config
                )
                results["synced_items"][f"{target_store}_translations"] = translation_results
            
            # Handle currency conversions
            if config.currencies and config.currency_conversion:
                currency_results = self._apply_currency_conversions(
                    target_api, target_config, config
                )
                results["synced_items"][f"{target_store}_currencies"] = currency_results
        
        return results
    
    def _sync_products(self, source_api, target_api, target_config, config) -> Dict[str, Any]:
        """Synchronize products between stores"""
        
        synced = 0
        failed = 0
        conflicts = []
        
        try:
            # Get all products from source
            page = 1
            while True:
                response = source_api.get("products", params={"page": page, "per_page": 100})
                if response.status_code != 200:
                    break
                
                products = response.json()
                if not products:
                    break
                
                for product in products:
                    try:
                        # Apply transformations
                        transformed = self._transform_product(product, target_config, config)
                        
                        # Check if product exists in target
                        existing = self._find_product_by_sku(target_api, product.get('sku'))
                        
                        if existing:
                            # Handle conflict resolution
                            if config.conflict_resolution == "source-wins":
                                response = target_api.put(f"products/{existing['id']}", transformed)
                                if response.status_code in [200, 201]:
                                    synced += 1
                                else:
                                    failed += 1
                            elif config.conflict_resolution == "manual":
                                conflicts.append({
                                    "sku": product.get('sku'),
                                    "source": product,
                                    "target": existing
                                })
                        else:
                            # Create new product
                            response = target_api.post("products", transformed)
                            if response.status_code in [200, 201]:
                                synced += 1
                            else:
                                failed += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to sync product {product.get('id')}: {e}")
                        failed += 1
                
                page += 1
        
        except Exception as e:
            logger.error(f"Product sync failed: {e}")
        
        return {
            "synced": synced,
            "failed": failed,
            "conflicts": conflicts
        }
    
    def _sync_categories(self, source_api, target_api, target_config, config) -> Dict[str, Any]:
        """Synchronize categories between stores"""
        
        synced = 0
        failed = 0
        
        try:
            response = source_api.get("products/categories", params={"per_page": 100})
            if response.status_code == 200:
                categories = response.json()
                
                for category in categories:
                    try:
                        # Apply translations if needed
                        if config.translations and target_config.get('language') != 'en':
                            category = self._translate_category(category, target_config['language'])
                        
                        # Check if category exists
                        existing = self._find_category_by_slug(target_api, category.get('slug'))
                        
                        if existing:
                            response = target_api.put(f"products/categories/{existing['id']}", category)
                        else:
                            response = target_api.post("products/categories", category)
                        
                        if response.status_code in [200, 201]:
                            synced += 1
                        else:
                            failed += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to sync category {category.get('id')}: {e}")
                        failed += 1
        
        except Exception as e:
            logger.error(f"Category sync failed: {e}")
        
        return {"synced": synced, "failed": failed}
    
    def _sync_translations(self, source_api, target_api, target_config, config) -> Dict[str, Any]:
        """Synchronize translations between stores"""
        
        if not config.translation_rules:
            return {"status": "skipped", "reason": "No translation rules provided"}
        
        translated_items = 0
        
        # Apply translation rules based on target language
        target_language = target_config.get('language', 'en')
        
        if target_language in config.translation_rules:
            rules = config.translation_rules[target_language]
            
            # Apply translations to products, categories, etc.
            # This would integrate with a translation service or use predefined mappings
            
            return {"translated": translated_items, "language": target_language}
        
        return {"status": "no_translation_needed", "language": target_language}
    
    def _apply_currency_conversions(self, target_api, target_config, config) -> Dict[str, Any]:
        """Apply currency conversions to product prices"""
        
        target_currency = target_config.get('currency', 'EUR')
        
        if target_currency not in config.currency_conversion:
            return {"status": "skipped", "reason": f"No conversion rate for {target_currency}"}
        
        conversion_rate = config.currency_conversion[target_currency]
        converted_count = 0
        
        try:
            # Get all products and update prices
            page = 1
            while True:
                response = target_api.get("products", params={"page": page, "per_page": 100})
                if response.status_code != 200:
                    break
                
                products = response.json()
                if not products:
                    break
                
                for product in products:
                    try:
                        # Convert prices
                        if product.get('regular_price'):
                            new_price = float(product['regular_price']) * conversion_rate
                            product['regular_price'] = str(round(new_price, 2))
                        
                        if product.get('sale_price'):
                            new_price = float(product['sale_price']) * conversion_rate
                            product['sale_price'] = str(round(new_price, 2))
                        
                        # Update product
                        response = target_api.put(f"products/{product['id']}", product)
                        if response.status_code in [200, 201]:
                            converted_count += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to convert currency for product {product.get('id')}: {e}")
                
                page += 1
        
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
        
        return {
            "converted": converted_count,
            "currency": target_currency,
            "rate": conversion_rate
        }
    
    def _transform_product(self, product: Dict[str, Any], target_config: Dict[str, Any], 
                          sync_config: SyncConfig) -> Dict[str, Any]:
        """Transform product data for target store"""
        
        transformed = product.copy()
        
        # Apply currency conversion if needed
        if sync_config.currency_conversion:
            target_currency = target_config.get('currency', 'EUR')
            if target_currency in sync_config.currency_conversion:
                rate = sync_config.currency_conversion[target_currency]
                
                if transformed.get('regular_price'):
                    transformed['regular_price'] = str(
                        round(float(transformed['regular_price']) * rate, 2)
                    )
                
                if transformed.get('sale_price'):
                    transformed['sale_price'] = str(
                        round(float(transformed['sale_price']) * rate, 2)
                    )
        
        # Apply translation rules if needed
        if sync_config.translation_rules:
            target_language = target_config.get('language', 'en')
            if target_language in sync_config.translation_rules:
                # Apply translations (simplified example)
                # In reality, this would use a translation service
                pass
        
        return transformed
    
    def _find_product_by_sku(self, api, sku: str) -> Optional[Dict[str, Any]]:
        """Find product by SKU"""
        if not sku:
            return None
        
        try:
            response = api.get("products", params={"sku": sku})
            if response.status_code == 200:
                products = response.json()
                if products and len(products) > 0:
                    return products[0]
        except Exception as e:
            logger.error(f"Error finding product by SKU {sku}: {e}")
        
        return None
    
    def _find_category_by_slug(self, api, slug: str) -> Optional[Dict[str, Any]]:
        """Find category by slug"""
        if not slug:
            return None
        
        try:
            response = api.get("products/categories", params={"slug": slug})
            if response.status_code == 200:
                categories = response.json()
                if categories and len(categories) > 0:
                    return categories[0]
        except Exception as e:
            logger.error(f"Error finding category by slug {slug}: {e}")
        
        return None
    
    def _translate_category(self, category: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Translate category (placeholder for actual translation logic)"""
        # This would integrate with a translation service
        # For now, just return the original category
        return category
    
    def get_sync_status(self, store_id: str) -> Dict[str, Any]:
        """Get synchronization status for a store"""
        
        # Find recent syncs involving this store
        recent_syncs = []
        for sync in self.sync_history[-10:]:  # Last 10 syncs
            if sync['source'] == store_id or store_id in sync.get('targets', []):
                recent_syncs.append({
                    "sync_id": sync.get('sync_id'),
                    "role": "source" if sync['source'] == store_id else "target",
                    "status": sync.get('status'),
                    "started": sync.get('started'),
                    "completed": sync.get('completed')
                })
        
        # Find active syncs
        active = []
        for sync_id, sync_data in self.active_syncs.items():
            if sync_data['source'] == store_id or store_id in sync_data.get('targets', []):
                active.append({
                    "sync_id": sync_id,
                    "status": sync_data.get('status'),
                    "progress": sync_data.get('progress')
                })
        
        return {
            "store_id": store_id,
            "recent_syncs": recent_syncs,
            "active_syncs": active,
            "total_syncs": len(recent_syncs)
        }
    
    def resolve_sync_conflicts(self, conflicts: List[Dict[str, Any]], 
                              resolution_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve synchronization conflicts"""
        
        resolved = []
        failed = []
        
        for conflict in conflicts:
            try:
                resolution = resolution_rules.get(conflict['type'], 'skip')
                
                if resolution == 'source-wins':
                    # Use source data
                    resolved.append({
                        "item": conflict['item'],
                        "resolution": "source",
                        "applied": True
                    })
                elif resolution == 'target-wins':
                    # Keep target data
                    resolved.append({
                        "item": conflict['item'],
                        "resolution": "target",
                        "applied": False
                    })
                elif resolution == 'merge':
                    # Merge data (custom logic needed)
                    resolved.append({
                        "item": conflict['item'],
                        "resolution": "merged",
                        "applied": True
                    })
                else:
                    # Skip
                    failed.append(conflict)
            
            except Exception as e:
                logger.error(f"Failed to resolve conflict: {e}")
                failed.append(conflict)
        
        return {
            "resolved": resolved,
            "failed": failed,
            "total": len(conflicts)
        }