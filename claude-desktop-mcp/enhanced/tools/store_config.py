"""
Store Configuration Management Tools
Complete store settings, shipping, payments, and tax configuration
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def get_store_settings(api_client) -> Dict[str, Any]:
    """Get all store configuration settings"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        settings = {
            "store_info": {},
            "general_settings": {},
            "product_settings": {},
            "shipping_settings": {},
            "tax_settings": {},
            "checkout_settings": {},
            "account_settings": {},
            "email_settings": {},
            "integration_settings": {}
        }
        
        # Get general store information
        try:
            system_response = api_client.get("system_status")
            if system_response.status_code == 200:
                system_data = system_response.json()
                settings["store_info"] = {
                    "site_url": system_data.get("environment", {}).get("site_url"),
                    "wp_version": system_data.get("environment", {}).get("wp_version"),
                    "wc_version": system_data.get("environment", {}).get("version"),
                    "theme": system_data.get("theme", {}),
                    "active_plugins": len(system_data.get("active_plugins", [])),
                    "currency": system_data.get("settings", {}).get("currency"),
                    "currency_symbol": system_data.get("settings", {}).get("currency_symbol")
                }
        except Exception as e:
            logger.warning(f"Could not fetch system status: {e}")
        
        # Get setting groups
        setting_groups = ["general", "products", "shipping", "tax", "checkout", "account", "email"]
        
        for group in setting_groups:
            try:
                response = api_client.get(f"settings/{group}")
                if response.status_code == 200:
                    group_settings = response.json()
                    formatted_settings = {}
                    
                    for setting in group_settings:
                        formatted_settings[setting.get("id", "")] = {
                            "id": setting.get("id"),
                            "label": setting.get("label"),
                            "description": setting.get("description"),
                            "type": setting.get("type"),
                            "default": setting.get("default"),
                            "value": setting.get("value"),
                            "options": setting.get("options", {}),
                            "tip": setting.get("tip", "")
                        }
                    
                    settings[f"{group}_settings"] = formatted_settings
            
            except Exception as e:
                logger.warning(f"Could not fetch {group} settings: {e}")
                settings[f"{group}_settings"] = {"error": str(e)}
        
        return settings
    
    except Exception as e:
        logger.error(f"Error fetching store settings: {e}")
        return {"error": str(e)}


