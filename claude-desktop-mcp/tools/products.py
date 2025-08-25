"""
Product management tools for Claude Desktop MCP
"""

from typing import Optional, Dict, Any


def list_products(api_client, page: int = 1, per_page: int = 10, search: str = "") -> Dict[str, Any]:
    """List products from the WooCommerce store"""
    if not api_client:
        return {"error": "Store not connected"}
    
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
        return {"error": f"API Error: {response.status_code}"}
    
    products = response.json()
    
    return {
        "total_products": len(products),
        "page": page,
        "products": [{
            "id": p.get("id"),
            "name": p.get("name"),
            "price": p.get("price"),
            "stock_status": p.get("stock_status"),
            "sku": p.get("sku")
        } for p in products]
    }


def get_product(api_client, product_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific product"""
    if not api_client:
        return {"error": "Store not connected"}
    
    response = api_client.get(f"products/{product_id}")
    if response.status_code != 200:
        return {"error": f"Product not found or API error: {response.status_code}"}
    
    return response.json()


def search_products(api_client, query: str, category: Optional[int] = None, 
                   min_price: Optional[float] = None, max_price: Optional[float] = None) -> Dict[str, Any]:
    """Advanced product search with filters"""
    if not api_client:
        return {"error": "Store not connected"}
    
    params = {"search": query, "per_page": 50}
    
    if category:
        params["category"] = category
    if min_price is not None:
        params["min_price"] = str(min_price)
    if max_price is not None:
        params["max_price"] = str(max_price)
    
    response = api_client.get("products", params=params)
    if response.status_code != 200:
        return {"error": f"Search failed: {response.status_code}"}
    
    products = response.json()
    
    return {
        "query": query,
        "results_count": len(products),
        "products": [{
            "id": p.get("id"),
            "name": p.get("name"),
            "price": p.get("price"),
            "categories": [c.get("name") for c in p.get("categories", [])]
        } for p in products]
    }


def update_product(api_client, product_id: int, **kwargs) -> Dict[str, Any]:
    """Update product information"""
    if not api_client:
        return {"error": "Store not connected"}
    
    # Filter allowed update fields
    allowed_fields = ["name", "description", "regular_price", "sale_price", 
                     "stock_quantity", "stock_status", "sku"]
    
    data = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
    
    if not data:
        return {"error": "No valid fields to update"}
    
    response = api_client.put(f"products/{product_id}", data)
    if response.status_code not in [200, 201]:
        return {"error": f"Update failed: {response.status_code}"}
    
    return {"success": True, "updated_fields": list(data.keys())}


def create_product(api_client, name: str, price: str, description: str = "", 
                  sku: str = "", stock_quantity: Optional[int] = None) -> Dict[str, Any]:
    """Create a new product"""
    if not api_client:
        return {"error": "Store not connected"}
    
    data = {
        "name": name,
        "type": "simple",
        "regular_price": price,
        "description": description,
        "sku": sku,
        "manage_stock": stock_quantity is not None
    }
    
    if stock_quantity is not None:
        data["stock_quantity"] = stock_quantity
    
    response = api_client.post("products", data)
    if response.status_code not in [200, 201]:
        return {"error": f"Creation failed: {response.status_code}"}
    
    product = response.json()
    return {
        "success": True,
        "product_id": product.get("id"),
        "name": product.get("name"),
        "permalink": product.get("permalink")
    }