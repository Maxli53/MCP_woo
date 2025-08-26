"""
Customer Management Tools
Complete customer lifecycle management with analytics
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_customers(api_client, page: int = 1, per_page: int = 50, 
                 search: str = "", role: str = "", order_by: str = "registered_date") -> Dict[str, Any]:
    """Get customer list with advanced search and filtering"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        params = {
            "page": page,
            "per_page": min(per_page, 100),  # API limit
            "orderby": order_by,
            "order": "desc"
        }
        
        if search:
            params["search"] = search
        
        if role:
            params["role"] = role
        
        response = api_client.get("customers", params=params)
        if response.status_code != 200:
            return {"error": f"Failed to fetch customers: {response.text}"}
        
        customers = response.json()
        total_customers = int(response.headers.get("X-WP-Total", 0))
        total_pages = int(response.headers.get("X-WP-TotalPages", 0))
        
        # Enhance customer data
        enhanced_customers = []
        for customer in customers:
            enhanced = {
                "id": customer.get("id"),
                "email": customer.get("email"),
                "username": customer.get("username"),
                "first_name": customer.get("first_name"),
                "last_name": customer.get("last_name"),
                "full_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                "role": customer.get("role"),
                "date_created": customer.get("date_created"),
                "date_modified": customer.get("date_modified"),
                "orders_count": customer.get("orders_count", 0),
                "total_spent": customer.get("total_spent", "0"),
                "avatar_url": customer.get("avatar_url"),
                "billing": customer.get("billing", {}),
                "shipping": customer.get("shipping", {}),
                "is_paying_customer": customer.get("is_paying_customer", False),
                "meta_data": customer.get("meta_data", [])
            }
            
            # Add customer analytics
            enhanced["analytics"] = {
                "registration_days_ago": (datetime.now() - datetime.fromisoformat(
                    customer.get("date_created", "").replace("Z", "+00:00")
                )).days if customer.get("date_created") else None,
                "average_order_value": float(customer.get("total_spent", 0)) / max(customer.get("orders_count", 1), 1),
                "customer_lifetime_value": float(customer.get("total_spent", 0)),
                "customer_segment": _classify_customer_segment(customer)
            }
            
            enhanced_customers.append(enhanced)
        
        return {
            "customers": enhanced_customers,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_customers": total_customers,
                "total_pages": total_pages,
                "has_next_page": page < total_pages,
                "has_previous_page": page > 1
            },
            "search_filters": {
                "search": search,
                "role": role,
                "order_by": order_by
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        return {"error": str(e)}


def get_customer_details(api_client, customer_id: int) -> Dict[str, Any]:
    """Get comprehensive customer profile with order history and analytics"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get customer profile
        customer_response = api_client.get(f"customers/{customer_id}")
        if customer_response.status_code != 200:
            return {"error": f"Customer {customer_id} not found"}
        
        customer = customer_response.json()
        
        # Get customer's order history
        orders_response = api_client.get("orders", params={
            "customer": customer_id,
            "per_page": 100
        })
        
        orders = []
        if orders_response.status_code == 200:
            orders = orders_response.json()
        
        # Build comprehensive customer profile
        profile = {
            "basic_info": {
                "id": customer.get("id"),
                "email": customer.get("email"),
                "username": customer.get("username"),
                "first_name": customer.get("first_name"),
                "last_name": customer.get("last_name"),
                "full_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                "role": customer.get("role"),
                "date_created": customer.get("date_created"),
                "date_modified": customer.get("date_modified"),
                "avatar_url": customer.get("avatar_url")
            },
            "contact_info": {
                "billing": customer.get("billing", {}),
                "shipping": customer.get("shipping", {}),
                "phone": customer.get("billing", {}).get("phone", ""),
                "country": customer.get("billing", {}).get("country", ""),
                "city": customer.get("billing", {}).get("city", ""),
                "postcode": customer.get("billing", {}).get("postcode", "")
            },
            "order_history": {
                "total_orders": len(orders),
                "total_spent": float(customer.get("total_spent", 0)),
                "orders": []
            },
            "analytics": {},
            "preferences": {},
            "meta_data": customer.get("meta_data", [])
        }
        
        # Process order history
        if orders:
            order_statuses = {}
            monthly_spending = {}
            product_preferences = {}
            payment_methods = {}
            
            for order in orders:
                # Basic order info
                order_summary = {
                    "id": order.get("id"),
                    "number": order.get("number"),
                    "status": order.get("status"),
                    "total": order.get("total"),
                    "date_created": order.get("date_created"),
                    "payment_method": order.get("payment_method_title")
                }
                profile["order_history"]["orders"].append(order_summary)
                
                # Status analytics
                status = order.get("status", "unknown")
                order_statuses[status] = order_statuses.get(status, 0) + 1
                
                # Monthly spending
                order_date = datetime.fromisoformat(order.get("date_created", "").replace("Z", "+00:00"))
                month_key = order_date.strftime("%Y-%m")
                monthly_spending[month_key] = monthly_spending.get(month_key, 0) + float(order.get("total", 0))
                
                # Payment method preferences
                payment_method = order.get("payment_method_title", "Unknown")
                payment_methods[payment_method] = payment_methods.get(payment_method, 0) + 1
                
                # Product preferences
                for item in order.get("line_items", []):
                    product_name = item.get("name")
                    if product_name:
                        if product_name in product_preferences:
                            product_preferences[product_name]["quantity"] += int(item.get("quantity", 0))
                            product_preferences[product_name]["total_spent"] += float(item.get("total", 0))
                            product_preferences[product_name]["orders"] += 1
                        else:
                            product_preferences[product_name] = {
                                "quantity": int(item.get("quantity", 0)),
                                "total_spent": float(item.get("total", 0)),
                                "orders": 1,
                                "product_id": item.get("product_id")
                            }
            
            # Calculate analytics
            first_order = min(orders, key=lambda x: x.get("date_created", ""))
            last_order = max(orders, key=lambda x: x.get("date_created", ""))
            
            first_order_date = datetime.fromisoformat(first_order.get("date_created", "").replace("Z", "+00:00"))
            last_order_date = datetime.fromisoformat(last_order.get("date_created", "").replace("Z", "+00:00"))
            
            profile["analytics"] = {
                "customer_lifetime_value": float(customer.get("total_spent", 0)),
                "average_order_value": float(customer.get("total_spent", 0)) / max(len(orders), 1),
                "order_frequency": len(orders) / max((datetime.now() - first_order_date).days / 30, 1),  # orders per month
                "days_since_first_order": (datetime.now() - first_order_date).days,
                "days_since_last_order": (datetime.now() - last_order_date).days,
                "customer_segment": _classify_customer_segment(customer),
                "order_statuses": order_statuses,
                "monthly_spending": monthly_spending,
                "preferred_payment_method": max(payment_methods.items(), key=lambda x: x[1])[0] if payment_methods else "None",
                "top_products": dict(sorted(product_preferences.items(), key=lambda x: x[1]["total_spent"], reverse=True)[:5]),
                "repeat_customer": len(orders) > 1,
                "high_value_customer": float(customer.get("total_spent", 0)) > 500,  # Configurable threshold
                "at_risk": (datetime.now() - last_order_date).days > 90 if orders else False  # No order in 90 days
            }
        
        return profile
    
    except Exception as e:
        logger.error(f"Error fetching customer details {customer_id}: {e}")
        return {"error": str(e)}


def manage_customer_data(api_client, customer_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update customer profile information with validation"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get current customer data
        response = api_client.get(f"customers/{customer_id}")
        if response.status_code != 200:
            return {"error": f"Customer {customer_id} not found"}
        
        current_customer = response.json()
        
        # Validate and prepare update data
        update_data = {}
        changes_made = []
        
        # Basic profile fields
        profile_fields = ["first_name", "last_name", "username", "email"]
        for field in profile_fields:
            if field in updates and updates[field] != current_customer.get(field):
                update_data[field] = updates[field]
                changes_made.append(f"Updated {field}")
        
        # Billing address
        if "billing" in updates:
            current_billing = current_customer.get("billing", {})
            new_billing = current_billing.copy()
            new_billing.update(updates["billing"])
            
            if new_billing != current_billing:
                update_data["billing"] = new_billing
                changes_made.append("Updated billing address")
        
        # Shipping address
        if "shipping" in updates:
            current_shipping = current_customer.get("shipping", {})
            new_shipping = current_shipping.copy()
            new_shipping.update(updates["shipping"])
            
            if new_shipping != current_shipping:
                update_data["shipping"] = new_shipping
                changes_made.append("Updated shipping address")
        
        # Meta data (custom fields)
        if "meta_data" in updates:
            current_meta = current_customer.get("meta_data", [])
            new_meta = []
            
            # Keep existing meta not being updated
            meta_keys_to_update = set(updates["meta_data"].keys())
            for meta in current_meta:
                if meta.get("key") not in meta_keys_to_update:
                    new_meta.append(meta)
            
            # Add updated meta
            for key, value in updates["meta_data"].items():
                new_meta.append({"key": key, "value": value})
                changes_made.append(f"Updated custom field: {key}")
            
            update_data["meta_data"] = new_meta
        
        # Apply updates
        if update_data:
            response = api_client.put(f"customers/{customer_id}", update_data)
            if response.status_code not in [200, 201]:
                return {"error": f"Failed to update customer: {response.text}"}
            
            updated_customer = response.json()
            
            return {
                "success": True,
                "customer_id": customer_id,
                "changes_made": changes_made,
                "updated_fields": list(update_data.keys()),
                "date_modified": updated_customer.get("date_modified")
            }
        else:
            return {"message": "No changes detected"}
    
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        return {"error": str(e)}


def get_customer_analytics(api_client, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get comprehensive customer insights and analytics"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get all customers with pagination
        all_customers = []
        page = 1
        
        while True:
            params = {"page": page, "per_page": 100}
            if filters:
                if "role" in filters:
                    params["role"] = filters["role"]
                if "registered_after" in filters:
                    params["after"] = filters["registered_after"]
                if "registered_before" in filters:
                    params["before"] = filters["registered_before"]
            
            response = api_client.get("customers", params=params)
            if response.status_code != 200:
                break
            
            customers = response.json()
            if not customers:
                break
            
            all_customers.extend(customers)
            page += 1
            
            # Safety limit
            if len(all_customers) >= 10000:
                break
        
        if not all_customers:
            return {"error": "No customers found"}
        
        # Calculate analytics
        analytics = {
            "total_customers": len(all_customers),
            "customer_segments": {
                "new": 0,
                "active": 0,
                "vip": 0,
                "at_risk": 0,
                "inactive": 0
            },
            "registration_trends": {},
            "geographical_distribution": {},
            "value_distribution": {
                "0-50": 0,
                "50-200": 0,
                "200-500": 0,
                "500-1000": 0,
                "1000+": 0
            },
            "order_frequency": {
                "no_orders": 0,
                "1_order": 0,
                "2-5_orders": 0,
                "6-10_orders": 0,
                "10+_orders": 0
            },
            "average_customer_lifetime_value": 0,
            "total_customer_value": 0,
            "top_customers": [],
            "payment_preferences": {},
            "demographic_insights": {}
        }
        
        countries = {}
        total_clv = 0
        customers_with_value = []
        registration_months = {}
        
        for customer in all_customers:
            # Customer lifetime value
            clv = float(customer.get("total_spent", 0))
            total_clv += clv
            
            if clv > 0:
                customers_with_value.append({
                    "id": customer.get("id"),
                    "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                    "email": customer.get("email"),
                    "total_spent": clv,
                    "orders_count": customer.get("orders_count", 0)
                })
            
            # Customer segmentation
            segment = _classify_customer_segment(customer)
            analytics["customer_segments"][segment] += 1
            
            # Value distribution
            if clv == 0:
                analytics["value_distribution"]["0-50"] += 1
            elif clv <= 50:
                analytics["value_distribution"]["0-50"] += 1
            elif clv <= 200:
                analytics["value_distribution"]["50-200"] += 1
            elif clv <= 500:
                analytics["value_distribution"]["200-500"] += 1
            elif clv <= 1000:
                analytics["value_distribution"]["500-1000"] += 1
            else:
                analytics["value_distribution"]["1000+"] += 1
            
            # Order frequency distribution
            orders_count = customer.get("orders_count", 0)
            if orders_count == 0:
                analytics["order_frequency"]["no_orders"] += 1
            elif orders_count == 1:
                analytics["order_frequency"]["1_order"] += 1
            elif orders_count <= 5:
                analytics["order_frequency"]["2-5_orders"] += 1
            elif orders_count <= 10:
                analytics["order_frequency"]["6-10_orders"] += 1
            else:
                analytics["order_frequency"]["10+_orders"] += 1
            
            # Geographical distribution
            billing = customer.get("billing", {})
            country = billing.get("country", "Unknown")
            countries[country] = countries.get(country, 0) + 1
            
            # Registration trends
            if customer.get("date_created"):
                reg_date = datetime.fromisoformat(customer.get("date_created").replace("Z", "+00:00"))
                month_key = reg_date.strftime("%Y-%m")
                registration_months[month_key] = registration_months.get(month_key, 0) + 1
        
        # Calculate derived metrics
        analytics["average_customer_lifetime_value"] = total_clv / len(all_customers)
        analytics["total_customer_value"] = total_clv
        
        # Top customers (by value)
        analytics["top_customers"] = sorted(customers_with_value, key=lambda x: x["total_spent"], reverse=True)[:10]
        
        # Geographical distribution
        analytics["geographical_distribution"] = {
            country: {
                "count": count,
                "percentage": (count / len(all_customers)) * 100
            }
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
        # Registration trends
        analytics["registration_trends"] = dict(sorted(registration_months.items()))
        
        # Calculate percentages for segments
        for segment in analytics["customer_segments"]:
            count = analytics["customer_segments"][segment]
            analytics["customer_segments"][segment] = {
                "count": count,
                "percentage": (count / len(all_customers)) * 100
            }
        
        return analytics
    
    except Exception as e:
        logger.error(f"Error generating customer analytics: {e}")
        return {"error": str(e)}


def create_customer_segment(api_client, segment_name: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Create customer segment based on criteria"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get all customers and apply criteria
        params = {"per_page": 100}
        all_customers = []
        page = 1
        
        while True:
            params["page"] = page
            response = api_client.get("customers", params=params)
            if response.status_code != 200:
                break
            
            customers = response.json()
            if not customers:
                break
            
            all_customers.extend(customers)
            page += 1
            
            if len(all_customers) >= 5000:  # Limit for performance
                break
        
        # Apply segment criteria
        segment_customers = []
        
        for customer in all_customers:
            matches_criteria = True
            
            # Check spending criteria
            if "min_spent" in criteria:
                if float(customer.get("total_spent", 0)) < criteria["min_spent"]:
                    matches_criteria = False
            
            if "max_spent" in criteria:
                if float(customer.get("total_spent", 0)) > criteria["max_spent"]:
                    matches_criteria = False
            
            # Check order count criteria
            if "min_orders" in criteria:
                if customer.get("orders_count", 0) < criteria["min_orders"]:
                    matches_criteria = False
            
            if "max_orders" in criteria:
                if customer.get("orders_count", 0) > criteria["max_orders"]:
                    matches_criteria = False
            
            # Check registration date criteria
            if "registered_after" in criteria:
                reg_date = datetime.fromisoformat(customer.get("date_created", "").replace("Z", "+00:00"))
                after_date = datetime.fromisoformat(criteria["registered_after"])
                if reg_date < after_date:
                    matches_criteria = False
            
            # Check country criteria
            if "countries" in criteria:
                customer_country = customer.get("billing", {}).get("country", "")
                if customer_country not in criteria["countries"]:
                    matches_criteria = False
            
            if matches_criteria:
                segment_customers.append({
                    "id": customer.get("id"),
                    "email": customer.get("email"),
                    "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                    "total_spent": customer.get("total_spent"),
                    "orders_count": customer.get("orders_count")
                })
        
        return {
            "segment_name": segment_name,
            "criteria": criteria,
            "customer_count": len(segment_customers),
            "customers": segment_customers[:100],  # Limit response size
            "total_value": sum(float(c.get("total_spent", 0)) for c in segment_customers),
            "average_value": sum(float(c.get("total_spent", 0)) for c in segment_customers) / max(len(segment_customers), 1)
        }
    
    except Exception as e:
        logger.error(f"Error creating customer segment: {e}")
        return {"error": str(e)}


def _classify_customer_segment(customer: Dict[str, Any]) -> str:
    """Classify customer into segment based on behavior"""
    
    total_spent = float(customer.get("total_spent", 0))
    orders_count = customer.get("orders_count", 0)
    
    # Get registration date
    reg_date = None
    if customer.get("date_created"):
        reg_date = datetime.fromisoformat(customer.get("date_created").replace("Z", "+00:00"))
        days_since_registration = (datetime.now() - reg_date).days
    else:
        days_since_registration = 0
    
    # Classification logic
    if total_spent == 0:
        if days_since_registration <= 30:
            return "new"
        else:
            return "inactive"
    elif total_spent >= 1000:
        return "vip"
    elif orders_count >= 3 and days_since_registration <= 90:
        return "active"
    elif days_since_registration > 180 and orders_count > 0:
        return "at_risk"
    elif days_since_registration <= 30:
        return "new"
    else:
        return "active"