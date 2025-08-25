"""
MCP Server for Claude Desktop Integration
Modern FastMCP-based stdio server for WooCommerce management
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from woocommerce import API as WooCommerceAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP app
mcp = FastMCP("WooCommerce Store Manager")

# Global store configuration
store_config = None
api_client = None

def initialize_store():
    """Initialize store connection from environment variables"""
    global store_config, api_client
    
    store_url = os.getenv('STORE_URL')
    consumer_key = os.getenv('WOOCOMMERCE_KEY')  
    consumer_secret = os.getenv('WOOCOMMERCE_SECRET')
    
    if not all([store_url, consumer_key, consumer_secret]):
        logger.error("Missing required environment variables")
        return False
    
    store_config = {
        "url": store_url,
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret
    }
    
    try:
        api_client = WooCommerceAPI(
            url=store_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            wp_api=True,
            version="wc/v3",
            timeout=30
        )
        
        # Test connection
        response = api_client.get("system_status")
        if response.status_code == 200:
            logger.info(f"Successfully connected to {store_url}")
            return True
        else:
            logger.error(f"Connection test failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize store: {e}")
        return False

# Initialize on startup
initialize_store()

@mcp.tool()
def list_products(page: int = 1, per_page: int = 10, search: str = "") -> str:
    """List products from the WooCommerce store
    
    Args:
        page: Page number (default: 1)
        per_page: Products per page (default: 10) 
        search: Search query (optional)
    """
    if not api_client:
        return "Error: Store not connected"
    
    try:
        params = {
            "page": page,
            "per_page": per_page,
            "orderby": "date",
            "order": "desc"
        }
        
        if search:
            params["search"] = search
        
        response = api_client.get("products", params=params)
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"
        
        products = response.json()
        
        result = {
            "total_products": len(products),
            "page": page,
            "per_page": per_page,
            "products": []
        }
        
        for product in products:
            result["products"].append({
                "id": product["id"],
                "name": product["name"],
                "sku": product["sku"],
                "price": product["price"],
                "regular_price": product["regular_price"],
                "stock_status": product["stock_status"],
                "stock_quantity": product["stock_quantity"],
                "status": product["status"],
                "date_created": product["date_created"]
            })
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_product(product_id: int) -> str:
    """Get detailed information about a specific product
    
    Args:
        product_id: The product ID to retrieve
    """
    if not api_client:
        return "Error: Store not connected"
    
    try:
        response = api_client.get(f"products/{product_id}")
        if response.status_code != 200:
            return f"Product not found: {response.text}"
        
        product = response.json()
        return json.dumps(product, indent=2)
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        return f"Error: {str(e)}"

@mcp.tool() 
def search_products(query: str, category: str = "", status: str = "") -> str:
    """Search products by name, SKU, or description
    
    Args:
        query: Search query
        category: Category filter (optional)
        status: Product status filter (optional)
    """
    if not api_client:
        return "Error: Store not connected"
    
    try:
        params = {
            "search": query,
            "per_page": 20
        }
        
        if category:
            params["category"] = category
        if status:
            params["status"] = status
        
        response = api_client.get("products", params=params)
        if response.status_code != 200:
            return f"Search failed: {response.text}"
        
        products = response.json()
        
        result = {
            "query": query,
            "total_found": len(products),
            "products": []
        }
        
        for product in products:
            result["products"].append({
                "id": product["id"],
                "name": product["name"],
                "sku": product["sku"],
                "price": product["price"],
                "stock_status": product["stock_status"],
                "categories": [cat["name"] for cat in product.get("categories", [])]
            })
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_store_stats() -> str:
    """Get store statistics and overview"""
    if not api_client:
        return "Error: Store not connected"
    
    try:
        # Get basic stats
        products_response = api_client.get("products", params={"per_page": 1})
        orders_response = api_client.get("orders", params={"per_page": 1})
        
        stats = {
            "store_url": store_config["url"] if store_config else "Unknown",
            "timestamp": datetime.now().isoformat(),
            "connection_status": "Connected",
            "products": {
                "accessible": products_response.status_code == 200
            },
            "orders": {
                "accessible": orders_response.status_code == 200
            }
        }
        
        # Add totals from headers if available
        if products_response.status_code == 200:
            total_products = products_response.headers.get('X-WP-Total', 'Unknown')
            stats["products"]["total_count"] = total_products
        
        if orders_response.status_code == 200:
            total_orders = orders_response.headers.get('X-WP-Total', 'Unknown')  
            stats["orders"]["total_count"] = total_orders
        
        return json.dumps(stats, indent=2)
    except Exception as e:
        logger.error(f"Error getting store stats: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_orders(status: str = "", per_page: int = 10) -> str:
    """Get recent orders
    
    Args:
        status: Order status filter (optional)
        per_page: Number of orders to retrieve (default: 10)
    """
    if not api_client:
        return "Error: Store not connected"
    
    try:
        params = {
            "per_page": per_page,
            "orderby": "date", 
            "order": "desc"
        }
        
        if status:
            params["status"] = status
        
        response = api_client.get("orders", params=params)
        if response.status_code != 200:
            return f"Failed to fetch orders: {response.text}"
        
        orders = response.json()
        
        result = {
            "total_orders": len(orders),
            "orders": []
        }
        
        for order in orders:
            result["orders"].append({
                "id": order["id"],
                "status": order["status"],
                "total": order["total"],
                "date_created": order["date_created"],
                "customer_id": order["customer_id"],
                "billing_email": order.get("billing", {}).get("email", "")
            })
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def update_product(product_id: int, updates: dict) -> str:
    """Update product information
    
    Args:
        product_id: The product ID to update
        updates: Dictionary of field updates
    """
    if not api_client:
        return "Error: Store not connected"
    
    try:
        response = api_client.put(f"products/{product_id}", updates)
        if response.status_code not in [200, 201]:
            return f"Update failed: {response.text}"
        
        updated_product = response.json()
        return f"Successfully updated product {product_id}:\n{json.dumps(updated_product, indent=2)}"
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def create_product(product_data: dict) -> str:
    """Create a new product
    
    Args:
        product_data: Dictionary containing product information
    """
    if not api_client:
        return "Error: Store not connected"
    
    try:
        response = api_client.post("products", product_data)
        if response.status_code not in [200, 201]:
            return f"Creation failed: {response.text}"
        
        new_product = response.json()
        return f"Successfully created product:\n{json.dumps(new_product, indent=2)}"
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_categories(per_page: int = 100) -> str:
    """List product categories
    
    Args:
        per_page: Number of categories to retrieve (default: 100)
    """
    if not api_client:
        return "Error: Store not connected"
    
    try:
        params = {"per_page": per_page}
        response = api_client.get("products/categories", params=params)
        
        if response.status_code != 200:
            return f"Failed to fetch categories: {response.text}"
        
        categories = response.json()
        
        result = {
            "total_categories": len(categories),
            "categories": []
        }
        
        for category in categories:
            result["categories"].append({
                "id": category["id"],
                "name": category["name"],
                "slug": category["slug"],
                "count": category.get("count", 0)
            })
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")