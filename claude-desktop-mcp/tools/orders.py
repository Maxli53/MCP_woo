"""
Order management tools for Claude Desktop MCP
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def get_orders(api_client, status: Optional[str] = None, days_back: int = 7) -> Dict[str, Any]:
    """Get recent orders from the store"""
    if not api_client:
        return {"error": "Store not connected"}
    
    params = {
        "per_page": 50,
        "orderby": "date",
        "order": "desc"
    }
    
    if status:
        params["status"] = status
    
    # Add date filter
    after_date = (datetime.now() - timedelta(days=days_back)).isoformat()
    params["after"] = after_date
    
    response = api_client.get("orders", params=params)
    if response.status_code != 200:
        return {"error": f"Failed to fetch orders: {response.status_code}"}
    
    orders = response.json()
    
    return {
        "total_orders": len(orders),
        "date_range": f"Last {days_back} days",
        "orders": [{
            "id": o.get("id"),
            "number": o.get("number"),
            "status": o.get("status"),
            "total": o.get("total"),
            "currency": o.get("currency"),
            "date_created": o.get("date_created"),
            "customer": {
                "name": f"{o.get('billing', {}).get('first_name', '')} {o.get('billing', {}).get('last_name', '')}",
                "email": o.get("billing", {}).get("email")
            }
        } for o in orders]
    }


def get_order(api_client, order_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific order"""
    if not api_client:
        return {"error": "Store not connected"}
    
    response = api_client.get(f"orders/{order_id}")
    if response.status_code != 200:
        return {"error": f"Order not found: {response.status_code}"}
    
    order = response.json()
    
    return {
        "id": order.get("id"),
        "number": order.get("number"),
        "status": order.get("status"),
        "total": order.get("total"),
        "currency": order.get("currency"),
        "date_created": order.get("date_created"),
        "customer": {
            "name": f"{order.get('billing', {}).get('first_name', '')} {order.get('billing', {}).get('last_name', '')}",
            "email": order.get("billing", {}).get("email"),
            "phone": order.get("billing", {}).get("phone")
        },
        "items": [{
            "name": item.get("name"),
            "quantity": item.get("quantity"),
            "total": item.get("total")
        } for item in order.get("line_items", [])],
        "shipping": {
            "method": order.get("shipping_lines", [{}])[0].get("method_title") if order.get("shipping_lines") else None,
            "total": order.get("shipping_total")
        }
    }


def update_order_status(api_client, order_id: int, status: str) -> Dict[str, Any]:
    """Update the status of an order"""
    if not api_client:
        return {"error": "Store not connected"}
    
    valid_statuses = ["pending", "processing", "on-hold", "completed", 
                     "cancelled", "refunded", "failed"]
    
    if status not in valid_statuses:
        return {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
    
    data = {"status": status}
    response = api_client.put(f"orders/{order_id}", data)
    
    if response.status_code not in [200, 201]:
        return {"error": f"Failed to update order: {response.status_code}"}
    
    return {
        "success": True,
        "order_id": order_id,
        "new_status": status
    }