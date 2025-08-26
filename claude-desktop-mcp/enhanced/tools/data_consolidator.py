"""
Data Consolidation Tools
Core tool for consolidating product data from multiple sources by SKU
"""

import logging
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Document repository base path
DOCUMENT_REPOSITORY = Path(__file__).parent.parent.parent.parent / "document_repository"

def consolidate_product_data(sku: str, sources: List[str] = None) -> Dict[str, Any]:
    """
    Tool 7: Consolidate product data from multiple sources (database, Excel, catalogues)
    
    Args:
        sku: Product SKU to consolidate data for
        sources: List of data sources to include ["database", "excel", "catalogue", "all"]
    
    Returns:
        Consolidated product data with conflict resolution and completeness scoring
    """
    try:
        if sources is None:
            sources = ["all"]
        
        consolidated = {
            "sku": sku,
            "consolidation_date": datetime.now().isoformat(),
            "sources_checked": [],
            "data_found": {},
            "conflicts": [],
            "confidence_score": 0.0,
            "completeness_score": 0.0
        }
        
        # Collect data from all sources
        if "all" in sources or "database" in sources:
            db_data = get_database_data(sku)
            if db_data and not db_data.get("error"):
                consolidated["sources_checked"].append("database")
                consolidated["data_found"]["database"] = db_data
        
        if "all" in sources or "excel" in sources:
            excel_data = get_latest_excel_data(sku)
            if excel_data and not excel_data.get("error"):
                consolidated["sources_checked"].append("excel")
                consolidated["data_found"]["excel"] = excel_data
        
        if "all" in sources or "catalogue" in sources:
            catalogue_data = get_catalogue_data(sku)
            if catalogue_data and not catalogue_data.get("error"):
                consolidated["sources_checked"].append("catalogue")
                consolidated["data_found"]["catalogue"] = catalogue_data
        
        # If no data found, return early
        if not consolidated["data_found"]:
            consolidated["error"] = f"No data found for SKU: {sku}"
            return consolidated
        
        # Consolidate the data with conflict detection
        final_data = {}
        conflicts = []
        
        # Define field priority and consolidation rules
        field_priority = {
            "name": ["catalogue", "database", "excel"],
            "description": ["catalogue", "database", "excel"], 
            "price": ["excel", "database", "catalogue"],
            "cost": ["excel", "database", "catalogue"],
            "inventory": ["excel", "database", "catalogue"],
            "specifications": ["catalogue", "database", "excel"],
            "category": ["catalogue", "database", "excel"],
            "manufacturer": ["catalogue", "database", "excel"]
        }
        
        # Consolidate each field type
        for field, priority_sources in field_priority.items():
            values_found = {}
            
            # Collect values from all sources
            for source in consolidated["sources_checked"]:
                source_data = consolidated["data_found"][source]
                field_value = extract_field_value(source_data, field)
                if field_value is not None:
                    values_found[source] = field_value
            
            if values_found:
                # Apply priority-based consolidation
                final_value, conflict_info = resolve_field_conflicts(field, values_found, priority_sources)
                final_data[field] = final_value
                
                if conflict_info:
                    conflicts.append(conflict_info)
        
        # Calculate confidence and completeness scores
        confidence_score = calculate_confidence_score(final_data, consolidated["sources_checked"])
        completeness_score = calculate_completeness_score(final_data)
        
        # Generate AI description if we have enough data
        ai_description = None
        if completeness_score > 0.3:  # Only if we have reasonable data coverage
            ai_description = prepare_ai_description_data(final_data, consolidated["data_found"])
        
        # Build final consolidated result
        consolidated.update({
            "consolidated_data": final_data,
            "conflicts": conflicts,
            "confidence_score": confidence_score,
            "completeness_score": completeness_score,
            "ai_description_ready": ai_description is not None,
            "ai_description_data": ai_description,
            "recommendation": generate_consolidation_recommendation(confidence_score, completeness_score, conflicts)
        })
        
        # Store consolidated data for review
        store_consolidated_data(sku, consolidated)
        
        return consolidated
        
    except Exception as e:
        logger.error(f"Error consolidating data for SKU {sku}: {e}")
        return {"error": str(e), "sku": sku}