def update_store_settings(api_client, section: str, setting_updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update store configuration settings by section"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    valid_sections = ["general", "products", "shipping", "tax", "checkout", "account", "email"]
    
    if section not in valid_sections:
        return {"error": f"Invalid section. Must be one of: {', '.join(valid_sections)}"}
    
    try:
        # Get current settings for the section
        response = api_client.get(f"settings/{section}")
        if response.status_code != 200:
            return {"error": f"Could not fetch {section} settings"}
        
        current_settings = response.json()
        setting_ids = {setting["id"]: setting for setting in current_settings}
        
        results = {
            "section": section,
            "updated_settings": [],
            "failed_updates": [],
            "warnings": []
        }
        
        # Update each setting
        for setting_id, new_value in setting_updates.items():
            if setting_id not in setting_ids:
                results["failed_updates"].append({
                    "setting": setting_id,
                    "error": "Setting not found"
                })
                continue
            
            try:
                # Validate setting type and value
                setting_info = setting_ids[setting_id]
                setting_type = setting_info.get("type", "text")
                
                # Type validation
                if setting_type in ["number", "integer"] and not isinstance(new_value, (int, float)):
                    try:
                        new_value = float(new_value) if setting_type == "number" else int(new_value)
                    except ValueError:
                        results["failed_updates"].append({
                            "setting": setting_id,
                            "error": f"Invalid {setting_type} value"
                        })
                        continue
                
                elif setting_type == "checkbox" and not isinstance(new_value, bool):
                    new_value = str(new_value).lower() in ["true", "1", "yes", "on"]
                
                elif setting_type == "select" and setting_info.get("options"):
                    valid_options = list(setting_info["options"].keys())
                    if str(new_value) not in valid_options:
                        results["failed_updates"].append({
                            "setting": setting_id,
                            "error": f"Invalid option. Must be one of: {', '.join(valid_options)}"
                        })
                        continue
                
                # Update the setting
                update_data = {"value": new_value}
                update_response = api_client.put(f"settings/{section}/{setting_id}", update_data)
                
                if update_response.status_code in [200, 201]:
                    updated_setting = update_response.json()
                    results["updated_settings"].append({
                        "id": setting_id,
                        "label": setting_info.get("label"),
                        "old_value": setting_info.get("value"),
                        "new_value": updated_setting.get("value"),
                        "type": setting_type
                    })
                else:
                    results["failed_updates"].append({
                        "setting": setting_id,
                        "error": f"Update failed: {update_response.text}"
                    })
            
            except Exception as e:
                results["failed_updates"].append({
                    "setting": setting_id,
                    "error": str(e)
                })
        
        # Add warnings for critical settings
        critical_settings = {
            "woocommerce_store_address": "Store address affects tax calculations",
            "woocommerce_currency": "Currency changes affect all product prices",
            "woocommerce_store_country": "Country affects shipping and tax settings"
        }
        
        for setting_id in setting_updates:
            if setting_id in critical_settings:
                results["warnings"].append({
                    "setting": setting_id,
                    "warning": critical_settings[setting_id]
                })
        
        return results
    
    except Exception as e:
        logger.error(f"Error updating {section} settings: {e}")
        return {"error": str(e)}


def manage_shipping_zones(api_client, action: str, zone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manage shipping zones and methods"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    valid_actions = ["create", "update", "delete", "list", "get"]
    
    if action not in valid_actions:
        return {"error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"}
    
    try:
        if action == "list":
            response = api_client.get("shipping/zones")
            if response.status_code != 200:
                return {"error": "Failed to fetch shipping zones"}
            
            zones = response.json()
            enhanced_zones = []
            
            for zone in zones:
                zone_id = zone.get("id")
                enhanced_zone = zone.copy()
                
                # Get shipping methods for each zone
                try:
                    methods_response = api_client.get(f"shipping/zones/{zone_id}/methods")
                    if methods_response.status_code == 200:
                        enhanced_zone["methods"] = methods_response.json()
                    else:
                        enhanced_zone["methods"] = []
                except Exception as e:
                    logger.warning(f"Could not fetch methods for zone {zone_id}: {e}")
                    enhanced_zone["methods"] = []
                
                enhanced_zones.append(enhanced_zone)
            
            return {"zones": enhanced_zones}
        
        elif action == "get":
            zone_id = zone_data.get("id")
            if not zone_id:
                return {"error": "Zone ID required for get action"}
            
            response = api_client.get(f"shipping/zones/{zone_id}")
            if response.status_code != 200:
                return {"error": f"Zone {zone_id} not found"}
            
            zone = response.json()
            
            # Get methods for this zone
            methods_response = api_client.get(f"shipping/zones/{zone_id}/methods")
            if methods_response.status_code == 200:
                zone["methods"] = methods_response.json()
            
            return {"zone": zone}
        
        elif action == "create":
            create_data = {
                "name": zone_data.get("name", "New Zone"),
                "order": zone_data.get("order", 0)
            }
            
            response = api_client.post("shipping/zones", create_data)
            if response.status_code not in [200, 201]:
                return {"error": f"Failed to create zone: {response.text}"}
            
            created_zone = response.json()
            
            # Add locations if specified
            if zone_data.get("locations"):
                zone_id = created_zone.get("id")
                for location in zone_data["locations"]:
                    try:
                        api_client.post(f"shipping/zones/{zone_id}/locations", location)
                    except Exception as e:
                        logger.warning(f"Could not add location to zone: {e}")
            
            # Add methods if specified
            if zone_data.get("methods"):
                zone_id = created_zone.get("id")
                for method in zone_data["methods"]:
                    try:
                        api_client.post(f"shipping/zones/{zone_id}/methods", method)
                    except Exception as e:
                        logger.warning(f"Could not add method to zone: {e}")
            
            return {"success": True, "zone": created_zone}
        
        elif action == "update":
            zone_id = zone_data.get("id")
            if not zone_id:
                return {"error": "Zone ID required for update action"}
            
            update_data = {}
            if "name" in zone_data:
                update_data["name"] = zone_data["name"]
            if "order" in zone_data:
                update_data["order"] = zone_data["order"]
            
            if update_data:
                response = api_client.put(f"shipping/zones/{zone_id}", update_data)
                if response.status_code not in [200, 201]:
                    return {"error": f"Failed to update zone: {response.text}"}
            
            return {"success": True, "zone_id": zone_id, "updates": update_data}
        
        elif action == "delete":
            zone_id = zone_data.get("id")
            if not zone_id:
                return {"error": "Zone ID required for delete action"}
            
            response = api_client.delete(f"shipping/zones/{zone_id}")
            if response.status_code != 200:
                return {"error": f"Failed to delete zone: {response.text}"}
            
            return {"success": True, "deleted_zone_id": zone_id}
    
    except Exception as e:
        logger.error(f"Error managing shipping zones: {e}")
        return {"error": str(e)}


def manage_payment_gateways(api_client, gateway_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Configure payment gateway settings"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        if not gateway_id:
            # List all payment gateways
            response = api_client.get("payment_gateways")
            if response.status_code != 200:
                return {"error": "Failed to fetch payment gateways"}
            
            gateways = response.json()
            formatted_gateways = []
            
            for gateway in gateways:
                formatted_gateway = {
                    "id": gateway.get("id"),
                    "title": gateway.get("title"),
                    "description": gateway.get("description"),
                    "enabled": gateway.get("enabled"),
                    "method_title": gateway.get("method_title"),
                    "method_description": gateway.get("method_description"),
                    "order": gateway.get("order"),
                    "settings": gateway.get("settings", {})
                }
                formatted_gateways.append(formatted_gateway)
            
            return {"gateways": formatted_gateways}
        
        else:
            # Get specific gateway
            if not settings:
                response = api_client.get(f"payment_gateways/{gateway_id}")
                if response.status_code != 200:
                    return {"error": f"Gateway {gateway_id} not found"}
                
                return {"gateway": response.json()}
            
            # Update gateway settings
            update_data = {}
            
            # Handle enabled status
            if "enabled" in settings:
                update_data["enabled"] = settings["enabled"]
            
            # Handle title and description
            if "title" in settings:
                update_data["title"] = settings["title"]
            
            if "description" in settings:
                update_data["description"] = settings["description"]
            
            if "order" in settings:
                update_data["order"] = settings["order"]
            
            # Handle gateway-specific settings
            if "gateway_settings" in settings:
                update_data["settings"] = settings["gateway_settings"]
            
            if update_data:
                response = api_client.put(f"payment_gateways/{gateway_id}", update_data)
                if response.status_code not in [200, 201]:
                    return {"error": f"Failed to update gateway: {response.text}"}
                
                updated_gateway = response.json()
                
                return {
                    "success": True,
                    "gateway_id": gateway_id,
                    "updated_settings": update_data,
                    "gateway": updated_gateway
                }
            else:
                return {"error": "No settings provided for update"}
    
    except Exception as e:
        logger.error(f"Error managing payment gateway {gateway_id}: {e}")
        return {"error": str(e)}


def manage_tax_settings(api_client, tax_data: Dict[str, Any]) -> Dict[str, Any]:
    """Configure tax settings and rates"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        action = tax_data.get("action", "get_settings")
        
        if action == "get_settings":
            # Get current tax settings
            response = api_client.get("settings/tax")
            if response.status_code != 200:
                return {"error": "Failed to fetch tax settings"}
            
            tax_settings = response.json()
            
            # Get tax classes
            classes_response = api_client.get("taxes/classes")
            tax_classes = []
            if classes_response.status_code == 200:
                tax_classes = classes_response.json()
            
            # Get tax rates
            rates_response = api_client.get("taxes")
            tax_rates = []
            if rates_response.status_code == 200:
                tax_rates = rates_response.json()
            
            formatted_settings = {}
            for setting in tax_settings:
                formatted_settings[setting.get("id", "")] = {
                    "id": setting.get("id"),
                    "label": setting.get("label"),
                    "value": setting.get("value"),
                    "type": setting.get("type"),
                    "description": setting.get("description")
                }
            
            return {
                "tax_settings": formatted_settings,
                "tax_classes": tax_classes,
                "tax_rates": tax_rates
            }
        
        elif action == "update_settings":
            # Update tax settings
            settings_updates = tax_data.get("settings", {})
            results = {
                "updated_settings": [],
                "failed_updates": []
            }
            
            for setting_id, new_value in settings_updates.items():
                try:
                    update_data = {"value": new_value}
                    response = api_client.put(f"settings/tax/{setting_id}", update_data)
                    
                    if response.status_code in [200, 201]:
                        results["updated_settings"].append({
                            "setting": setting_id,
                            "new_value": new_value
                        })
                    else:
                        results["failed_updates"].append({
                            "setting": setting_id,
                            "error": response.text
                        })
                
                except Exception as e:
                    results["failed_updates"].append({
                        "setting": setting_id,
                        "error": str(e)
                    })
            
            return results
        
        elif action == "create_tax_rate":
            # Create new tax rate
            rate_data = tax_data.get("rate_data", {})
            required_fields = ["country", "rate", "name"]
            
            for field in required_fields:
                if field not in rate_data:
                    return {"error": f"Missing required field: {field}"}
            
            response = api_client.post("taxes", rate_data)
            if response.status_code not in [200, 201]:
                return {"error": f"Failed to create tax rate: {response.text}"}
            
            return {"success": True, "tax_rate": response.json()}
        
        elif action == "update_tax_rate":
            # Update existing tax rate
            rate_id = tax_data.get("rate_id")
            if not rate_id:
                return {"error": "Rate ID required for update"}
            
            rate_updates = tax_data.get("rate_data", {})
            
            response = api_client.put(f"taxes/{rate_id}", rate_updates)
            if response.status_code not in [200, 201]:
                return {"error": f"Failed to update tax rate: {response.text}"}
            
            return {"success": True, "tax_rate": response.json()}
        
        elif action == "delete_tax_rate":
            # Delete tax rate
            rate_id = tax_data.get("rate_id")
            if not rate_id:
                return {"error": "Rate ID required for delete"}
            
            response = api_client.delete(f"taxes/{rate_id}")
            if response.status_code != 200:
                return {"error": f"Failed to delete tax rate: {response.text}"}
            
            return {"success": True, "deleted_rate_id": rate_id}
        
        else:
            return {"error": f"Invalid action: {action}"}
    
    except Exception as e:
        logger.error(f"Error managing tax settings: {e}")
        return {"error": str(e)}


def get_store_reports(api_client, report_type: str = "sales") -> Dict[str, Any]:
    """Get various store reports and analytics"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get available reports
        if report_type == "list":
            response = api_client.get("reports")
            if response.status_code != 200:
                return {"error": "Failed to fetch reports list"}
            
            return {"available_reports": response.json()}
        
        # Get specific report
        response = api_client.get(f"reports/{report_type}")
        if response.status_code != 200:
            return {"error": f"Failed to fetch {report_type} report"}
        
        report_data = response.json()
        
        # Format report based on type
        if report_type == "sales":
            formatted_report = {
                "report_type": "sales",
                "period": "current",
                "data": []
            }
            
            if isinstance(report_data, list):
                for item in report_data:
                    formatted_item = {
                        "period": item.get("period"),
                        "total_sales": item.get("total_sales"),
                        "total_orders": item.get("total_orders"),
                        "total_items": item.get("total_items"),
                        "total_tax": item.get("total_tax"),
                        "total_shipping": item.get("total_shipping"),
                        "total_refunds": item.get("total_refunds"),
                        "average_sales": item.get("average_sales")
                    }
                    formatted_report["data"].append(formatted_item)
            
            return formatted_report
        
        else:
            return {
                "report_type": report_type,
                "raw_data": report_data
            }
    
    except Exception as e:
        logger.error(f"Error fetching {report_type} report: {e}")
        return {"error": str(e)}


def manage_coupons(api_client, action: str, coupon_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Manage store coupons and discounts"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    valid_actions = ["list", "get", "create", "update", "delete"]
    
    if action not in valid_actions:
        return {"error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"}
    
    try:
        if action == "list":
            response = api_client.get("coupons", params={"per_page": 100})
            if response.status_code != 200:
                return {"error": "Failed to fetch coupons"}
            
            coupons = response.json()
            formatted_coupons = []
            
            for coupon in coupons:
                formatted_coupon = {
                    "id": coupon.get("id"),
                    "code": coupon.get("code"),
                    "amount": coupon.get("amount"),
                    "discount_type": coupon.get("discount_type"),
                    "description": coupon.get("description"),
                    "date_expires": coupon.get("date_expires"),
                    "usage_count": coupon.get("usage_count"),
                    "usage_limit": coupon.get("usage_limit"),
                    "minimum_amount": coupon.get("minimum_amount"),
                    "maximum_amount": coupon.get("maximum_amount"),
                    "individual_use": coupon.get("individual_use"),
                    "exclude_sale_items": coupon.get("exclude_sale_items"),
                    "date_created": coupon.get("date_created")
                }
                formatted_coupons.append(formatted_coupon)
            
            return {"coupons": formatted_coupons}
        
        elif action == "get":
            coupon_id = coupon_data.get("id") if coupon_data else None
            if not coupon_id:
                return {"error": "Coupon ID required"}
            
            response = api_client.get(f"coupons/{coupon_id}")
            if response.status_code != 200:
                return {"error": f"Coupon {coupon_id} not found"}
            
            return {"coupon": response.json()}
        
        elif action == "create":
            if not coupon_data:
                return {"error": "Coupon data required for creation"}
            
            required_fields = ["code", "discount_type", "amount"]
            for field in required_fields:
                if field not in coupon_data:
                    return {"error": f"Missing required field: {field}"}
            
            response = api_client.post("coupons", coupon_data)
            if response.status_code not in [200, 201]:
                return {"error": f"Failed to create coupon: {response.text}"}
            
            return {"success": True, "coupon": response.json()}
        
        elif action == "update":
            coupon_id = coupon_data.get("id") if coupon_data else None
            if not coupon_id:
                return {"error": "Coupon ID required for update"}
            
            update_data = {k: v for k, v in coupon_data.items() if k != "id"}
            
            response = api_client.put(f"coupons/{coupon_id}", update_data)
            if response.status_code not in [200, 201]:
                return {"error": f"Failed to update coupon: {response.text}"}
            
            return {"success": True, "coupon": response.json()}
        
        elif action == "delete":
            coupon_id = coupon_data.get("id") if coupon_data else None
            if not coupon_id:
                return {"error": "Coupon ID required for deletion"}
            
            response = api_client.delete(f"coupons/{coupon_id}")
            if response.status_code != 200:
                return {"error": f"Failed to delete coupon: {response.text}"}
            
            return {"success": True, "deleted_coupon_id": coupon_id}
    
    except Exception as e:
        logger.error(f"Error managing coupons: {e}")
        return {"error": str(e)}