"""
Store information and statistics tools for Claude Desktop MCP
"""

from typing import Dict, Any


def get_store_stats(api_client) -> Dict[str, Any]:
    """Get store overview and statistics"""
    if not api_client:
        return {"error": "Store not connected"}
    
    stats = {}
    
    # Get system status
    response = api_client.get("system_status")
    if response.status_code == 200:
        system = response.json()
        stats["store_info"] = {
            "url": system.get("environment", {}).get("site_url"),
            "wc_version": system.get("environment", {}).get("version"),
            "currency": system.get("settings", {}).get("currency"),
            "currency_symbol": system.get("settings", {}).get("currency_symbol")
        }
    
    # Get reports
    response = api_client.get("reports")
    if response.status_code == 200:
        reports = response.json()
        stats["reports_available"] = [r.get("slug") for r in reports]
    
    # Get sales report
    response = api_client.get("reports/sales", params={"period": "month"})
    if response.status_code == 200:
        sales = response.json()
        if sales:
            latest = sales[0] if isinstance(sales, list) else sales
            stats["sales"] = {
                "total_sales": latest.get("total_sales"),
                "total_orders": latest.get("total_orders"),
                "total_items": latest.get("total_items"),
                "average_sales": latest.get("average_sales")
            }
    
    # Get product count
    response = api_client.get("products", params={"per_page": 1})
    if response.status_code == 200:
        total_products = response.headers.get("X-WP-Total", "Unknown")
        stats["total_products"] = total_products
    
    # Get order count
    response = api_client.get("orders", params={"per_page": 1})
    if response.status_code == 200:
        total_orders = response.headers.get("X-WP-Total", "Unknown")
        stats["total_orders"] = total_orders
    
    # Get customer count
    response = api_client.get("customers", params={"per_page": 1})
    if response.status_code == 200:
        total_customers = response.headers.get("X-WP-Total", "Unknown")
        stats["total_customers"] = total_customers
    
    return stats


def get_categories(api_client, hide_empty: bool = False) -> Dict[str, Any]:
    """List all product categories"""
    if not api_client:
        return {"error": "Store not connected"}
    
    params = {
        "per_page": 100,
        "hide_empty": hide_empty
    }
    
    response = api_client.get("products/categories", params=params)
    if response.status_code != 200:
        return {"error": f"Failed to fetch categories: {response.status_code}"}
    
    categories = response.json()
    
    return {
        "total_categories": len(categories),
        "categories": [{
            "id": c.get("id"),
            "name": c.get("name"),
            "slug": c.get("slug"),
            "count": c.get("count"),
            "parent": c.get("parent")
        } for c in categories]
    }


def get_coupons(api_client) -> Dict[str, Any]:
    """List all available coupons"""
    if not api_client:
        return {"error": "Store not connected"}
    
    response = api_client.get("coupons", params={"per_page": 50})
    if response.status_code != 200:
        return {"error": f"Failed to fetch coupons: {response.status_code}"}
    
    coupons = response.json()
    
    return {
        "total_coupons": len(coupons),
        "coupons": [{
            "id": c.get("id"),
            "code": c.get("code"),
            "amount": c.get("amount"),
            "discount_type": c.get("discount_type"),
            "usage_count": c.get("usage_count"),
            "usage_limit": c.get("usage_limit"),
            "expiry_date": c.get("date_expires")
        } for c in coupons]
    }