def get_database_data(sku: str) -> Optional[Dict[str, Any]]:
    """Get product data from SQL database"""
    try:
        from .database_integration import query_database
        return query_database('get_product', {'sku': sku})
    except Exception as e:
        logger.error(f"Error getting database data for {sku}: {e}")
        return {"error": str(e)}


def get_latest_excel_data(sku: str) -> Optional[Dict[str, Any]]:
    """Get latest Excel data for SKU from temp files"""
    try:
        temp_folder = DOCUMENT_REPOSITORY / "_temp"
        if not temp_folder.exists():
            return None
        
        # Find latest Excel import files
        excel_files = sorted(
            [f for f in temp_folder.glob("excel_import_*.json")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for excel_file in excel_files:
            with open(excel_file, 'r') as f:
                excel_data = json.load(f)
            
            processed_data = excel_data.get("processed_data", {})
            if sku in processed_data:
                return processed_data[sku]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting Excel data for {sku}: {e}")
        return {"error": str(e)}


def get_catalogue_data(sku: str) -> Optional[Dict[str, Any]]:
    """Get catalogue data for SKU from extracted catalogue files"""
    try:
        temp_folder = DOCUMENT_REPOSITORY / "_temp"
        if not temp_folder.exists():
            return None
        
        # Find latest catalogue extraction files
        catalogue_files = sorted(
            [f for f in temp_folder.glob("extracted_*.json")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for catalogue_file in catalogue_files:
            with open(catalogue_file, 'r') as f:
                catalogue_data = json.load(f)
            
            products = catalogue_data.get("products", {})
            if sku in products:
                return products[sku]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting catalogue data for {sku}: {e}")
        return {"error": str(e)}


def extract_field_value(source_data: Dict[str, Any], field: str) -> Any:
    """Extract specific field value from source data"""
    
    # Check if this is database integration format (has product_data sub-object)
    product_data = source_data.get("product_data", {})
    
    # Direct field mapping (check both main data and product_data)
    if field in source_data:
        return source_data[field]
    if field in product_data:
        return product_data[field]
    
    # Field-specific extraction logic
    if field == "name":
        return (source_data.get("name") or 
                source_data.get("product_name") or 
                source_data.get("title") or
                # Database format fields
                product_data.get("model") or
                f"{product_data.get('brand', '')} {product_data.get('model', '')}".strip())
    
    elif field == "description":
        return (source_data.get("description") or 
                source_data.get("product_description") or 
                source_data.get("short_description") or
                # Build description from database fields
                build_description_from_product_data(product_data))
    
    elif field == "price":
        pricing = source_data.get("pricing", {})
        return (pricing.get("retail_price") or 
                pricing.get("price") or 
                pricing.get("msrp") or
                source_data.get("price") or
                # Database format fields
                product_data.get("price_fi") or
                product_data.get("price"))
    
    elif field == "cost":
        pricing = source_data.get("pricing", {})
        return (pricing.get("cost_price") or 
                pricing.get("wholesale_price") or
                pricing.get("cost"))
    
    elif field == "inventory":
        inventory = source_data.get("inventory", {})
        return (inventory.get("stock_quantity") or 
                inventory.get("available") or
                inventory.get("qty") or
                source_data.get("stock"))
    
    elif field == "specifications":
        return (source_data.get("specifications") or 
                source_data.get("specs") or 
                source_data.get("technical_specs") or
                # Build specs from database fields
                build_specifications_from_product_data(product_data))
    
    elif field == "category":
        return (source_data.get("category") or 
                source_data.get("product_category") or 
                source_data.get("type") or
                # Database format fields
                determine_category_from_product_data(product_data))
    
    elif field == "manufacturer":
        return (source_data.get("manufacturer") or 
                source_data.get("brand") or 
                source_data.get("supplier") or
                # Database format fields
                product_data.get("brand"))
    
    return None


def build_description_from_product_data(product_data: Dict[str, Any]) -> str:
    """Build description from database product fields"""
    if not product_data:
        return ""
    
    parts = []
    
    # Add basic info
    brand = product_data.get("brand", "")
    model = product_data.get("model", "")
    year = product_data.get("year", "")
    
    if brand and model:
        base = f"{brand} {model}"
        if year:
            base += f" ({year})"
        parts.append(base)
    
    # Add technical specs
    engine = product_data.get("engine", "")
    if engine:
        parts.append(f"Engine: {engine}")
    
    track = product_data.get("track", "")
    if track:
        parts.append(f"Track: {track}")
    
    starter = product_data.get("starter", "")
    if starter:
        parts.append(f"Starter: {starter}")
    
    color = product_data.get("color", "")
    if color:
        parts.append(f"Color: {color}")
    
    return ". ".join(parts) if parts else ""


def build_specifications_from_product_data(product_data: Dict[str, Any]) -> Dict[str, str]:
    """Build specifications dict from database product fields"""
    if not product_data:
        return {}
    
    specs = {}
    
    # Map database fields to specification fields
    spec_mapping = {
        "engine": "Engine",
        "track": "Track",
        "starter": "Starter Type",
        "gauge": "Gauge",
        "color": "Color",
        "year": "Model Year",
        "package": "Package"
    }
    
    for db_field, spec_name in spec_mapping.items():
        value = product_data.get(db_field)
        if value and str(value).strip():
            specs[spec_name] = str(value).strip()
    
    return specs


def determine_category_from_product_data(product_data: Dict[str, Any]) -> str:
    """Determine product category from database fields"""
    if not product_data:
        return ""
    
    brand = product_data.get("brand", "").upper()
    model = product_data.get("model", "").lower()
    
    # Category mapping based on brand/model patterns
    if brand in ["SKIDOO", "SKI-DOO", "LYNX"]:
        if "expedition" in model:
            return "Snowmobile - Touring"
        elif "summit" in model:
            return "Snowmobile - Mountain"
        elif "renegade" in model or "backcountry" in model:
            return "Snowmobile - Trail"
        elif "ranger" in model:
            return "Snowmobile - Utility"
        else:
            return "Snowmobile"
    
    return "Powersport Vehicle"


def resolve_field_conflicts(field: str, values_found: Dict[str, Any], priority_sources: List[str]) -> tuple:
    """Resolve conflicts between different source values"""
    
    if len(values_found) <= 1:
        # No conflict
        source, value = next(iter(values_found.items()))
        return value, None
    
    # Check if all values are the same
    unique_values = set(str(v) for v in values_found.values())
    if len(unique_values) == 1:
        # Same value from all sources
        return list(values_found.values())[0], None
    
    # Conflict detected - apply priority resolution
    for priority_source in priority_sources:
        if priority_source in values_found:
            conflict_info = {
                "field": field,
                "chosen_source": priority_source,
                "chosen_value": values_found[priority_source],
                "conflicting_values": {k: v for k, v in values_found.items() if k != priority_source}
            }
            return values_found[priority_source], conflict_info
    
    # Fallback - use first available value
    source, value = next(iter(values_found.items()))
    conflict_info = {
        "field": field,
        "chosen_source": source,
        "chosen_value": value,
        "conflicting_values": {k: v for k, v in values_found.items() if k != source},
        "resolution_method": "fallback"
    }
    return value, conflict_info


def calculate_confidence_score(final_data: Dict[str, Any], sources_checked: List[str]) -> float:
    """Calculate confidence score based on data sources and coverage"""
    
    # Base score from number of sources
    source_score = len(sources_checked) / 3.0  # Max 3 sources
    
    # Data coverage score
    required_fields = ["name", "price", "description"]
    optional_fields = ["cost", "inventory", "specifications", "category", "manufacturer"]
    
    required_coverage = sum(1 for field in required_fields if final_data.get(field)) / len(required_fields)
    optional_coverage = sum(1 for field in optional_fields if final_data.get(field)) / len(optional_fields)
    
    coverage_score = (required_coverage * 0.7) + (optional_coverage * 0.3)
    
    # Final confidence score
    confidence = (source_score * 0.4) + (coverage_score * 0.6)
    return min(confidence, 1.0)


def calculate_completeness_score(final_data: Dict[str, Any]) -> float:
    """Calculate data completeness score"""
    
    required_fields = ["name", "sku", "price", "description"]
    optional_fields = ["specifications", "category", "manufacturer", "cost", "inventory"]
    
    total_fields = len(required_fields) + len(optional_fields)
    filled_fields = 0
    
    # Required fields (weight: 2x)
    for field in required_fields:
        if final_data.get(field):
            filled_fields += 2
    
    # Optional fields (weight: 1x)
    for field in optional_fields:
        if final_data.get(field):
            filled_fields += 1
    
    max_score = (len(required_fields) * 2) + len(optional_fields)
    return filled_fields / max_score if max_score > 0 else 0


def prepare_ai_description_data(final_data: Dict[str, Any], source_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for AI description generation"""
    
    ai_data = {
        "sku": final_data.get("sku"),
        "name": final_data.get("name"),
        "category": final_data.get("category"),
        "manufacturer": final_data.get("manufacturer"),
        "specifications": final_data.get("specifications"),
        "existing_description": final_data.get("description"),
        "price_info": {
            "retail_price": final_data.get("price"),
            "cost_price": final_data.get("cost")
        },
        "source_descriptions": []
    }
    
    # Collect any existing descriptions from sources
    for source, data in source_data.items():
        desc = extract_field_value(data, "description")
        if desc:
            ai_data["source_descriptions"].append({
                "source": source,
                "description": desc
            })
    
    return ai_data


def generate_consolidation_recommendation(confidence_score: float, completeness_score: float, conflicts: List[Dict]) -> str:
    """Generate recommendation based on consolidation results"""
    
    if confidence_score >= 0.8 and completeness_score >= 0.7 and len(conflicts) <= 1:
        return "HIGH_CONFIDENCE - Ready for automated processing"
    
    elif confidence_score >= 0.6 and completeness_score >= 0.5:
        return "MEDIUM_CONFIDENCE - Review recommended before processing"
    
    elif len(conflicts) > 3:
        return "HIGH_CONFLICTS - Manual review required"
    
    elif completeness_score < 0.3:
        return "LOW_DATA_COVERAGE - Additional data sources needed"
    
    else:
        return "LOW_CONFIDENCE - Manual review required"


def store_consolidated_data(sku: str, consolidated_data: Dict[str, Any]) -> None:
    """Store consolidated data for review and audit trail"""
    try:
        consolidated_folder = DOCUMENT_REPOSITORY / "_consolidated"
        consolidated_folder.mkdir(exist_ok=True)
        
        # Store with timestamp for audit trail
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sku}_{timestamp}.json"
        
        with open(consolidated_folder / filename, 'w') as f:
            json.dump(consolidated_data, f, indent=2)
        
        # Also store as latest for quick access
        latest_filename = f"{sku}_latest.json"
        with open(consolidated_folder / latest_filename, 'w') as f:
            json.dump(consolidated_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error storing consolidated data for {sku}: {e}")


def get_consolidated_data(sku: str) -> Optional[Dict[str, Any]]:
    """Retrieve latest consolidated data for SKU"""
    try:
        consolidated_folder = DOCUMENT_REPOSITORY / "_consolidated"
        latest_file = consolidated_folder / f"{sku}_latest.json"
        
        if latest_file.exists():
            with open(latest_file, 'r') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving consolidated data for {sku}: {e}")
        return None


def batch_consolidate_products(sku_list: List[str], sources: List[str] = None) -> Dict[str, Any]:
    """Consolidate data for multiple SKUs in batch"""
    try:
        results = {}
        summary = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "high_confidence": 0,
            "needs_review": 0
        }
        
        for sku in sku_list:
            result = consolidate_product_data(sku, sources)
            results[sku] = result
            
            summary["total_processed"] += 1
            
            if result.get("error"):
                summary["failed"] += 1
            else:
                summary["successful"] += 1
                
                if result.get("confidence_score", 0) >= 0.8:
                    summary["high_confidence"] += 1
                else:
                    summary["needs_review"] += 1
        
        return {
            "success": True,
            "batch_results": results,
            "summary": summary,
            "processing_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch consolidation: {e}")
        return {"error": str(e)}