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
    """Get AI description template from database - Enhanced with Avito integration"""
    try:
        from .database_integration import query_database
        
        # First try to get Avito template if available
        avito_template = get_avito_template(template_type, language)
        if avito_template and not avito_template.get("error"):
            return avito_template
        
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


def get_avito_template(template_type: str, language: str) -> Optional[Dict[str, Any]]:
    """Get Avito template from database with full XML generation capability"""
    try:
        import sqlite3
        
        # Use direct connection to the database
        conn = sqlite3.connect('C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository/_temp/Snowmobile.db')
        if not conn:
            return {"error": "Database connection failed"}
        
        cursor = conn.cursor()
        
        # Get Avito template data
        cursor.execute("""
            SELECT template_name, template_version, template_purpose, 
                   header_section, availability_section, product_description_section, 
                   call_to_action_section, gpt_system_prompt, gpt_structure_template,
                   complete_xml_template, availability_mappings, business_rules
            FROM avito_description_templates 
            ORDER BY id DESC LIMIT 1
        """)
        
        template_row = cursor.fetchone()
        if not template_row:
            return {"error": "No Avito templates found"}
        
        conn.close()
        
        return {
            "template_type": "avito_complete",
            "language": language,
            "template_name": template_row[0],
            "template_version": template_row[1],
            "template_purpose": template_row[2],
            "gpt_system_prompt": template_row[7],
            "gpt_structure_template": template_row[8],
            "complete_xml_template": template_row[9],
            "sections": {
                "header": template_row[3],
                "availability": template_row[4], 
                "description": template_row[5],
                "call_to_action": template_row[6]
            },
            "availability_mappings": json.loads(template_row[10]) if template_row[10] else {},
            "business_rules": json.loads(template_row[11]) if template_row[11] else {},
            "template_info": {
                "source": "avito_database",
                "template_id": f"avito_{template_row[0]}_{template_row[1]}"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting Avito template: {e}")
        return {"error": str(e)}


def generate_avito_xml_description(sku: str, template_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate complete Avito XML description using existing database template"""
    try:
        import sqlite3
        
        # Use direct connection to the database
        conn = sqlite3.connect('C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository/_temp/Snowmobile.db')
        if not conn:
            return {"error": "Database connection failed"}
        
        # Get existing article_complete data for this SKU
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles_complete WHERE article_code = ?", (sku,))
        article_row = cursor.fetchone()
        
        if not article_row:
            return {"error": f"No article_complete data found for SKU: {sku}"}
        
        # Get column names
        cursor.execute("PRAGMA table_info(articles_complete)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Create article data dictionary
        article_data = dict(zip(columns, article_row))
        
        conn.close()
        
        # Extract Avito-specific fields
        avito_fields = {
            "title": article_data.get("avito_title", ""),
            "year": article_data.get("avito_year", ""),
            "engine_type": article_data.get("avito_engine_type", ""),
            "power": article_data.get("avito_power", ""),
            "engine_capacity": article_data.get("avito_engine_capacity", ""),
            "track_width": article_data.get("avito_track_width", ""),
            "stroke": article_data.get("avito_stroke", ""),
            "weight": article_data.get("avito_weight_for_delivery", ""),
            "length": article_data.get("avito_length_for_delivery", ""),
            "height": article_data.get("avito_height_for_delivery", ""),
            "width": article_data.get("avito_width_for_delivery", ""),
            "color": article_data.get("avito_color", ""),
            "gauge_type": article_data.get("avito_gauge_type", "")
        }
        
        # Get template fields
        template_fields = {
            "engine": json.loads(article_data.get("template_engine", "{}")) if article_data.get("template_engine") else {},
            "track": json.loads(article_data.get("template_track", "{}")) if article_data.get("template_track") else {},
            "front_suspension": article_data.get("template_front_suspension", ""),
            "rear_suspension": article_data.get("template_rear_suspension", ""),
            "brake_system": article_data.get("template_brake_system", ""),
            "platform": article_data.get("template_platform", ""),
            "seating": article_data.get("template_seating", ""),
            "dry_weight": article_data.get("template_dry_weight", "")
        }
        
        # Use existing generated content if available
        existing_description = article_data.get("generated_description", "")
        existing_xml = article_data.get("generated_xml", "")
        
        # Generate new description using GPT template if needed
        if template_data.get("gpt_system_prompt") and template_data.get("gpt_structure_template"):
            gpt_context = {
                "sku": sku,
                "article_data": article_data,
                "avito_fields": avito_fields,
                "template_fields": template_fields,
                "kb_data": {
                    "marketing_description": article_data.get("kb_marketing_description", ""),
                    "features": json.loads(article_data.get("kb_features", "[]")) if article_data.get("kb_features") else [],
                    "specifications": {
                        "engine_options": json.loads(article_data.get("kb_engine_options", "[]")) if article_data.get("kb_engine_options") else [],
                        "track_options": json.loads(article_data.get("kb_track_options", "[]")) if article_data.get("kb_track_options") else [],
                        "dimensions": json.loads(article_data.get("kb_dimensions", "{}")) if article_data.get("kb_dimensions") else {}
                    }
                }
            }
            
            # Apply GPT template (simulate AI generation)
            generated_description = apply_avito_gpt_template(
                template_data.get("gpt_system_prompt"),
                template_data.get("gpt_structure_template"), 
                gpt_context
            )
        else:
            generated_description = existing_description or f"Professional {article_data.get('article_brand', '')} {article_data.get('article_model', '')} snowmobile"
        
        # Generate XML using complete template
        xml_content = generate_avito_xml_content(
            template_data.get("complete_xml_template", ""),
            sku,
            avito_fields,
            template_fields,
            generated_description,
            article_data
        )
        
        return {
            "sku": sku,
            "generated_description": generated_description,
            "generated_xml": xml_content,
            "avito_fields": avito_fields,
            "template_fields": template_fields,
            "article_data_used": bool(article_data),
            "existing_content_found": bool(existing_description or existing_xml),
            "template_source": template_data.get("template_info", {}).get("source", "unknown"),
            "generation_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating Avito XML description for {sku}: {e}")
        return {"error": str(e)}


def apply_avito_gpt_template(system_prompt: str, structure_template: str, context: Dict[str, Any]) -> str:
    """Apply Avito GPT template to generate structured description"""
    try:
        # Simulate GPT processing using the structured template
        article_data = context.get("article_data", {})
        avito_fields = context.get("avito_fields", {})
        kb_data = context.get("kb_data", {})
        
        # Extract key information for description
        brand = article_data.get("article_brand", "")
        model = article_data.get("article_model", "") 
        year = article_data.get("article_year", "")
        engine = avito_fields.get("engine_type", "")
        power = avito_fields.get("power", "")
        
        # Build structured description
        description_parts = []
        
        # Title section
        if brand and model:
            title = f"{brand} {model}"
            if year:
                title += f" {year}"
            description_parts.append(f"**{title}**")
        
        # Technical specifications
        if engine or power:
            tech_specs = []
            if engine:
                tech_specs.append(f"Engine: {engine}")
            if power:
                tech_specs.append(f"Power: {power}")
            
            if tech_specs:
                description_parts.append("Technical Specifications:")
                description_parts.extend([f"• {spec}" for spec in tech_specs])
        
        # Features from knowledge base
        features = kb_data.get("features", [])
        if features:
            description_parts.append("Key Features:")
            description_parts.extend([f"• {feature}" for feature in features[:5]])  # Limit to 5 features
        
        # Marketing description
        marketing_desc = kb_data.get("marketing_description", "")
        if marketing_desc and len(marketing_desc) > 20:
            description_parts.append(f"\n{marketing_desc}")
        
        # Professional availability note
        description_parts.append("\nProfessional snowmobile with genuine parts and warranty support.")
        
        generated_description = "\n\n".join(description_parts)
        
        # Ensure minimum length
        if len(generated_description) < 100:
            generated_description += f"\n\nThis {brand} {model} represents quality engineering and reliable performance for professional and recreational use."
        
        return generated_description
        
    except Exception as e:
        logger.error(f"Error applying Avito GPT template: {e}")
        return f"Professional snowmobile - {context.get('sku', 'product')} with complete specifications and warranty support."


def generate_avito_xml_content(xml_template: str, sku: str, avito_fields: Dict[str, Any], 
                              template_fields: Dict[str, Any], description: str, 
                              article_data: Dict[str, Any]) -> str:
    """Generate Avito XML content using complete template"""
    try:
        if not xml_template:
            return create_basic_avito_xml(sku, avito_fields, description)
        
        # Prepare template variables
        template_vars = {
            "sku": sku,
            "title": avito_fields.get("title", f"{article_data.get('article_brand', '')} {article_data.get('article_model', '')}"),
            "description": description,
            "year": avito_fields.get("year", article_data.get("article_year", "")),
            "engine_type": avito_fields.get("engine_type", ""),
            "power": avito_fields.get("power", ""),
            "engine_capacity": avito_fields.get("engine_capacity", ""),
            "track_width": avito_fields.get("track_width", ""),
            "weight": avito_fields.get("weight", ""),
            "length": avito_fields.get("length", ""),
            "height": avito_fields.get("height", ""),
            "width": avito_fields.get("width", ""),
            "color": avito_fields.get("color", ""),
            "price": article_data.get("article_price_fi", "Contact for pricing"),
            "brand": article_data.get("article_brand", ""),
            "model": article_data.get("article_model", ""),
            "condition": "New",  # Assuming new products
            "availability": "In Stock"  # Default availability
        }
        
        # Apply template formatting
        try:
            xml_content = xml_template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Template formatting error: {e}, using basic XML")
            return create_basic_avito_xml(sku, avito_fields, description)
        
        return xml_content
        
    except Exception as e:
        logger.error(f"Error generating Avito XML content: {e}")
        return create_basic_avito_xml(sku, avito_fields, description)


def create_basic_avito_xml(sku: str, avito_fields: Dict[str, Any], description: str) -> str:
    """Create basic Avito XML as fallback"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ad>
    <sku>{sku}</sku>
    <title>{avito_fields.get('title', 'Snowmobile')}</title>
    <description><![CDATA[{description}]]></description>
    <category>Transport</category>
    <subcategory>Snowmobiles</subcategory>
    <condition>New</condition>
    <availability>In Stock</availability>
</ad>"""


def regenerate_all_avito_descriptions(sku_filter: List[str] = None) -> Dict[str, Any]:
    """Regenerate all Avito descriptions for SKUs in price lists using document repository data"""
    try:
        import sqlite3
        
        # Use direct connection to the database
        conn = sqlite3.connect('C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository/_temp/Snowmobile.db')
        if not conn:
            return {"error": "Database connection failed"}
        
        cursor = conn.cursor()
        
        # Get SKUs to process
        if sku_filter:
            placeholders = ",".join(["?" for _ in sku_filter])
            cursor.execute(f"SELECT article_code FROM articles_complete WHERE article_code IN ({placeholders})", sku_filter)
        else:
            # Get all SKUs that have price list data
            cursor.execute("SELECT article_code FROM articles_complete WHERE article_price_fi IS NOT NULL AND article_price_fi != ''")
        
        skus_to_process = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not skus_to_process:
            return {"error": "No SKUs found with price list data"}
        
        # Get Avito template
        avito_template = get_avito_template("avito", "en")
        if not avito_template or avito_template.get("error"):
            return {"error": f"Failed to get Avito template: {avito_template.get('error') if avito_template else 'Template not found'}"}
        
        # Process each SKU
        results = {}
        summary = {
            "total_processed": len(skus_to_process),
            "successful_generations": 0,
            "failed_generations": 0,
            "template_used": avito_template.get("template_name", "unknown"),
            "processing_date": datetime.now().isoformat()
        }
        
        for sku in skus_to_process:
            try:
                # Generate Avito XML description
                result = generate_avito_xml_description(sku, avito_template, {})
                
                if result.get("error"):
                    results[sku] = {"error": result["error"]}
                    summary["failed_generations"] += 1
                else:
                    results[sku] = {
                        "description": result.get("generated_description", ""),
                        "xml": result.get("generated_xml", ""),
                        "status": "success"
                    }
                    summary["successful_generations"] += 1
                    
                    # Update database with new content
                    update_article_complete_content(sku, result)
                    
            except Exception as e:
                results[sku] = {"error": str(e)}
                summary["failed_generations"] += 1
        
        return {
            "success": True,
            "results": results,
            "summary": summary,
            "message": f"Processed {len(skus_to_process)} SKUs using all available document repository data"
        }
        
    except Exception as e:
        logger.error(f"Error in regenerate_all_avito_descriptions: {e}")
        return {"error": str(e)}


def update_article_complete_content(sku: str, generation_result: Dict[str, Any]) -> bool:
    """Update articles_complete table with newly generated content"""
    try:
        import sqlite3
        
        # Use direct connection to the database
        conn = sqlite3.connect('C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository/_temp/Snowmobile.db')
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Update the article with new generated content
        cursor.execute("""
            UPDATE articles_complete 
            SET generated_description = ?,
                generated_xml = ?,
                processing_status = 'completed',
                last_description_generation_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP,
                version = version + 1
            WHERE article_code = ?
        """, (
            generation_result.get("generated_description", ""),
            generation_result.get("generated_xml", ""),
            sku
        ))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Error updating article_complete content for {sku}: {e}")
        return False


def list_available_templates() -> Dict[str, Any]:
    """List all available description templates - Enhanced with Avito templates"""
    try:
        # Get templates from database
        from .database_integration import query_database, get_database_connection
        
        available_templates = {
            "avito_templates": [],
            "database_templates": [],
            "builtin_templates": ["technical", "marketing", "basic", "avito"],
            "supported_languages": ["en", "no", "se", "dk"]
        }
        
        # Get Avito templates
        try:
            import sqlite3
            conn = sqlite3.connect('C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository/_temp/Snowmobile.db')
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT template_name, template_version, template_purpose FROM avito_description_templates")
                avito_rows = cursor.fetchall()
                
                for row in avito_rows:
                    available_templates["avito_templates"].append({
                        "name": row[0],
                        "version": row[1],
                        "purpose": row[2],
                        "type": "avito_xml_generation"
                    })
                
                conn.close()
        except Exception as e:
            logger.warning(f"Could not fetch Avito templates: {e}")
        
        # Get regular templates
        db_templates = query_database("SELECT template_type, language, description FROM ai_templates", {})
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