"""
SEO and Marketing Integration Tools
Complete SEO optimization and marketing tool integration
"""

import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def manage_seo_settings(api_client, seo_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure and optimize SEO settings for the store"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        action = seo_config.get("action", "audit")
        
        if action == "audit":
            # Perform comprehensive SEO audit
            audit_results = {
                "overall_score": 0,
                "critical_issues": [],
                "warnings": [],
                "recommendations": [],
                "technical_seo": {},
                "on_page_seo": {},
                "product_seo": {},
                "content_seo": {}
            }
            
            # Technical SEO checks
            technical_issues = []
            technical_score = 0
            
            # Check store configuration
            try:
                system_response = api_client.get("system_status")
                if system_response.status_code == 200:
                    system_data = system_response.json()
                    
                    # SSL check
                    site_url = system_data.get("environment", {}).get("site_url", "")
                    if site_url.startswith("https://"):
                        technical_score += 15
                    else:
                        technical_issues.append("Site not using HTTPS - critical for SEO and security")
                    
                    # Theme check
                    theme_info = system_data.get("theme", {})
                    if theme_info:
                        technical_score += 10
                        audit_results["technical_seo"]["theme"] = {
                            "name": theme_info.get("name"),
                            "version": theme_info.get("version"),
                            "mobile_responsive": True  # Assume modern themes are responsive
                        }
            
            except Exception as e:
                technical_issues.append(f"Could not verify technical configuration: {str(e)}")
            
            # Product SEO analysis
            product_seo_score = 0
            try:
                products_response = api_client.get("products", params={"per_page": 20})
                if products_response.status_code == 200:
                    products = products_response.json()
                    
                    products_with_seo = 0
                    products_missing_descriptions = 0
                    products_missing_images = 0
                    
                    for product in products:
                        has_description = bool(product.get("description", "").strip())
                        has_images = len(product.get("images", [])) > 0
                        has_meta_description = bool(product.get("short_description", "").strip())
                        
                        if has_description and has_images and has_meta_description:
                            products_with_seo += 1
                        
                        if not has_description:
                            products_missing_descriptions += 1
                        
                        if not has_images:
                            products_missing_images += 1
                    
                    if products:
                        seo_completion_rate = (products_with_seo / len(products)) * 100
                        product_seo_score = min(30, (seo_completion_rate / 100) * 30)
                        
                        audit_results["product_seo"] = {
                            "total_products_checked": len(products),
                            "seo_optimized_products": products_with_seo,
                            "missing_descriptions": products_missing_descriptions,
                            "missing_images": products_missing_images,
                            "seo_completion_rate": f"{seo_completion_rate:.1f}%"
                        }
                        
                        if products_missing_descriptions > 0:
                            audit_results["warnings"].append(f"{products_missing_descriptions} products missing descriptions")
                        
                        if products_missing_images > 0:
                            audit_results["warnings"].append(f"{products_missing_images} products missing images")
            
            except Exception as e:
                audit_results["warnings"].append(f"Could not analyze product SEO: {str(e)}")
            
            # Category SEO analysis
            try:
                categories_response = api_client.get("products/categories", params={"per_page": 50})
                if categories_response.status_code == 200:
                    categories = categories_response.json()
                    
                    categories_with_descriptions = sum(1 for cat in categories if cat.get("description", "").strip())
                    
                    if categories:
                        category_seo_rate = (categories_with_descriptions / len(categories)) * 100
                        product_seo_score += min(15, (category_seo_rate / 100) * 15)
                        
                        audit_results["product_seo"]["categories"] = {
                            "total_categories": len(categories),
                            "with_descriptions": categories_with_descriptions,
                            "description_rate": f"{category_seo_rate:.1f}%"
                        }
            
            except Exception as e:
                audit_results["warnings"].append(f"Could not analyze category SEO: {str(e)}")
            
            # Generate recommendations
            if technical_score < 20:
                audit_results["critical_issues"].append("Technical SEO issues need immediate attention")
            
            if product_seo_score < 30:
                audit_results["recommendations"].extend([
                    "Add detailed descriptions to all products",
                    "Include high-quality images for all products",
                    "Write compelling meta descriptions for products",
                    "Optimize product titles with relevant keywords"
                ])
            
            # Calculate overall score
            audit_results["overall_score"] = technical_score + product_seo_score
            audit_results["technical_seo"]["score"] = technical_score
            audit_results["technical_seo"]["issues"] = technical_issues
            
            # Add general recommendations
            audit_results["recommendations"].extend([
                "Set up Google Search Console for monitoring",
                "Create and submit XML sitemap",
                "Optimize page loading speed",
                "Implement structured data markup",
                "Build quality backlinks"
            ])
            
            return audit_results
        
        elif action == "optimize_products":
            # Optimize product SEO
            optimization_config = seo_config.get("optimization", {})
            
            # Get products to optimize
            products_response = api_client.get("products", params={"per_page": 50})
            if products_response.status_code != 200:
                return {"error": "Could not fetch products for optimization"}
            
            products = products_response.json()
            optimization_results = {
                "optimized_products": 0,
                "skipped_products": 0,
                "failed_optimizations": 0,
                "optimizations_applied": [],
                "errors": []
            }
            
            for product in products:
                try:
                    product_id = product.get("id")
                    updates_needed = {}
                    optimizations = []
                    
                    # Optimize title
                    current_title = product.get("name", "")
                    if len(current_title) < 30:
                        # Suggest title optimization
                        optimizations.append("Title too short - consider adding descriptive keywords")
                    elif len(current_title) > 60:
                        optimizations.append("Title too long - may be truncated in search results")
                    
                    # Optimize description
                    if not product.get("description", "").strip():
                        optimizations.append("Missing product description")
                    elif len(product.get("description", "")) < 100:
                        optimizations.append("Product description too short - aim for 150-300 words")
                    
                    # Optimize short description (meta description)
                    short_desc = product.get("short_description", "")
                    if not short_desc.strip():
                        # Generate basic short description
                        if optimization_config.get("auto_generate_descriptions"):
                            categories = product.get("categories", [])
                            category_names = [cat.get("name", "") for cat in categories]
                            generated_desc = f"High-quality {current_title.lower()}"
                            if category_names:
                                generated_desc += f" in {', '.join(category_names[:2])}"
                            generated_desc += f". Starting at {product.get('price', 'N/A')}."
                            
                            updates_needed["short_description"] = generated_desc
                            optimizations.append("Generated meta description")
                    elif len(short_desc) > 160:
                        optimizations.append("Meta description too long - should be under 160 characters")
                    
                    # Check for images
                    if not product.get("images"):
                        optimizations.append("Missing product images - critical for SEO")
                    else:
                        # Check image alt text (would need additional API calls)
                        optimizations.append("Verify image alt text is optimized")
                    
                    # Apply updates if any
                    if updates_needed and optimization_config.get("apply_changes", False):
                        update_response = api_client.put(f"products/{product_id}", updates_needed)
                        if update_response.status_code in [200, 201]:
                            optimization_results["optimized_products"] += 1
                        else:
                            optimization_results["failed_optimizations"] += 1
                            optimization_results["errors"].append(f"Failed to update product {product_id}")
                    else:
                        optimization_results["skipped_products"] += 1
                    
                    if optimizations:
                        optimization_results["optimizations_applied"].append({
                            "product_id": product_id,
                            "product_name": current_title,
                            "recommendations": optimizations
                        })
                
                except Exception as e:
                    optimization_results["failed_optimizations"] += 1
                    optimization_results["errors"].append(f"Error optimizing product {product.get('id')}: {str(e)}")
            
            return optimization_results
        
        elif action == "generate_sitemap":
            # Generate XML sitemap data
            sitemap_data = {
                "sitemap_info": {
                    "generated_at": datetime.now().isoformat(),
                    "total_urls": 0,
                    "url_types": {}
                },
                "urls": []
            }
            
            # Add products to sitemap
            try:
                products_response = api_client.get("products", params={"per_page": 100, "status": "publish"})
                if products_response.status_code == 200:
                    products = products_response.json()
                    
                    for product in products:
                        sitemap_data["urls"].append({
                            "loc": product.get("permalink", ""),
                            "lastmod": product.get("date_modified", ""),
                            "changefreq": "weekly",
                            "priority": "0.8",
                            "type": "product"
                        })
                    
                    sitemap_data["sitemap_info"]["url_types"]["products"] = len(products)
                    sitemap_data["sitemap_info"]["total_urls"] += len(products)
            
            except Exception as e:
                logger.warning(f"Could not include products in sitemap: {e}")
            
            # Add categories to sitemap
            try:
                categories_response = api_client.get("products/categories", params={"per_page": 100})
                if categories_response.status_code == 200:
                    categories = categories_response.json()
                    
                    for category in categories:
                        if category.get("count", 0) > 0:  # Only include categories with products
                            sitemap_data["urls"].append({
                                "loc": f"/product-category/{category.get('slug', '')}/",
                                "lastmod": datetime.now().isoformat(),
                                "changefreq": "weekly",
                                "priority": "0.6",
                                "type": "category"
                            })
                    
                    active_categories = sum(1 for cat in categories if cat.get("count", 0) > 0)
                    sitemap_data["sitemap_info"]["url_types"]["categories"] = active_categories
                    sitemap_data["sitemap_info"]["total_urls"] += active_categories
            
            except Exception as e:
                logger.warning(f"Could not include categories in sitemap: {e}")
            
            return sitemap_data
        
        elif action == "structured_data":
            # Generate structured data markup
            structured_data_config = seo_config.get("structured_data", {})
            
            markup_results = {
                "generated_schemas": [],
                "product_schemas": 0,
                "organization_schema": None,
                "website_schema": None
            }
            
            # Generate Organization schema
            business_info = structured_data_config.get("business_info", {})
            if business_info:
                org_schema = {
                    "@context": "https://schema.org",
                    "@type": "Organization",
                    "name": business_info.get("name", ""),
                    "url": business_info.get("website", ""),
                    "logo": business_info.get("logo", ""),
                    "contactPoint": {
                        "@type": "ContactPoint",
                        "telephone": business_info.get("phone", ""),
                        "contactType": "customer service"
                    },
                    "address": {
                        "@type": "PostalAddress",
                        "streetAddress": business_info.get("address", ""),
                        "addressCountry": business_info.get("country", "")
                    }
                }
                markup_results["organization_schema"] = org_schema
                markup_results["generated_schemas"].append("Organization")
            
            # Generate Product schemas for sample products
            try:
                products_response = api_client.get("products", params={"per_page": 10})
                if products_response.status_code == 200:
                    products = products_response.json()
                    
                    product_schemas = []
                    for product in products:
                        product_schema = {
                            "@context": "https://schema.org",
                            "@type": "Product",
                            "name": product.get("name", ""),
                            "description": product.get("short_description", ""),
                            "image": [img.get("src", "") for img in product.get("images", [])],
                            "sku": product.get("sku", ""),
                            "offers": {
                                "@type": "Offer",
                                "price": product.get("price", ""),
                                "priceCurrency": "EUR",  # Would get from store settings
                                "availability": "https://schema.org/InStock" if product.get("stock_status") == "instock" else "https://schema.org/OutOfStock",
                                "url": product.get("permalink", "")
                            }
                        }
                        
                        # Add categories as product type
                        categories = product.get("categories", [])
                        if categories:
                            product_schema["category"] = categories[0].get("name", "")
                        
                        product_schemas.append(product_schema)
                    
                    markup_results["product_schemas"] = len(product_schemas)
                    markup_results["sample_product_schema"] = product_schemas[0] if product_schemas else None
                    markup_results["generated_schemas"].append("Product")
            
            except Exception as e:
                logger.warning(f"Could not generate product schemas: {e}")
            
            return markup_results
        
        return {"error": f"Unknown SEO action: {action}"}
    
    except Exception as e:
        logger.error(f"Error managing SEO settings: {e}")
        return {"error": str(e)}


def setup_analytics_tracking(api_client, analytics_config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup analytics tracking for the store"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        tracking_setup = {
            "google_analytics": {},
            "google_tag_manager": {},
            "facebook_pixel": {},
            "ecommerce_tracking": {},
            "custom_events": [],
            "setup_status": {}
        }
        
        # Google Analytics setup
        ga_config = analytics_config.get("google_analytics", {})
        if ga_config.get("tracking_id"):
            tracking_setup["google_analytics"] = {
                "tracking_id": ga_config["tracking_id"],
                "enhanced_ecommerce": ga_config.get("enhanced_ecommerce", True),
                "demographics": ga_config.get("demographics", True),
                "site_speed": ga_config.get("site_speed", True),
                "tracking_code": _generate_ga_tracking_code(ga_config["tracking_id"])
            }
            tracking_setup["setup_status"]["google_analytics"] = "configured"
        else:
            tracking_setup["setup_status"]["google_analytics"] = "not_configured"
        
        # Google Tag Manager setup
        gtm_config = analytics_config.get("google_tag_manager", {})
        if gtm_config.get("container_id"):
            tracking_setup["google_tag_manager"] = {
                "container_id": gtm_config["container_id"],
                "dataLayer_events": gtm_config.get("dataLayer_events", True),
                "ecommerce_events": gtm_config.get("ecommerce_events", True),
                "tracking_code": _generate_gtm_tracking_code(gtm_config["container_id"])
            }
            tracking_setup["setup_status"]["google_tag_manager"] = "configured"
        
        # Facebook Pixel setup
        fb_config = analytics_config.get("facebook_pixel", {})
        if fb_config.get("pixel_id"):
            tracking_setup["facebook_pixel"] = {
                "pixel_id": fb_config["pixel_id"],
                "standard_events": fb_config.get("standard_events", True),
                "conversion_api": fb_config.get("conversion_api", False),
                "tracking_code": _generate_fb_pixel_code(fb_config["pixel_id"])
            }
            tracking_setup["setup_status"]["facebook_pixel"] = "configured"
        
        # Ecommerce tracking events
        ecommerce_events = [
            "view_item",
            "add_to_cart",
            "begin_checkout",
            "purchase",
            "remove_from_cart",
            "view_item_list",
            "select_item"
        ]
        
        tracking_setup["ecommerce_tracking"] = {
            "events_to_track": ecommerce_events,
            "enhanced_ecommerce": True,
            "conversion_tracking": True,
            "revenue_tracking": True
        }
        
        # Custom events setup
        custom_events = analytics_config.get("custom_events", [])
        for event in custom_events:
            tracking_setup["custom_events"].append({
                "event_name": event.get("name"),
                "trigger": event.get("trigger"),
                "parameters": event.get("parameters", {})
            })
        
        # GDPR compliance setup
        tracking_setup["gdpr_compliance"] = {
            "cookie_consent": analytics_config.get("cookie_consent", True),
            "anonymize_ip": analytics_config.get("anonymize_ip", True),
            "data_retention": analytics_config.get("data_retention", "26 months"),
            "opt_out_option": analytics_config.get("opt_out", True)
        }
        
        return tracking_setup
    
    except Exception as e:
        logger.error(f"Error setting up analytics tracking: {e}")
        return {"error": str(e)}


def manage_social_media_integration(api_client, social_config: Dict[str, Any]) -> Dict[str, Any]:
    """Manage social media integration and marketing"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        action = social_config.get("action", "setup")
        
        if action == "setup":
            # Setup social media integrations
            integration_setup = {
                "facebook_shop": {},
                "instagram_shopping": {},
                "social_sharing": {},
                "social_login": {},
                "review_platforms": {},
                "setup_status": {}
            }
            
            # Facebook Shop integration
            fb_config = social_config.get("facebook", {})
            if fb_config:
                integration_setup["facebook_shop"] = {
                    "page_id": fb_config.get("page_id", ""),
                    "app_id": fb_config.get("app_id", ""),
                    "catalog_id": fb_config.get("catalog_id", ""),
                    "pixel_id": fb_config.get("pixel_id", ""),
                    "features": [
                        "Product catalog sync",
                        "Dynamic ads",
                        "Shop section",
                        "Messenger shopping"
                    ]
                }
                integration_setup["setup_status"]["facebook"] = "configured"
            
            # Instagram Shopping
            ig_config = social_config.get("instagram", {})
            if ig_config:
                integration_setup["instagram_shopping"] = {
                    "business_account": ig_config.get("business_account", ""),
                    "connected_to_facebook": ig_config.get("connected_to_facebook", False),
                    "shopping_tags": ig_config.get("shopping_tags", True),
                    "product_stickers": ig_config.get("product_stickers", True)
                }
                integration_setup["setup_status"]["instagram"] = "configured"
            
            # Social sharing buttons
            sharing_config = social_config.get("sharing", {})
            integration_setup["social_sharing"] = {
                "platforms": sharing_config.get("platforms", ["facebook", "twitter", "pinterest", "whatsapp"]),
                "placement": sharing_config.get("placement", ["product_pages", "blog_posts"]),
                "style": sharing_config.get("style", "buttons")
            }
            
            # Social login
            login_config = social_config.get("social_login", {})
            integration_setup["social_login"] = {
                "facebook_login": login_config.get("facebook", False),
                "google_login": login_config.get("google", False),
                "twitter_login": login_config.get("twitter", False),
                "benefits": [
                    "Faster checkout process",
                    "Reduced cart abandonment",
                    "Better user experience",
                    "Access to social profile data"
                ]
            }
            
            return integration_setup
        
        elif action == "sync_products":
            # Sync products to social platforms
            sync_config = social_config.get("sync", {})
            platforms = sync_config.get("platforms", ["facebook", "instagram"])
            
            sync_results = {
                "platforms": platforms,
                "sync_status": {},
                "total_products": 0,
                "synced_products": 0,
                "failed_products": 0
            }
            
            # Get products to sync
            products_response = api_client.get("products", params={"per_page": 100, "status": "publish"})
            if products_response.status_code == 200:
                products = products_response.json()
                sync_results["total_products"] = len(products)
                
                for platform in platforms:
                    platform_results = {
                        "synced": 0,
                        "failed": 0,
                        "errors": []
                    }
                    
                    for product in products:
                        try:
                            # Validate product for social commerce
                            validation = _validate_product_for_social(product, platform)
                            
                            if validation["valid"]:
                                # Would sync to actual platform
                                platform_results["synced"] += 1
                            else:
                                platform_results["failed"] += 1
                                platform_results["errors"].append({
                                    "product_id": product.get("id"),
                                    "product_name": product.get("name"),
                                    "issues": validation["issues"]
                                })
                        
                        except Exception as e:
                            platform_results["failed"] += 1
                            platform_results["errors"].append({
                                "product_id": product.get("id"),
                                "error": str(e)
                            })
                    
                    sync_results["sync_status"][platform] = platform_results
                
                sync_results["synced_products"] = sum(p["synced"] for p in sync_results["sync_status"].values())
                sync_results["failed_products"] = sum(p["failed"] for p in sync_results["sync_status"].values())
            
            return sync_results
        
        elif action == "generate_social_content":
            # Generate social media content for products
            content_config = social_config.get("content", {})
            
            # Get featured products
            products_response = api_client.get("products", params={"per_page": 10, "featured": True})
            if products_response.status_code != 200:
                products_response = api_client.get("products", params={"per_page": 10})
            
            if products_response.status_code != 200:
                return {"error": "Could not fetch products for content generation"}
            
            products = products_response.json()
            
            social_content = {
                "generated_posts": [],
                "content_calendar": [],
                "hashtag_suggestions": {},
                "content_types": ["product_showcase", "lifestyle", "behind_scenes", "user_generated"]
            }
            
            for product in products[:5]:  # Generate for first 5 products
                post_variations = _generate_social_post_variations(product, content_config)
                social_content["generated_posts"].extend(post_variations)
            
            # Generate hashtag suggestions
            social_content["hashtag_suggestions"] = _generate_hashtag_suggestions(products)
            
            # Create content calendar suggestions
            social_content["content_calendar"] = _generate_social_content_calendar(products)
            
            return social_content
        
        return {"error": f"Unknown social media action: {action}"}
    
    except Exception as e:
        logger.error(f"Error managing social media integration: {e}")
        return {"error": str(e)}


def optimize_multilingual_seo(api_client, multilingual_seo: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize SEO for multilingual and international stores"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        languages = multilingual_seo.get("languages", ["en", "fi", "sv"])
        target_markets = multilingual_seo.get("target_markets", {})
        
        optimization_results = {
            "languages": languages,
            "hreflang_tags": {},
            "url_structure": {},
            "local_seo": {},
            "keyword_optimization": {},
            "content_localization": {}
        }
        
        # Generate hreflang tags
        hreflang_tags = []
        for lang in languages:
            market_info = target_markets.get(lang, {})
            country_code = market_info.get("country", lang.upper())
            
            hreflang_tags.append({
                "hreflang": f"{lang}-{country_code}",
                "href": f"https://example.com/{lang}/",
                "language": lang,
                "country": country_code
            })
        
        optimization_results["hreflang_tags"] = hreflang_tags
        
        # URL structure recommendations
        optimization_results["url_structure"] = {
            "recommended_structure": "subdirectory",  # /en/, /fi/, /sv/
            "alternatives": [
                {"type": "subdomain", "example": "en.example.com", "pros": ["Clear separation"], "cons": ["SEO complexity"]},
                {"type": "ccTLD", "example": "example.fi", "pros": ["Local trust"], "cons": ["Multiple domains to manage"]},
                {"type": "parameter", "example": "example.com?lang=fi", "pros": ["Simple setup"], "cons": ["Poor SEO"]}
            ],
            "current_recommendation": "Use subdirectory structure (/en/, /fi/) for better SEO consolidation"
        }
        
        # Local SEO optimization
        for lang in languages:
            market = target_markets.get(lang, {})
            
            local_seo = {
                "language": lang,
                "country": market.get("country", ""),
                "currency": market.get("currency", "EUR"),
                "local_keywords": market.get("keywords", []),
                "local_search_optimization": [
                    f"Google My Business in {lang}",
                    f"Local directory listings",
                    f"Customer reviews in {lang}",
                    f"Local content creation"
                ],
                "schema_markup": {
                    "language": lang,
                    "addressCountry": market.get("country", ""),
                    "priceCurrency": market.get("currency", "EUR")
                }
            }
            
            optimization_results["local_seo"][lang] = local_seo
        
        # Keyword optimization by language
        try:
            products_response = api_client.get("products", params={"per_page": 20})
            if products_response.status_code == 200:
                products = products_response.json()
                
                for lang in languages:
                    keyword_suggestions = []
                    
                    for product in products[:5]:  # Sample products
                        product_name = product.get("name", "")
                        categories = [cat.get("name", "") for cat in product.get("categories", [])]
                        
                        # Generate localized keyword suggestions
                        base_keywords = [product_name.lower()] + [cat.lower() for cat in categories]
                        
                        # Add language-specific modifiers
                        if lang == "fi":
                            keyword_suggestions.extend([
                                f"{keyword} Suomessa" for keyword in base_keywords[:2]
                            ])
                            keyword_suggestions.extend([
                                f"osta {keyword}" for keyword in base_keywords[:2]
                            ])
                        elif lang == "sv":
                            keyword_suggestions.extend([
                                f"{keyword} Sverige" for keyword in base_keywords[:2]
                            ])
                            keyword_suggestions.extend([
                                f"köp {keyword}" for keyword in base_keywords[:2]
                            ])
                        
                    optimization_results["keyword_optimization"][lang] = {
                        "suggested_keywords": keyword_suggestions[:10],
                        "keyword_research_tips": [
                            f"Use Google Keyword Planner for {lang} keywords",
                            f"Analyze local competitors in {lang}",
                            f"Consider cultural context in {lang}",
                            f"Monitor search trends in target markets"
                        ]
                    }
        
        except Exception as e:
            logger.warning(f"Could not generate keyword optimization: {e}")
        
        # Content localization recommendations
        optimization_results["content_localization"] = {
            "critical_content": [
                "Product descriptions and titles",
                "Category descriptions",
                "Homepage and key landing pages",
                "Legal pages (Terms, Privacy)",
                "Customer service content"
            ],
            "localization_best_practices": [
                "Translate, don't just convert text",
                "Adapt cultural references and imagery",
                "Localize prices, currencies, and measurements",
                "Consider local payment preferences",
                "Adapt to local business practices and regulations",
                "Use native speakers for quality control"
            ],
            "seo_localization_tips": [
                "Research local search behavior",
                "Use local domain authority sites for backlinks",
                "Create location-specific content",
                "Optimize for local search engines (Yandex, Baidu)",
                "Monitor local search rankings separately"
            ]
        }
        
        return optimization_results
    
    except Exception as e:
        logger.error(f"Error optimizing multilingual SEO: {e}")
        return {"error": str(e)}


def _generate_ga_tracking_code(tracking_id: str) -> str:
    """Generate Google Analytics tracking code"""
    
    return f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={tracking_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{tracking_id}', {{
    'anonymize_ip': true,
    'custom_map': {{'custom_parameter': 'custom_value'}}
  }});
</script>
<!-- End Google Analytics -->
"""


def _generate_gtm_tracking_code(container_id: str) -> str:
    """Generate Google Tag Manager tracking code"""
    
    return f"""
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{container_id}');</script>
<!-- End Google Tag Manager -->

<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={container_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"""


def _generate_fb_pixel_code(pixel_id: str) -> str:
    """Generate Facebook Pixel tracking code"""
    
    return f"""
<!-- Facebook Pixel Code -->
<script>
  !function(f,b,e,v,n,t,s)
  {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '{pixel_id}');
  fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
  src="https://www.facebook.com/tr?id={pixel_id}&ev=PageView&noscript=1"
/></noscript>
<!-- End Facebook Pixel Code -->
"""


def _validate_product_for_social(product: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """Validate product for social commerce requirements"""
    
    issues = []
    valid = True
    
    # Check required fields
    if not product.get("name", "").strip():
        issues.append("Missing product name")
        valid = False
    
    if not product.get("description", "").strip() and not product.get("short_description", "").strip():
        issues.append("Missing product description")
        valid = False
    
    if not product.get("images"):
        issues.append("Missing product images")
        valid = False
    
    if not product.get("price") or float(product.get("price", 0)) <= 0:
        issues.append("Missing or invalid price")
        valid = False
    
    # Platform-specific requirements
    if platform == "facebook":
        if len(product.get("name", "")) > 150:
            issues.append("Product name too long for Facebook (max 150 characters)")
        
        if len(product.get("description", "")) > 5000:
            issues.append("Product description too long for Facebook (max 5000 characters)")
    
    elif platform == "instagram":
        if not product.get("images"):
            issues.append("Instagram requires high-quality images")
            valid = False
    
    return {"valid": valid, "issues": issues}


def _generate_social_post_variations(product: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate social media post variations for a product"""
    
    product_name = product.get("name", "Product")
    price = product.get("price", "0")
    categories = [cat.get("name", "") for cat in product.get("categories", [])]
    
    variations = []
    
    # Product showcase post
    variations.append({
        "type": "product_showcase",
        "platform": "instagram",
        "caption": f"✨ New arrival: {product_name}\n\n{product.get('short_description', '')}[:100]...\n\n💰 Starting at €{price}\n\n#newproduct #shop #ecommerce",
        "image_required": True,
        "cta": "Shop now in bio!"
    })
    
    # Facebook post
    variations.append({
        "type": "product_feature",
        "platform": "facebook",
        "caption": f"Introducing {product_name}! Perfect for {categories[0] if categories else 'your needs'}. Get yours today for just €{price}.",
        "image_required": True,
        "cta": "Shop Now"
    })
    
    # Story post
    variations.append({
        "type": "story",
        "platform": "instagram",
        "caption": f"{product_name}\n€{price}",
        "image_required": True,
        "cta": "Swipe up to shop!",
        "duration": "24h"
    })
    
    return variations


def _generate_hashtag_suggestions(products: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Generate hashtag suggestions based on products"""
    
    hashtags = {
        "general": ["#shop", "#ecommerce", "#onlineshopping", "#retail", "#sale"],
        "product_specific": [],
        "branded": ["#yourbrand", "#qualityproducts", "#trustedstore"],
        "seasonal": ["#newyear", "#spring", "#summer", "#autumn", "#winter"]
    }
    
    # Generate product-specific hashtags
    all_categories = []
    for product in products:
        categories = [cat.get("name", "").lower().replace(" ", "") for cat in product.get("categories", [])]
        all_categories.extend(categories)
    
    unique_categories = list(set(all_categories))
    hashtags["product_specific"] = [f"#{cat}" for cat in unique_categories[:10]]
    
    return hashtags


def _generate_social_content_calendar(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate social content calendar suggestions"""
    
    calendar = []
    
    # Weekly content suggestions
    content_types = [
        {"day": "Monday", "type": "motivation", "content": "Monday motivation with featured product"},
        {"day": "Tuesday", "type": "tutorial", "content": "How-to content featuring products"},
        {"day": "Wednesday", "type": "behind_scenes", "content": "Behind the scenes content"},
        {"day": "Thursday", "type": "user_generated", "content": "Customer features and reviews"},
        {"day": "Friday", "type": "product_feature", "content": "Weekend product recommendations"},
        {"day": "Saturday", "type": "lifestyle", "content": "Lifestyle content with products"},
        {"day": "Sunday", "type": "community", "content": "Community engagement posts"}
    ]
    
    for content_type in content_types:
        calendar.append({
            "day": content_type["day"],
            "content_type": content_type["type"],
            "suggestion": content_type["content"],
            "optimal_time": "10:00 AM" if content_type["day"] in ["Tuesday", "Thursday"] else "2:00 PM"
        })
    
    return calendar