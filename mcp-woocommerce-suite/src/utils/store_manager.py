"""
Store Manager - Handles multiple WooCommerce store connections
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import aiofiles
from woocommerce import API as WooCommerceAPI
from cryptography.fernet import Fernet
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class StoreManager:
    """Manages multiple WooCommerce store connections"""
    
    def __init__(self):
        self.stores_file = settings.stores_dir / "stores.json"
        self.stores_cache = {}
        self.api_clients = {}
        self.cipher = Fernet(settings.security.encryption_key.encode())
        self._load_stores()
    
    def _load_stores(self):
        """Load stores from configuration file"""
        if self.stores_file.exists():
            try:
                with open(self.stores_file, 'r') as f:
                    data = json.load(f)
                    self.stores_cache = data.get('stores', {})
            except Exception as e:
                logger.error(f"Error loading stores: {e}")
                self.stores_cache = {}
    
    async def save_store(self, store_config: Dict[str, Any]) -> bool:
        """Save store configuration"""
        try:
            store_id = store_config['id']
            self.stores_cache[store_id] = store_config
            
            # Save to file
            await self._save_stores_file()
            
            # Clear API client cache for this store
            if store_id in self.api_clients:
                del self.api_clients[store_id]
            
            return True
        except Exception as e:
            logger.error(f"Error saving store: {e}")
            return False
    
    async def _save_stores_file(self):
        """Save stores to configuration file"""
        try:
            self.stores_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'stores': self.stores_cache,
                'last_updated': datetime.now().isoformat()
            }
            
            async with aiofiles.open(self.stores_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error saving stores file: {e}")
    
    async def get_store(self, store_id: str) -> Optional[Dict[str, Any]]:
        """Get store configuration"""
        return self.stores_cache.get(store_id)
    
    async def get_all_stores(self) -> List[Dict[str, Any]]:
        """Get all store configurations"""
        return list(self.stores_cache.values())
    
    async def delete_store(self, store_id: str) -> bool:
        """Delete store configuration"""
        try:
            if store_id in self.stores_cache:
                del self.stores_cache[store_id]
                await self._save_stores_file()
                
                # Clear API client cache
                if store_id in self.api_clients:
                    del self.api_clients[store_id]
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting store: {e}")
            return False
    
    async def get_api_client(self, store_id: str) -> Optional[WooCommerceAPI]:
        """Get WooCommerce API client for a store"""
        try:
            # Check cache
            if store_id in self.api_clients:
                return self.api_clients[store_id]
            
            # Get store configuration
            store = await self.get_store(store_id)
            if not store:
                return None
            
            # Decrypt credentials
            consumer_key = self.cipher.decrypt(store['consumer_key'].encode()).decode()
            consumer_secret = self.cipher.decrypt(store['consumer_secret'].encode()).decode()
            
            # Create API client
            api = WooCommerceAPI(
                url=store['url'],
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                wp_api=store.get('wp_api', True),
                version=store.get('version', 'wc/v3'),
                timeout=settings.woocommerce.api_timeout
            )
            
            # Cache the client
            self.api_clients[store_id] = api
            
            return api
        except Exception as e:
            logger.error(f"Error creating API client for store {store_id}: {e}")
            return None
    
    async def check_store_health(self, store_id: str) -> Dict[str, Any]:
        """Check if store connection is healthy"""
        try:
            api = await self.get_api_client(store_id)
            if not api:
                return {
                    'status': 'error',
                    'message': 'Store not configured'
                }
            
            # Try to fetch system status
            response = api.get("system_status")
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'woocommerce_version': response.json().get('environment', {}).get('version')
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'message': response.text
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def get_store_statistics(self, store_id: str) -> Dict[str, Any]:
        """Get store statistics"""
        try:
            api = await self.get_api_client(store_id)
            if not api:
                return {}
            
            stats = {}
            
            # Get product count
            products_response = api.get("products", params={"per_page": 1})
            if products_response.status_code == 200:
                stats['total_products'] = int(products_response.headers.get('X-WP-Total', 0))
            
            # Get order count
            orders_response = api.get("orders", params={"per_page": 1})
            if orders_response.status_code == 200:
                stats['total_orders'] = int(orders_response.headers.get('X-WP-Total', 0))
            
            # Get customer count
            customers_response = api.get("customers", params={"per_page": 1})
            if customers_response.status_code == 200:
                stats['total_customers'] = int(customers_response.headers.get('X-WP-Total', 0))
            
            # Get categories count
            categories_response = api.get("products/categories", params={"per_page": 1})
            if categories_response.status_code == 200:
                stats['total_categories'] = int(categories_response.headers.get('X-WP-Total', 0))
            
            return stats
        except Exception as e:
            logger.error(f"Error getting store statistics: {e}")
            return {}
    
    async def sync_store_data(self, store_id: str) -> bool:
        """Sync store data to local cache"""
        try:
            store = await self.get_store(store_id)
            if not store:
                return False
            
            # Get updated statistics
            stats = await self.get_store_statistics(store_id)
            
            # Update store record
            store['last_sync'] = datetime.now().isoformat()
            store['product_count'] = stats.get('total_products', 0)
            store['order_count'] = stats.get('total_orders', 0)
            store['customer_count'] = stats.get('total_customers', 0)
            
            # Save updated store
            await self.save_store(store)
            
            return True
        except Exception as e:
            logger.error(f"Error syncing store data: {e}")
            return False
    
    async def test_connection(self, url: str, consumer_key: str, 
                             consumer_secret: str, wp_api: bool = True,
                             version: str = "wc/v3") -> Dict[str, Any]:
        """Test connection to a WooCommerce store"""
        try:
            api = WooCommerceAPI(
                url=url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                wp_api=wp_api,
                version=version,
                timeout=10
            )
            
            response = api.get("system_status")
            
            if response.status_code == 200:
                system_info = response.json()
                return {
                    'success': True,
                    'store_name': system_info.get('environment', {}).get('site_title'),
                    'woocommerce_version': system_info.get('environment', {}).get('version'),
                    'wp_version': system_info.get('environment', {}).get('wp_version')
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'message': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }