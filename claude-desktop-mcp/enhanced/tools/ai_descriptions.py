"""
AI Description Generation Tools
Core tools for generating product descriptions using AI and stored templates
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

def generate_descriptions(sku_list: List[str], template_type: str = "auto", language: str = "en") -> Dict[str, Any]:
    """
    Tool 5: Generate AI-powered product descriptions using database templates
    
    Args:
        sku_list: List of SKUs to generate descriptions for
        template_type: Template type to use ("auto", "technical", "marketing", "basic")
        language: Language code for descriptions ("en", "no", "se", "dk")
    
    Returns:
        Generated descriptions with confidence scores and source data
    """
    try:
        results = {}
        summary = {
            "total_requested": len(sku_list),
            "successful_generations": 0,
            "failed_generations": 0,
            "template_used": template_type,
            "language": language
        }
        
        # Get AI template from database
        template_data = get_ai_template(template_type, language)
        if template_data.get("error"):
            return {"error": f"Failed to get AI template: {template_data['error']}"}
        
        for sku in sku_list:
            # Get consolidated data for the SKU
            from .data_consolidator import get_consolidated_data
            consolidated_data = get_consolidated_data(sku)
            
            if not consolidated_data:
                # Try to consolidate data first
                from .data_consolidator import consolidate_product_data
                consolidated_data = consolidate_product_data(sku)
                
                if consolidated_data.get("error"):
                    results[sku] = {
                        "error": f"No consolidated data available for SKU: {sku}",
                        "sku": sku
                    }
                    summary["failed_generations"] += 1
                    continue
            
            # Generate description
            description_result = generate_single_description(
                sku, 
                consolidated_data, 
                template_data, 
                language
            )
            
            results[sku] = description_result
            
            if description_result.get("error"):
                summary["failed_generations"] += 1
            else:
                summary["successful_generations"] += 1
                
                # Store generated description
                store_generated_description(sku, description_result)
        
        return {
            "success": True,
            "results": results,
            "summary": summary,
            "generation_date": datetime.now().isoformat(),
            "template_info": template_data.get("template_info", {})
        }
        
    except Exception as e:
        logger.error(f"Error generating descriptions: {e}")
        return {"error": str(e)}


def generate_single_description(sku: str, consolidated_data: Dict[str, Any], template_data: Dict[str, Any], language: str) -> Dict[str, Any]:
    """Generate description for a single SKU"""
    try:
        # Extract key data for description generation
        product_data = consolidated_data.get("consolidated_data", {})
        ai_ready_data = consolidated_data.get("ai_description_data", {})
        
        # Prepare description context
        context = {
            "sku": sku,
            "name": product_data.get("name", "").strip(),
            "category": product_data.get("category", "").strip(),
            "manufacturer": product_data.get("manufacturer", "").strip(),
            "specifications": product_data.get("specifications", {}),
            "price": product_data.get("price"),
            "existing_descriptions": []
        }
        
        # Add existing descriptions from sources
        for source_desc in ai_ready_data.get("source_descriptions", []):
            if source_desc.get("description"):
                context["existing_descriptions"].append({
                    "source": source_desc["source"],
                    "text": source_desc["description"]
                })
        
        # Generate description using template
        generated_description = apply_ai_template(context, template_data, language)
        
        # Calculate confidence score
        confidence_score = calculate_description_confidence(context, generated_description)
        
        return {
            "sku": sku,
            "generated_description": generated_description,
            "confidence_score": confidence_score,
            "template_type": template_data.get("template_type"),
            "language": language,
            "generation_date": datetime.now().isoformat(),
            "source_data_quality": consolidated_data.get("completeness_score", 0),
            "context_used": context
        }
        
    except Exception as e:
        logger.error(f"Error generating single description for {sku}: {e}")
        return {"error": str(e), "sku": sku}


def get_ai_template(template_type: str, language: str) -> Dict[str, Any]:
    """Get AI description template from database"""
    try:
        from .database_integration import query_database
        
        # Try to get specific template from database
        db_template = query_database('get_ai_template', {
            'template_type': template_type, 
            'language': language
        })
        
        if db_template and not db_template.get("error"):
            return db_template
        
        # Fallback to built-in templates
        return get_builtin_template(template_type, language)
        
    except Exception as e:
        logger.error(f"Error getting AI template: {e}")
        return {"error": str(e)}


def get_builtin_template(template_type: str, language: str) -> Dict[str, Any]:
    """Get built-in template as fallback"""
    
    builtin_templates = {
        "en": {
            "technical": {
                "template": """Generate a technical product description for {name} (SKU: {sku}).
                
Key Information:
- Category: {category}
- Manufacturer: {manufacturer}
- Specifications: {specifications}
- Price: {price}

Create a detailed technical description focusing on specifications and professional use cases.
Include key technical features and compatibility information.
Keep the tone professional and informative.""",
                "fields": ["name", "specifications", "manufacturer", "category"]
            },
            "marketing": {
                "template": """Create an engaging marketing description for {name} (SKU: {sku}).
                
Key Information:
- Category: {category}
- Manufacturer: {manufacturer}
- Key Features: {specifications}
- Price: {price}

Write a compelling product description that highlights benefits and appeals to customers.
Focus on what makes this product special and why customers should choose it.
Use persuasive but honest language.""",
                "fields": ["name", "category", "manufacturer", "price"]
            },
            "basic": {
                "template": """Create a basic product description for {name} (SKU: {sku}).
                
Product Details:
- Category: {category}
- Brand: {manufacturer}
- Price: {price}

Write a clear, concise description covering the essential product information.
Keep it factual and straightforward.""",
                "fields": ["name", "category", "manufacturer"]
            }
        }
    }
    
    # Auto-select template based on available data
    if template_type == "auto":
        template_type = "basic"  # Default fallback
    
    lang_templates = builtin_templates.get(language, builtin_templates["en"])
    selected_template = lang_templates.get(template_type, lang_templates["basic"])
    
    return {
        "template_type": template_type,
        "language": language,
        "template": selected_template["template"],
        "required_fields": selected_template["fields"],
        "template_info": {
            "source": "builtin",
            "template_id": f"{template_type}_{language}"
        }
    }


def apply_ai_template(context: Dict[str, Any], template_data: Dict[str, Any], language: str) -> str:
    """Apply AI template to generate description"""
    try:
        template = template_data.get("template", "")
        
        # Prepare template variables
        template_vars = {
            "sku": context.get("sku", ""),
            "name": context.get("name", "Unknown Product"),
            "category": context.get("category", "General"),
            "manufacturer": context.get("manufacturer", ""),
            "specifications": format_specifications(context.get("specifications", {})),
            "price": format_price(context.get("price"))
        }
        
        # Format existing descriptions if available
        existing_desc_text = ""
        if context.get("existing_descriptions"):
            existing_desc_text = "\n".join([
                f"From {desc['source']}: {desc['text']}"
                for desc in context["existing_descriptions"]
            ])
            template_vars["existing_descriptions"] = existing_desc_text
        
        # Apply template formatting
        try:
            description = template.format(**template_vars)
        except KeyError as e:
            # If template formatting fails, create basic description
            description = f"{template_vars['name']} (SKU: {template_vars['sku']}) - {template_vars['category']} from {template_vars['manufacturer']}"
        
        # Clean up and validate description
        description = description.strip()
        
        # Add fallback content if description is too short
        if len(description) < 50:
            description += f"\n\nThis {template_vars['category']} product from {template_vars['manufacturer']} "
            description += f"offers reliable performance and quality construction."
        
        return description
        
    except Exception as e:
        logger.error(f"Error applying AI template: {e}")
        # Return basic fallback description
        return f"{context.get('name', 'Product')} (SKU: {context.get('sku')}) - Quality product from {context.get('manufacturer', 'trusted manufacturer')}"


def format_specifications(specs: Dict[str, Any]) -> str:
    """Format specifications for template use"""
    if not specs or not isinstance(specs, dict):
        return "Specifications available upon request"
    
    formatted_specs = []
    for key, value in specs.items():
        if value:
            clean_key = str(key).replace("_", " ").title()
            formatted_specs.append(f"{clean_key}: {value}")
    
    return "; ".join(formatted_specs) if formatted_specs else "Specifications available upon request"


def format_price(price: Any) -> str:
    """Format price for template use"""
    if not price:
        return "Contact for pricing"
    
    try:
        price_num = float(price)
        return f"${price_num:.2f}"
    except (ValueError, TypeError):
        return str(price)


def calculate_description_confidence(context: Dict[str, Any], description: str) -> float:
    """Calculate confidence score for generated description"""
    score = 0.0
    
    # Base score for having essential data
    if context.get("name"):
        score += 0.3
    if context.get("category"):
        score += 0.2
    if context.get("manufacturer"):
        score += 0.2
    
    # Bonus for additional data
    if context.get("specifications"):
        score += 0.1
    if context.get("price"):
        score += 0.1
    if context.get("existing_descriptions"):
        score += 0.1
    
    # Description quality factors
    if len(description) > 100:
        score += 0.1
    if len(description) > 200:
        score += 0.1
    
    return min(score, 1.0)


def store_generated_description(sku: str, description_result: Dict[str, Any]) -> None:
    """Store generated description for review and use"""
    try:
        descriptions_folder = DOCUMENT_REPOSITORY / "_descriptions"
        descriptions_folder.mkdir(exist_ok=True)
        
        # Store with timestamp for audit trail
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sku}_{timestamp}.json"
        
        with open(descriptions_folder / filename, 'w') as f:
            json.dump(description_result, f, indent=2)
        
        # Also store as latest for quick access
        latest_filename = f"{sku}_latest.json"
        with open(descriptions_folder / latest_filename, 'w') as f:
            json.dump(description_result, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error storing generated description for {sku}: {e}")


def get_generated_description(sku: str) -> Optional[Dict[str, Any]]:
    """Retrieve latest generated description for SKU"""
    try:
        descriptions_folder = DOCUMENT_REPOSITORY / "_descriptions"
        latest_file = descriptions_folder / f"{sku}_latest.json"
        
        if latest_file.exists():
            with open(latest_file, 'r') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving generated description for {sku}: {e}")
        return None


def batch_review_descriptions(sku_list: List[str], action: str = "preview") -> Dict[str, Any]:
    """Review and manage generated descriptions in batch"""
    try:
        results = {}
        
        for sku in sku_list:
            description_data = get_generated_description(sku)
            
            if description_data:
                if action == "preview":
                    results[sku] = {
                        "description": description_data.get("generated_description", ""),
                        "confidence": description_data.get("confidence_score", 0),
                        "generation_date": description_data.get("generation_date", ""),
                        "status": "ready_for_review"
                    }
                elif action == "approve":
                    # Mark as approved (could update WooCommerce here)
                    results[sku] = {"status": "approved", "sku": sku}
                elif action == "regenerate":
                    # Trigger regeneration
                    regen_result = generate_descriptions([sku])
                    results[sku] = regen_result.get("results", {}).get(sku, {})
            else:
                results[sku] = {"error": f"No generated description found for {sku}"}
        
        return {
            "success": True,
            "action": action,
            "results": results,
            "processed_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch description review: {e}")
        return {"error": str(e)}


def list_available_templates() -> Dict[str, Any]:
    """List all available description templates"""
    try:
        # Get templates from database
        from .database_integration import query_database
        db_templates = query_database("SELECT template_type, language, description FROM ai_templates", {})
        
        available_templates = {
            "database_templates": [],
            "builtin_templates": ["technical", "marketing", "basic"],
            "supported_languages": ["en", "no", "se", "dk"]
        }
        
        if db_templates and not db_templates.get("error"):
            for row in db_templates.get("results", []):
                available_templates["database_templates"].append({
                    "type": row.get("template_type"),
                    "language": row.get("language"),
                    "description": row.get("description")
                })
        
        return {
            "success": True,
            "templates": available_templates,
            "query_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing available templates: {e}")
        return {"error": str(e)}