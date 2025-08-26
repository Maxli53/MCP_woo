"""
Enhanced Product Management Tools
Complete product operations including variations, attributes, and bulk operations
"""

import logging
from typing import Dict, List, Any, Optional
import csv
import json
from io import StringIO
import pandas as pd

logger = logging.getLogger(__name__)


def get_product_variations(api_client, product_id: int) -> Dict[str, Any]:
    """Get all variations of a variable product with detailed information"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # First check if product is variable
        product_response = api_client.get(f"products/{product_id}")
        if product_response.status_code != 200:
            return {"error": f"Product {product_id} not found"}
        
        product = product_response.json()
        
        if product.get("type") != "variable":
            return {
                "product_id": product_id,
                "product_name": product.get("name"),
                "type": product.get("type"),
                "message": "Product is not variable - no variations available"
            }
        
        # Get variations
        variations_response = api_client.get(f"products/{product_id}/variations")
        if variations_response.status_code != 200:
            return {"error": "Failed to fetch variations"}
        
        variations = variations_response.json()
        
        # Enhance variation data
        enhanced_variations = []
        for variation in variations:
            enhanced = {
                "id": variation.get("id"),
                "sku": variation.get("sku"),
                "price": variation.get("price"),
                "regular_price": variation.get("regular_price"),
                "sale_price": variation.get("sale_price"),
                "stock_status": variation.get("stock_status"),
                "stock_quantity": variation.get("stock_quantity"),
                "manage_stock": variation.get("manage_stock"),
                "attributes": variation.get("attributes", []),
                "image": variation.get("image"),
                "weight": variation.get("weight"),
                "dimensions": variation.get("dimensions"),
                "downloadable": variation.get("downloadable"),
                "virtual": variation.get("virtual"),
                "permalink": variation.get("permalink")
            }
            
            # Format attributes for readability
            attribute_summary = []
            for attr in variation.get("attributes", []):
                attribute_summary.append(f"{attr.get('name')}: {attr.get('option')}")
            enhanced["attribute_summary"] = " | ".join(attribute_summary)
            
            enhanced_variations.append(enhanced)
        
        return {
            "product_id": product_id,
            "product_name": product.get("name"),
            "product_sku": product.get("sku"),
            "total_variations": len(variations),
            "variations": enhanced_variations,
            "product_attributes": product.get("attributes", [])
        }
    
    except Exception as e:
        logger.error(f"Error fetching variations for product {product_id}: {e}")
        return {"error": str(e)}


def manage_product_attributes(api_client, product_id: int, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Manage product custom fields, specifications, and attributes"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get current product
        response = api_client.get(f"products/{product_id}")
        if response.status_code != 200:
            return {"error": f"Product {product_id} not found"}
        
        product = response.json()
        
        # Prepare update data
        update_data = {}
        changes_made = []
        
        # Handle custom attributes
        if "custom_attributes" in attributes:
            current_attributes = product.get("attributes", [])
            new_attributes = []
            
            # Keep existing attributes not being modified
            for attr in current_attributes:
                attr_name = attr.get("name", "")
                if attr_name not in attributes["custom_attributes"]:
                    new_attributes.append(attr)
            
            # Add/update new attributes
            for attr_name, attr_config in attributes["custom_attributes"].items():
                new_attr = {
                    "name": attr_name,
                    "visible": attr_config.get("visible", True),
                    "variation": attr_config.get("variation", False),
                    "options": attr_config.get("options", [])
                }
                
                # Handle taxonomy attributes
                if attr_config.get("taxonomy"):
                    new_attr["slug"] = attr_config["taxonomy"]
                
                new_attributes.append(new_attr)
                changes_made.append(f"Updated attribute: {attr_name}")
            
            update_data["attributes"] = new_attributes
        
        # Handle meta data (custom fields)
        if "meta_data" in attributes:
            current_meta = product.get("meta_data", [])
            new_meta = []
            
            # Keep existing meta not being modified
            meta_keys_to_update = set(attributes["meta_data"].keys())
            for meta in current_meta:
                if meta.get("key") not in meta_keys_to_update:
                    new_meta.append(meta)
            
            # Add/update new meta
            for key, value in attributes["meta_data"].items():
                new_meta.append({
                    "key": key,
                    "value": value
                })
                changes_made.append(f"Updated meta field: {key}")
            
            update_data["meta_data"] = new_meta
        
        # Handle specifications (stored as meta data with special prefix)
        if "specifications" in attributes:
            current_meta = product.get("meta_data", [])
            new_meta = []
            
            # Keep non-specification meta
            for meta in current_meta:
                if not meta.get("key", "").startswith("_spec_"):
                    new_meta.append(meta)
            
            # Add specification meta
            for spec_name, spec_value in attributes["specifications"].items():
                new_meta.append({
                    "key": f"_spec_{spec_name}",
                    "value": spec_value
                })
                changes_made.append(f"Updated specification: {spec_name}")
            
            if "meta_data" not in update_data:
                update_data["meta_data"] = new_meta
            else:
                update_data["meta_data"].extend([m for m in new_meta if m.get("key", "").startswith("_spec_")])
        
        # Handle product dimensions and weight
        if "dimensions" in attributes:
            dims = attributes["dimensions"]
            if isinstance(dims, dict):
                update_data["dimensions"] = dims
                changes_made.append("Updated product dimensions")
        
        if "weight" in attributes:
            update_data["weight"] = str(attributes["weight"])
            changes_made.append("Updated product weight")
        
        # Handle shipping class
        if "shipping_class" in attributes:
            update_data["shipping_class"] = attributes["shipping_class"]
            changes_made.append("Updated shipping class")
        
        # Update the product
        if update_data:
            response = api_client.put(f"products/{product_id}", update_data)
            if response.status_code not in [200, 201]:
                return {"error": f"Failed to update product: {response.text}"}
            
            updated_product = response.json()
            
            return {
                "success": True,
                "product_id": product_id,
                "product_name": product.get("name"),
                "changes_made": changes_made,
                "updated_attributes": len(update_data.get("attributes", [])),
                "updated_meta_fields": len([m for m in update_data.get("meta_data", []) if not m.get("key", "").startswith("_spec_")]),
                "updated_specifications": len([m for m in update_data.get("meta_data", []) if m.get("key", "").startswith("_spec_")])
            }
        else:
            return {"message": "No changes specified"}
    
    except Exception as e:
        logger.error(f"Error managing attributes for product {product_id}: {e}")
        return {"error": str(e)}


def import_products(api_client, file_data: str, mapping_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Import products from CSV/Excel with advanced mapping rules"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Parse the file data
        if file_data.startswith("data:"):
            # Handle base64 encoded data
            import base64
            header, data = file_data.split(",", 1)
            decoded_data = base64.b64decode(data).decode('utf-8')
        else:
            decoded_data = file_data
        
        # Determine file format and parse
        if mapping_rules.get("format", "csv").lower() == "csv":
            df = pd.read_csv(StringIO(decoded_data))
        elif mapping_rules.get("format", "csv").lower() in ["xlsx", "excel"]:
            df = pd.read_excel(StringIO(decoded_data))
        else:
            return {"error": "Unsupported file format"}
        
        # Validate required columns
        required_columns = mapping_rules.get("required_columns", ["name"])
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {"error": f"Missing required columns: {missing_columns}"}
        
        # Process mapping rules
        column_mapping = mapping_rules.get("column_mapping", {})
        
        import_results = {
            "total_rows": len(df),
            "successful_imports": 0,
            "failed_imports": 0,
            "skipped_rows": 0,
            "errors": [],
            "imported_products": []
        }
        
        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get("name")) or str(row.get("name")).strip() == "":
                    import_results["skipped_rows"] += 1
                    continue
                
                # Build product data
                product_data = {}
                
                # Map basic fields
                field_mappings = {
                    "name": "name",
                    "description": "description",
                    "short_description": "short_description",
                    "sku": "sku",
                    "regular_price": "regular_price",
                    "sale_price": "sale_price",
                    "weight": "weight",
                    "status": "status"
                }
                
                for csv_field, wc_field in field_mappings.items():
                    mapped_field = column_mapping.get(csv_field, csv_field)
                    if mapped_field in row and pd.notna(row[mapped_field]):
                        value = str(row[mapped_field]).strip()
                        if value:
                            product_data[wc_field] = value
                
                # Handle categories
                if "categories" in row and pd.notna(row["categories"]):
                    categories_str = str(row["categories"])
                    category_names = [cat.strip() for cat in categories_str.split("|")]
                    
                    # Find or create categories
                    categories = []
                    for cat_name in category_names:
                        category = find_or_create_category(api_client, cat_name)
                        if category:
                            categories.append({"id": category["id"]})
                    
                    if categories:
                        product_data["categories"] = categories
                
                # Handle images
                if "images" in row and pd.notna(row["images"]):
                    images_str = str(row["images"])
                    image_urls = [url.strip() for url in images_str.split("|")]
                    
                    images = []
                    for url in image_urls:
                        if url.startswith("http"):
                            images.append({"src": url})
                    
                    if images:
                        product_data["images"] = images
                
                # Handle attributes
                attribute_columns = [col for col in df.columns if col.startswith("attribute_")]
                if attribute_columns:
                    attributes = []
                    for attr_col in attribute_columns:
                        if pd.notna(row[attr_col]):
                            attr_name = attr_col.replace("attribute_", "")
                            attr_value = str(row[attr_col]).strip()
                            
                            attributes.append({
                                "name": attr_name,
                                "options": [attr_value],
                                "visible": True,
                                "variation": False
                            })
                    
                    if attributes:
                        product_data["attributes"] = attributes
                
                # Handle stock
                if "stock_quantity" in row and pd.notna(row["stock_quantity"]):
                    try:
                        stock_qty = int(float(row["stock_quantity"]))
                        product_data["stock_quantity"] = stock_qty
                        product_data["manage_stock"] = True
                    except ValueError:
                        pass
                
                # Set default values
                product_data.setdefault("type", "simple")
                product_data.setdefault("status", "publish")
                
                # Check if product exists (by SKU)
                existing_product = None
                if product_data.get("sku"):
                    existing_product = find_product_by_sku(api_client, product_data["sku"])
                
                if existing_product and mapping_rules.get("update_existing", False):
                    # Update existing product
                    response = api_client.put(f"products/{existing_product['id']}", product_data)
                elif not existing_product:
                    # Create new product
                    response = api_client.post("products", product_data)
                else:
                    # Skip existing product
                    import_results["skipped_rows"] += 1
                    continue
                
                if response.status_code in [200, 201]:
                    product = response.json()
                    import_results["successful_imports"] += 1
                    import_results["imported_products"].append({
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "sku": product.get("sku"),
                        "action": "updated" if existing_product else "created"
                    })
                else:
                    import_results["failed_imports"] += 1
                    import_results["errors"].append(f"Row {index + 1}: {response.text}")
            
            except Exception as e:
                import_results["failed_imports"] += 1
                import_results["errors"].append(f"Row {index + 1}: {str(e)}")
        
        return import_results
    
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return {"error": str(e)}


def export_products(api_client, filters: Dict[str, Any] = None, 
                   format: str = "csv", columns: List[str] = None) -> Dict[str, Any]:
    """Export products with custom formatting and filters"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Default columns for export
        default_columns = [
            "id", "name", "sku", "type", "status", "featured", "catalog_visibility",
            "description", "short_description", "regular_price", "sale_price",
            "stock_status", "stock_quantity", "weight", "categories", "tags", "images"
        ]
        
        export_columns = columns or default_columns
        
        # Build API parameters from filters
        params = {"per_page": 100}
        if filters:
            if "status" in filters:
                params["status"] = filters["status"]
            if "featured" in filters:
                params["featured"] = filters["featured"]
            if "category" in filters:
                params["category"] = filters["category"]
            if "search" in filters:
                params["search"] = filters["search"]
            if "min_price" in filters:
                params["min_price"] = filters["min_price"]
            if "max_price" in filters:
                params["max_price"] = filters["max_price"]
        
        # Fetch all products
        all_products = []
        page = 1
        
        while True:
            params["page"] = page
            response = api_client.get("products", params=params)
            if response.status_code != 200:
                break
            
            products = response.json()
            if not products:
                break
            
            all_products.extend(products)
            page += 1
            
            # Safety limit
            if len(all_products) >= 10000:
                break
        
        if not all_products:
            return {"error": "No products found matching filters"}
        
        # Format data for export
        export_data = []
        for product in all_products:
            row = {}
            
            for column in export_columns:
                if column == "categories":
                    categories = product.get("categories", [])
                    row[column] = " | ".join([cat["name"] for cat in categories])
                elif column == "tags":
                    tags = product.get("tags", [])
                    row[column] = " | ".join([tag["name"] for tag in tags])
                elif column == "images":
                    images = product.get("images", [])
                    row[column] = " | ".join([img["src"] for img in images])
                elif column == "attributes":
                    attributes = product.get("attributes", [])
                    attr_list = []
                    for attr in attributes:
                        options = " | ".join(attr.get("options", []))
                        attr_list.append(f"{attr['name']}: {options}")
                    row[column] = " | ".join(attr_list)
                else:
                    row[column] = product.get(column, "")
            
            export_data.append(row)
        
        # Generate export file
        if format.lower() == "csv":
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=export_columns)
            writer.writeheader()
            writer.writerows(export_data)
            file_content = output.getvalue()
            file_extension = "csv"
        
        elif format.lower() in ["xlsx", "excel"]:
            # For Excel export, would need additional libraries
            # For now, return CSV format
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=export_columns)
            writer.writeheader()
            writer.writerows(export_data)
            file_content = output.getvalue()
            file_extension = "csv"  # Would be xlsx in full implementation
        
        else:
            return {"error": "Unsupported export format"}
        
        return {
            "success": True,
            "format": format,
            "total_products": len(export_data),
            "columns": export_columns,
            "file_content": file_content,
            "file_extension": file_extension,
            "filters_applied": filters or {}
        }
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return {"error": str(e)}


def find_or_create_category(api_client, category_name: str) -> Optional[Dict[str, Any]]:
    """Find existing category or create new one"""
    
    try:
        # Search for existing category
        response = api_client.get("products/categories", params={"search": category_name})
        if response.status_code == 200:
            categories = response.json()
            for category in categories:
                if category.get("name", "").lower() == category_name.lower():
                    return category
        
        # Create new category
        category_data = {
            "name": category_name,
            "slug": category_name.lower().replace(" ", "-")
        }
        
        response = api_client.post("products/categories", category_data)
        if response.status_code in [200, 201]:
            return response.json()
    
    except Exception as e:
        logger.error(f"Error with category {category_name}: {e}")
    
    return None


def find_product_by_sku(api_client, sku: str) -> Optional[Dict[str, Any]]:
    """Find product by SKU"""
    
    try:
        response = api_client.get("products", params={"sku": sku})
        if response.status_code == 200:
            products = response.json()
            if products and len(products) > 0:
                return products[0]
    except Exception as e:
        logger.error(f"Error finding product by SKU {sku}: {e}")
    
    return None