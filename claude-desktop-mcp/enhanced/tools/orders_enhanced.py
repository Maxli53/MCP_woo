"""
Enhanced Order Management Tools
Complete order lifecycle management with advanced analytics
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


def get_order_details(api_client, order_id: int) -> Dict[str, Any]:
    """Get complete order information with enhanced details"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        response = api_client.get(f"orders/{order_id}")
        if response.status_code != 200:
            return {"error": f"Order {order_id} not found"}
        
        order = response.json()
        
        # Enhanced order details
        enhanced_order = {
            "basic_info": {
                "id": order.get("id"),
                "number": order.get("number"),
                "status": order.get("status"),
                "currency": order.get("currency"),
                "total": order.get("total"),
                "subtotal": order.get("subtotal"),
                "total_tax": order.get("total_tax"),
                "shipping_total": order.get("shipping_total"),
                "discount_total": order.get("discount_total"),
                "date_created": order.get("date_created"),
                "date_modified": order.get("date_modified"),
                "date_completed": order.get("date_completed"),
                "date_paid": order.get("date_paid")
            },
            "customer_info": {
                "customer_id": order.get("customer_id"),
                "customer_note": order.get("customer_note"),
                "billing": order.get("billing", {}),
                "shipping": order.get("shipping", {}),
                "payment_method": order.get("payment_method"),
                "payment_method_title": order.get("payment_method_title"),
                "transaction_id": order.get("transaction_id")
            },
            "items": [],
            "fees": order.get("fee_lines", []),
            "coupons": order.get("coupon_lines", []),
            "refunds": order.get("refunds", []),
            "shipping_lines": order.get("shipping_lines", []),
            "tax_lines": order.get("tax_lines", []),
            "meta_data": order.get("meta_data", []),
            "order_analytics": {}
        }
        
        # Process line items with enhanced details
        total_items = 0
        total_quantity = 0
        
        for item in order.get("line_items", []):
            enhanced_item = {
                "id": item.get("id"),
                "name": item.get("name"),
                "product_id": item.get("product_id"),
                "variation_id": item.get("variation_id"),
                "quantity": item.get("quantity"),
                "price": item.get("price"),
                "subtotal": item.get("subtotal"),
                "subtotal_tax": item.get("subtotal_tax"),
                "total": item.get("total"),
                "total_tax": item.get("total_tax"),
                "sku": item.get("sku"),
                "meta_data": item.get("meta_data", [])
            }
            
            # Calculate item analytics
            quantity = int(item.get("quantity", 0))
            total_items += 1
            total_quantity += quantity
            
            # Add variation details if applicable
            if item.get("variation_id"):
                try:
                    var_response = api_client.get(f"products/{item['product_id']}/variations/{item['variation_id']}")
                    if var_response.status_code == 200:
                        variation = var_response.json()
                        enhanced_item["variation_details"] = {
                            "attributes": variation.get("attributes", []),
                            "sku": variation.get("sku"),
                            "stock_status": variation.get("stock_status")
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch variation details: {e}")
            
            enhanced_order["items"].append(enhanced_item)
        
        # Order analytics
        enhanced_order["order_analytics"] = {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "average_item_value": float(order.get("total", 0)) / max(total_quantity, 1),
            "has_discounts": len(order.get("coupon_lines", [])) > 0,
            "discount_percentage": (float(order.get("discount_total", 0)) / max(float(order.get("subtotal", 1)), 1)) * 100,
            "tax_percentage": (float(order.get("total_tax", 0)) / max(float(order.get("subtotal", 1)), 1)) * 100,
            "shipping_percentage": (float(order.get("shipping_total", 0)) / max(float(order.get("total", 1)), 1)) * 100,
            "is_guest_order": order.get("customer_id") == 0,
            "needs_shipping": order.get("shipping_total", "0") != "0"
        }
        
        return enhanced_order
    
    except Exception as e:
        logger.error(f"Error fetching order details {order_id}: {e}")
        return {"error": str(e)}


def update_order_status(api_client, order_id: int, status: str, notes: str = "") -> Dict[str, Any]:
    """Update order status with tracking and notifications"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    valid_statuses = [
        "pending", "processing", "on-hold", "completed", 
        "cancelled", "refunded", "failed", "trash"
    ]
    
    if status not in valid_statuses:
        return {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
    
    try:
        # Get current order state
        current_response = api_client.get(f"orders/{order_id}")
        if current_response.status_code != 200:
            return {"error": f"Order {order_id} not found"}
        
        current_order = current_response.json()
        old_status = current_order.get("status")
        
        # Prepare update data
        update_data = {"status": status}
        
        # Add notes if provided
        if notes:
            current_notes = current_order.get("customer_note", "")
            if current_notes:
                update_data["customer_note"] = f"{current_notes}\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
            else:
                update_data["customer_note"] = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
        
        # Update the order
        response = api_client.put(f"orders/{order_id}", update_data)
        if response.status_code not in [200, 201]:
            return {"error": f"Failed to update order: {response.text}"}
        
        updated_order = response.json()
        
        # Create order note for tracking
        note_data = {
            "note": f"Order status changed from {old_status} to {status}" + (f": {notes}" if notes else ""),
            "customer_note": bool(notes),
            "added_by_user": True
        }
        
        try:
            api_client.post(f"orders/{order_id}/notes", note_data)
        except Exception as e:
            logger.warning(f"Could not add order note: {e}")
        
        return {
            "success": True,
            "order_id": order_id,
            "old_status": old_status,
            "new_status": status,
            "notes_added": bool(notes),
            "updated_at": updated_order.get("date_modified")
        }
    
    except Exception as e:
        logger.error(f"Error updating order status {order_id}: {e}")
        return {"error": str(e)}


def manage_order_items(api_client, order_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add, remove, or modify order items"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get current order
        response = api_client.get(f"orders/{order_id}")
        if response.status_code != 200:
            return {"error": f"Order {order_id} not found"}
        
        current_order = response.json()
        current_items = current_order.get("line_items", [])
        
        results = {
            "order_id": order_id,
            "items_added": 0,
            "items_updated": 0,
            "items_removed": 0,
            "errors": []
        }
        
        for item_operation in items:
            action = item_operation.get("action", "add")  # add, update, remove
            
            try:
                if action == "add":
                    # Add new item to order
                    item_data = {
                        "product_id": item_operation.get("product_id"),
                        "quantity": item_operation.get("quantity", 1)
                    }
                    
                    if item_operation.get("variation_id"):
                        item_data["variation_id"] = item_operation["variation_id"]
                    
                    # Add item
                    item_response = api_client.post(f"orders/{order_id}/items", item_data)
                    if item_response.status_code in [200, 201]:
                        results["items_added"] += 1
                    else:
                        results["errors"].append(f"Failed to add item: {item_response.text}")
                
                elif action == "update":
                    # Update existing item
                    item_id = item_operation.get("item_id")
                    if not item_id:
                        results["errors"].append("Item ID required for update")
                        continue
                    
                    update_data = {}
                    if "quantity" in item_operation:
                        update_data["quantity"] = item_operation["quantity"]
                    
                    if update_data:
                        item_response = api_client.put(f"orders/{order_id}/items/{item_id}", update_data)
                        if item_response.status_code in [200, 201]:
                            results["items_updated"] += 1
                        else:
                            results["errors"].append(f"Failed to update item {item_id}: {item_response.text}")
                
                elif action == "remove":
                    # Remove item from order
                    item_id = item_operation.get("item_id")
                    if not item_id:
                        results["errors"].append("Item ID required for removal")
                        continue
                    
                    item_response = api_client.delete(f"orders/{order_id}/items/{item_id}")
                    if item_response.status_code == 200:
                        results["items_removed"] += 1
                    else:
                        results["errors"].append(f"Failed to remove item {item_id}: {item_response.text}")
            
            except Exception as e:
                results["errors"].append(f"Error processing item operation: {str(e)}")
        
        # Recalculate order totals
        try:
            recalc_response = api_client.put(f"orders/{order_id}", {"calculate_totals": True})
            if recalc_response.status_code not in [200, 201]:
                results["errors"].append("Failed to recalculate order totals")
        except Exception as e:
            results["errors"].append(f"Error recalculating totals: {str(e)}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error managing order items {order_id}: {e}")
        return {"error": str(e)}


def process_refund(api_client, order_id: int, amount: float, reason: str, 
                  refund_items: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Process order refund with detailed tracking"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get order details
        response = api_client.get(f"orders/{order_id}")
        if response.status_code != 200:
            return {"error": f"Order {order_id} not found"}
        
        order = response.json()
        order_total = float(order.get("total", 0))
        
        # Validate refund amount
        if amount <= 0:
            return {"error": "Refund amount must be greater than 0"}
        
        if amount > order_total:
            return {"error": f"Refund amount ({amount}) cannot exceed order total ({order_total})"}
        
        # Prepare refund data
        refund_data = {
            "amount": str(amount),
            "reason": reason,
            "refunded_by": "API"  # Could be enhanced with user identification
        }
        
        # Add line items for partial refunds
        if refund_items:
            line_items = []
            for item in refund_items:
                line_item = {
                    "id": item.get("item_id"),
                    "qty": item.get("quantity", 0),
                    "refund_total": str(item.get("refund_total", 0)),
                    "refund_tax": str(item.get("refund_tax", 0))
                }
                line_items.append(line_item)
            refund_data["line_items"] = line_items
        
        # Process refund
        refund_response = api_client.post(f"orders/{order_id}/refunds", refund_data)
        if refund_response.status_code not in [200, 201]:
            return {"error": f"Refund failed: {refund_response.text}"}
        
        refund_result = refund_response.json()
        
        # Update order status if fully refunded
        if amount >= order_total:
            try:
                api_client.put(f"orders/{order_id}", {"status": "refunded"})
            except Exception as e:
                logger.warning(f"Could not update order status to refunded: {e}")
        
        return {
            "success": True,
            "refund_id": refund_result.get("id"),
            "order_id": order_id,
            "refund_amount": amount,
            "reason": reason,
            "refunded_at": refund_result.get("date_created"),
            "remaining_total": order_total - amount,
            "fully_refunded": amount >= order_total
        }
    
    except Exception as e:
        logger.error(f"Error processing refund for order {order_id}: {e}")
        return {"error": str(e)}


def get_sales_analytics(api_client, date_range: str = "last_30_days", 
                       grouping: str = "day") -> Dict[str, Any]:
    """Get comprehensive sales analytics and revenue reports"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Calculate date range
        end_date = datetime.now()
        
        if date_range == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "yesterday":
            start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif date_range == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif date_range == "last_90_days":
            start_date = end_date - timedelta(days=90)
        elif date_range == "this_month":
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "last_month":
            last_month = end_date.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = last_month.replace(hour=23, minute=59, second=59)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 30 days
        
        # Get orders for the date range
        params = {
            "after": start_date.isoformat(),
            "before": end_date.isoformat(),
            "per_page": 100,
            "status": "completed"  # Only completed orders for sales analytics
        }
        
        all_orders = []
        page = 1
        
        while True:
            params["page"] = page
            response = api_client.get("orders", params=params)
            if response.status_code != 200:
                break
            
            orders = response.json()
            if not orders:
                break
            
            all_orders.extend(orders)
            page += 1
            
            # Safety limit
            if len(all_orders) >= 10000:
                break
        
        if not all_orders:
            return {
                "date_range": date_range,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_orders": 0,
                "total_revenue": 0,
                "message": "No completed orders found in date range"
            }
        
        # Calculate analytics
        analytics = {
            "date_range": date_range,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_orders": len(all_orders),
            "total_revenue": 0,
            "total_tax": 0,
            "total_shipping": 0,
            "total_discounts": 0,
            "average_order_value": 0,
            "total_items_sold": 0,
            "unique_customers": 0,
            "new_customers": 0,
            "payment_methods": {},
            "top_products": {},
            "daily_breakdown": {},
            "customer_analytics": {},
            "geographical_breakdown": {}
        }
        
        customer_ids = set()
        payment_methods = {}
        product_sales = {}
        daily_sales = {}
        countries = {}
        
        for order in all_orders:
            # Basic revenue calculations
            total = float(order.get("total", 0))
            tax = float(order.get("total_tax", 0))
            shipping = float(order.get("shipping_total", 0))
            discount = float(order.get("discount_total", 0))
            
            analytics["total_revenue"] += total
            analytics["total_tax"] += tax
            analytics["total_shipping"] += shipping
            analytics["total_discounts"] += discount
            
            # Customer analytics
            customer_id = order.get("customer_id")
            if customer_id and customer_id != 0:
                customer_ids.add(customer_id)
            
            # Payment method analytics
            payment_method = order.get("payment_method_title", "Unknown")
            payment_methods[payment_method] = payment_methods.get(payment_method, 0) + 1
            
            # Product sales analytics
            for item in order.get("line_items", []):
                product_name = item.get("name", "Unknown")
                quantity = int(item.get("quantity", 0))
                item_total = float(item.get("total", 0))
                
                if product_name in product_sales:
                    product_sales[product_name]["quantity"] += quantity
                    product_sales[product_name]["revenue"] += item_total
                else:
                    product_sales[product_name] = {
                        "quantity": quantity,
                        "revenue": item_total,
                        "product_id": item.get("product_id")
                    }
                
                analytics["total_items_sold"] += quantity
            
            # Daily breakdown
            order_date = datetime.fromisoformat(order.get("date_created", "").replace("Z", "+00:00")).date()
            date_key = order_date.isoformat()
            
            if date_key in daily_sales:
                daily_sales[date_key]["orders"] += 1
                daily_sales[date_key]["revenue"] += total
            else:
                daily_sales[date_key] = {
                    "orders": 1,
                    "revenue": total,
                    "date": date_key
                }
            
            # Geographical breakdown
            billing = order.get("billing", {})
            country = billing.get("country", "Unknown")
            if country in countries:
                countries[country]["orders"] += 1
                countries[country]["revenue"] += total
            else:
                countries[country] = {"orders": 1, "revenue": total}
        
        # Calculate derived metrics
        analytics["unique_customers"] = len(customer_ids)
        analytics["average_order_value"] = analytics["total_revenue"] / max(analytics["total_orders"], 1)
        
        # Format payment methods
        analytics["payment_methods"] = {
            method: {"orders": count, "percentage": (count / analytics["total_orders"]) * 100}
            for method, count in payment_methods.items()
        }
        
        # Format top products (top 10)
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1]["revenue"], reverse=True)
        analytics["top_products"] = {
            name: {
                "quantity_sold": data["quantity"],
                "revenue": data["revenue"],
                "product_id": data.get("product_id"),
                "percentage_of_revenue": (data["revenue"] / analytics["total_revenue"]) * 100
            }
            for name, data in sorted_products[:10]
        }
        
        # Format daily breakdown
        analytics["daily_breakdown"] = list(daily_sales.values())
        analytics["daily_breakdown"].sort(key=lambda x: x["date"])
        
        # Geographical breakdown
        analytics["geographical_breakdown"] = {
            country: {
                "orders": data["orders"],
                "revenue": data["revenue"],
                "percentage_of_orders": (data["orders"] / analytics["total_orders"]) * 100,
                "percentage_of_revenue": (data["revenue"] / analytics["total_revenue"]) * 100
            }
            for country, data in sorted(countries.items(), key=lambda x: x[1]["revenue"], reverse=True)
        }
        
        return analytics
    
    except Exception as e:
        logger.error(f"Error generating sales analytics: {e}")
        return {"error": str(e)}


