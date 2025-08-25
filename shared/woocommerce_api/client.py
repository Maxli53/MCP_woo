"""
WooCommerce API Client Wrapper
Shared by both Web Platform and Claude Desktop MCP
"""

from typing import Dict, Any, Optional, List
from woocommerce import API as WooCommerceAPI
import logging

logger = logging.getLogger(__name__)


class WooCommerceClient:
    """Enhanced WooCommerce API client with error handling"""
    
    def __init__(self, url: str, consumer_key: str, consumer_secret: str, 
                 timeout: int = 30, version: str = "wc/v3"):
        """
        Initialize WooCommerce API client
        
        Args:
            url: Store URL
            consumer_key: WooCommerce consumer key
            consumer_secret: WooCommerce consumer secret
            timeout: Request timeout in seconds
            version: API version
        """
        self.url = url
        self.version = version
        
        try:
            self.api = WooCommerceAPI(
                url=url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                wp_api=True,
                version=version,
                timeout=timeout
            )
            self.connected = self.test_connection()
        except Exception as e:
            logger.error(f"Failed to initialize WooCommerce client: {e}")
            self.api = None
            self.connected = False
    
    def test_connection(self) -> bool:
        """Test the API connection"""
        try:
            response = self.api.get("system_status")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_products(self, **kwargs) -> Dict[str, Any]:
        """Get products with pagination and filters"""
        if not self.connected:
            return {"error": "Not connected to store"}
        
        try:
            response = self.api.get("products", params=kwargs)
            if response.status_code != 200:
                return {"error": f"API error: {response.status_code}"}
            
            return {
                "success": True,
                "data": response.json(),
                "headers": dict(response.headers)
            }
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return {"error": str(e)}
    
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get single product by ID"""
        if not self.connected:
            return {"error": "Not connected to store"}
        
        try:
            response = self.api.get(f"products/{product_id}")
            if response.status_code != 200:
                return {"error": f"Product not found: {response.status_code}"}
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            return {"error": str(e)}
    
    def update_product(self, product_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update product"""
        if not self.connected:
            return {"error": "Not connected to store"}
        
        try:
            response = self.api.put(f"products/{product_id}", data)
            if response.status_code not in [200, 201]:
                return {"error": f"Update failed: {response.status_code}"}
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            return {"error": str(e)}
    
    def create_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new product"""
        if not self.connected:
            return {"error": "Not connected to store"}
        
        try:
            response = self.api.post("products", data)
            if response.status_code not in [200, 201]:
                return {"error": f"Creation failed: {response.status_code}"}
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            return {"error": str(e)}
    
    def get_orders(self, **kwargs) -> Dict[str, Any]:
        """Get orders with filters"""
        if not self.connected:
            return {"error": "Not connected to store"}
        
        try:
            response = self.api.get("orders", params=kwargs)
            if response.status_code != 200:
                return {"error": f"API error: {response.status_code}"}
            
            return {
                "success": True,
                "data": response.json(),
                "headers": dict(response.headers)
            }
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return {"error": str(e)}
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get store system information"""
        if not self.connected:
            return {"error": "Not connected to store"}
        
        try:
            response = self.api.get("system_status")
            if response.status_code != 200:
                return {"error": f"API error: {response.status_code}"}
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            logger.error(f"Error fetching store info: {e}")
            return {"error": str(e)}
    
    def bulk_update_products(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update multiple products"""
        if not self.connected:
            return {"error": "Not connected to store"}
        
        try:
            data = {"update": updates}
            response = self.api.post("products/batch", data)
            if response.status_code not in [200, 201]:
                return {"error": f"Bulk update failed: {response.status_code}"}
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            logger.error(f"Error in bulk update: {e}")
            return {"error": str(e)}