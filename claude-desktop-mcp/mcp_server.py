"""
Claude Desktop MCP Server for WooCommerce
Lightweight stdio server for single-store management
"""

import os
import json
import logging
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from woocommerce import API as WooCommerceAPI

# Import tool modules
from tools import products, orders, store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP app
mcp = FastMCP("WooCommerce Store Manager")

# Global API client
api_client = None


def initialize_store():
    """Initialize store connection from environment variables"""
    global api_client
    
    store_url = os.getenv('STORE_URL')
    consumer_key = os.getenv('WOOCOMMERCE_KEY')  
    consumer_secret = os.getenv('WOOCOMMERCE_SECRET')
    
    if not all([store_url, consumer_key, consumer_secret]):
        logger.error("Missing required environment variables")
        logger.error("Required: STORE_URL, WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET")
        return False
    
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
if not initialize_store():
    logger.warning("Store initialization failed - tools will return errors")


# Product Management Tools
@mcp.tool()
def list_products(page: int = 1, per_page: int = 10, search: str = "") -> str:
    """List products from the WooCommerce store
    
    Args:
        page: Page number (default: 1)
        per_page: Products per page (default: 10)
        search: Search query (optional)
    """
    result = products.list_products(api_client, page, per_page, search)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_product(product_id: int) -> str:
    """Get detailed information about a specific product
    
    Args:
        product_id: The product ID
    """
    result = products.get_product(api_client, product_id)
    return json.dumps(result, indent=2)


@mcp.tool()
def search_products(query: str, category: int = None, 
                   min_price: float = None, max_price: float = None) -> str:
    """Advanced product search with filters
    
    Args:
        query: Search query
        category: Category ID filter (optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
    """
    result = products.search_products(api_client, query, category, min_price, max_price)
    return json.dumps(result, indent=2)


@mcp.tool()
def update_product(product_id: int, name: str = None, description: str = None,
                  regular_price: str = None, sale_price: str = None,
                  stock_quantity: int = None, stock_status: str = None, 
                  sku: str = None) -> str:
    """Update product information
    
    Args:
        product_id: The product ID to update
        name: New product name (optional)
        description: New description (optional)
        regular_price: New regular price (optional)
        sale_price: New sale price (optional)
        stock_quantity: New stock quantity (optional)
        stock_status: New stock status (optional)
        sku: New SKU (optional)
    """
    kwargs = {k: v for k, v in locals().items() 
              if k not in ['product_id', 'api_client'] and v is not None}
    result = products.update_product(api_client, product_id, **kwargs)
    return json.dumps(result, indent=2)


@mcp.tool()
def create_product(name: str, price: str, description: str = "", 
                  sku: str = "", stock_quantity: int = None) -> str:
    """Create a new product
    
    Args:
        name: Product name
        price: Product price
        description: Product description (optional)
        sku: Product SKU (optional)
        stock_quantity: Initial stock quantity (optional)
    """
    result = products.create_product(api_client, name, price, description, sku, stock_quantity)
    return json.dumps(result, indent=2)


# Order Management Tools
@mcp.tool()
def get_orders(status: str = None, days_back: int = 7) -> str:
    """Get recent orders from the store
    
    Args:
        status: Filter by order status (optional)
        days_back: Number of days to look back (default: 7)
    """
    result = orders.get_orders(api_client, status, days_back)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_order(order_id: int) -> str:
    """Get detailed information about a specific order
    
    Args:
        order_id: The order ID
    """
    result = orders.get_order(api_client, order_id)
    return json.dumps(result, indent=2)


@mcp.tool()
def update_order_status(order_id: int, status: str) -> str:
    """Update the status of an order
    
    Args:
        order_id: The order ID
        status: New status (pending/processing/on-hold/completed/cancelled/refunded/failed)
    """
    result = orders.update_order_status(api_client, order_id, status)
    return json.dumps(result, indent=2)


# Store Information Tools
@mcp.tool()
def get_store_stats() -> str:
    """Get store overview and statistics"""
    result = store.get_store_stats(api_client)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_categories(hide_empty: bool = False) -> str:
    """List all product categories
    
    Args:
        hide_empty: Hide categories with no products (default: False)
    """
    result = store.get_categories(api_client, hide_empty)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_coupons() -> str:
    """List all available coupons"""
    result = store.get_coupons(api_client)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()