def get_order_notes(api_client, order_id: int) -> Dict[str, Any]:
    """Get all notes for an order"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        response = api_client.get(f"orders/{order_id}/notes")
        if response.status_code != 200:
            return {"error": f"Could not fetch notes for order {order_id}"}
        
        notes = response.json()
        
        # Format notes with enhanced information
        formatted_notes = []
        for note in notes:
            formatted_note = {
                "id": note.get("id"),
                "author": note.get("author", "System"),
                "date_created": note.get("date_created"),
                "note": note.get("note"),
                "customer_note": note.get("customer_note", False),
                "added_by_user": note.get("added_by_user", False)
            }
            formatted_notes.append(formatted_note)
        
        return {
            "order_id": order_id,
            "total_notes": len(notes),
            "notes": formatted_notes
        }
    
    except Exception as e:
        logger.error(f"Error fetching order notes {order_id}: {e}")
        return {"error": str(e)}


def add_order_note(api_client, order_id: int, note: str, customer_note: bool = False) -> Dict[str, Any]:
    """Add a note to an order"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        note_data = {
            "note": note,
            "customer_note": customer_note,
            "added_by_user": True
        }
        
        response = api_client.post(f"orders/{order_id}/notes", note_data)
        if response.status_code not in [200, 201]:
            return {"error": f"Failed to add note: {response.text}"}
        
        created_note = response.json()
        
        return {
            "success": True,
            "order_id": order_id,
            "note_id": created_note.get("id"),
            "note": note,
            "customer_note": customer_note,
            "date_created": created_note.get("date_created")
        }
    
    except Exception as e:
        logger.error(f"Error adding note to order {order_id}: {e}")
        return {"error": str(e)}