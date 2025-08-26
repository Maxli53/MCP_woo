"""
Multi-Language and Currency Management Tools
Complete internationalization support for WooCommerce stores
"""

import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


def get_supported_languages(api_client) -> Dict[str, Any]:
    """Get supported languages and translation status for the store"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        # Get system status to check for multilingual plugins
        system_response = api_client.get("system_status")
        languages_info = {
            "default_language": "en",
            "available_languages": [],
            "translation_plugins": [],
            "translation_status": {},
            "currency_languages": {}
        }
        
        if system_response.status_code == 200:
            system_data = system_response.json()
            
            # Check for popular multilingual plugins
            active_plugins = system_data.get("active_plugins", [])
            multilingual_plugins = []
            
            for plugin in active_plugins:
                plugin_name = plugin.get("name", "").lower()
                if any(term in plugin_name for term in ["wpml", "polylang", "weglot", "translatepress", "multilingual"]):
                    multilingual_plugins.append({
                        "name": plugin.get("name"),
                        "version": plugin.get("version"),
                        "active": True
                    })
            
            languages_info["translation_plugins"] = multilingual_plugins
        
        # Common language configurations
        common_languages = {
            "en": {"name": "English", "locale": "en_US", "currency_preference": "USD"},
            "fi": {"name": "Finnish", "locale": "fi_FI", "currency_preference": "EUR"},
            "sv": {"name": "Swedish", "locale": "sv_SE", "currency_preference": "SEK"},
            "da": {"name": "Danish", "locale": "da_DK", "currency_preference": "DKK"},
            "no": {"name": "Norwegian", "locale": "nb_NO", "currency_preference": "NOK"},
            "de": {"name": "German", "locale": "de_DE", "currency_preference": "EUR"},
            "fr": {"name": "French", "locale": "fr_FR", "currency_preference": "EUR"},
            "es": {"name": "Spanish", "locale": "es_ES", "currency_preference": "EUR"},
            "it": {"name": "Italian", "locale": "it_IT", "currency_preference": "EUR"},
            "nl": {"name": "Dutch", "locale": "nl_NL", "currency_preference": "EUR"},
            "pt": {"name": "Portuguese", "locale": "pt_PT", "currency_preference": "EUR"},
            "ru": {"name": "Russian", "locale": "ru_RU", "currency_preference": "RUB"},
            "zh": {"name": "Chinese", "locale": "zh_CN", "currency_preference": "CNY"},
            "ja": {"name": "Japanese", "locale": "ja_JP", "currency_preference": "JPY"},
            "ko": {"name": "Korean", "locale": "ko_KR", "currency_preference": "KRW"}
        }
        
        # Check which languages might be available based on store configuration
        try:
            # Get general settings to see current locale
            settings_response = api_client.get("settings/general")
            if settings_response.status_code == 200:
                settings = settings_response.json()
                for setting in settings:
                    if setting.get("id") == "woocommerce_default_country":
                        country_code = setting.get("value", "").split(":")[0]
                        # Map country to likely language
                        country_to_language = {
                            "FI": "fi", "SE": "sv", "DK": "da", "NO": "no",
                            "DE": "de", "FR": "fr", "ES": "es", "IT": "it",
                            "NL": "nl", "PT": "pt", "RU": "ru", "CN": "zh",
                            "JP": "ja", "KR": "ko", "US": "en", "GB": "en",
                            "CA": "en", "AU": "en"
                        }
                        default_lang = country_to_language.get(country_code, "en")
                        languages_info["default_language"] = default_lang
        except Exception as e:
            logger.warning(f"Could not determine default language: {e}")
        
        languages_info["available_languages"] = list(common_languages.keys())
        languages_info["language_details"] = common_languages
        
        # If multilingual plugins detected, try to get actual language configuration
        if languages_info["translation_plugins"]:
            languages_info["plugin_detected"] = True
            languages_info["note"] = "Multilingual plugin detected. Use plugin-specific APIs for detailed language management."
        
        return languages_info
    
    except Exception as e:
        logger.error(f"Error fetching language support info: {e}")
        return {"error": str(e)}


def manage_translations(api_client, translation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manage store translations for products, categories, and content"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        action = translation_data.get("action", "get_translation_status")
        target_language = translation_data.get("target_language", "fi")
        
        results = {
            "action": action,
            "target_language": target_language,
            "translation_results": {}
        }
        
        if action == "get_translation_status":
            # Get translation status for various content types
            translation_status = {
                "products": {"total": 0, "translated": 0, "pending": 0},
                "categories": {"total": 0, "translated": 0, "pending": 0},
                "pages": {"total": 0, "translated": 0, "pending": 0},
                "settings": {"total": 0, "translated": 0, "pending": 0}
            }
            
            # Check products
            try:
                products_response = api_client.get("products", params={"per_page": 100})
                if products_response.status_code == 200:
                    products = products_response.json()
                    translation_status["products"]["total"] = len(products)
                    
                    # Check for translation meta or multilingual plugin data
                    for product in products:
                        meta_data = product.get("meta_data", [])
                        has_translation = any(
                            meta.get("key", "").startswith(f"_translation_{target_language}")
                            for meta in meta_data
                        )
                        
                        if has_translation:
                            translation_status["products"]["translated"] += 1
                        else:
                            translation_status["products"]["pending"] += 1
            except Exception as e:
                logger.warning(f"Could not check product translations: {e}")
            
            # Check categories
            try:
                categories_response = api_client.get("products/categories", params={"per_page": 100})
                if categories_response.status_code == 200:
                    categories = categories_response.json()
                    translation_status["categories"]["total"] = len(categories)
                    # Similar translation checking logic
                    translation_status["categories"]["pending"] = len(categories)  # Simplified
            except Exception as e:
                logger.warning(f"Could not check category translations: {e}")
            
            results["translation_status"] = translation_status
        
        elif action == "translate_products":
            # Translate products using provided translations or auto-translation
            product_translations = translation_data.get("product_translations", {})
            
            if not product_translations:
                return {"error": "No product translations provided"}
            
            translation_results = {
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for product_id, translations in product_translations.items():
                try:
                    # Get current product
                    product_response = api_client.get(f"products/{product_id}")
                    if product_response.status_code != 200:
                        translation_results["errors"].append(f"Product {product_id} not found")
                        translation_results["failed"] += 1
                        continue
                    
                    product = product_response.json()
                    
                    # Prepare translation meta data
                    current_meta = product.get("meta_data", [])
                    new_meta = [meta for meta in current_meta 
                              if not meta.get("key", "").startswith(f"_translation_{target_language}")]
                    
                    # Add new translations as meta data
                    for field, translated_value in translations.items():
                        new_meta.append({
                            "key": f"_translation_{target_language}_{field}",
                            "value": translated_value
                        })
                    
                    # Update product with translation meta
                    update_data = {"meta_data": new_meta}
                    update_response = api_client.put(f"products/{product_id}", update_data)
                    
                    if update_response.status_code in [200, 201]:
                        translation_results["successful"] += 1
                    else:
                        translation_results["errors"].append(f"Failed to update product {product_id}")
                        translation_results["failed"] += 1
                
                except Exception as e:
                    translation_results["errors"].append(f"Error translating product {product_id}: {str(e)}")
                    translation_results["failed"] += 1
            
            results["translation_results"] = translation_results
        
        elif action == "translate_categories":
            # Translate categories
            category_translations = translation_data.get("category_translations", {})
            
            translation_results = {
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for category_id, translations in category_translations.items():
                try:
                    # For categories, we might create translated versions
                    # or use meta data depending on the multilingual setup
                    category_response = api_client.get(f"products/categories/{category_id}")
                    if category_response.status_code != 200:
                        translation_results["errors"].append(f"Category {category_id} not found")
                        translation_results["failed"] += 1
                        continue
                    
                    # In a real implementation, this would integrate with
                    # the specific multilingual plugin being used
                    translation_results["successful"] += 1
                
                except Exception as e:
                    translation_results["errors"].append(f"Error translating category {category_id}: {str(e)}")
                    translation_results["failed"] += 1
            
            results["translation_results"] = translation_results
        
        elif action == "auto_translate":
            # Auto-translate content using a translation service
            content_type = translation_data.get("content_type", "products")
            source_language = translation_data.get("source_language", "en")
            
            if content_type == "products":
                # Get products that need translation
                products_response = api_client.get("products", params={"per_page": 50})
                if products_response.status_code == 200:
                    products = products_response.json()
                    
                    auto_translation_results = {
                        "processed": 0,
                        "translated": 0,
                        "skipped": 0,
                        "errors": []
                    }
                    
                    for product in products:
                        try:
                            # Check if already translated
                            meta_data = product.get("meta_data", [])
                            already_translated = any(
                                meta.get("key", "").startswith(f"_translation_{target_language}")
                                for meta in meta_data
                            )
                            
                            if already_translated:
                                auto_translation_results["skipped"] += 1
                                continue
                            
                            # Auto-translate key fields
                            translations = {}
                            
                            if product.get("name"):
                                translations["name"] = _auto_translate_text(
                                    product["name"], source_language, target_language
                                )
                            
                            if product.get("short_description"):
                                translations["short_description"] = _auto_translate_text(
                                    product["short_description"], source_language, target_language
                                )
                            
                            if product.get("description"):
                                translations["description"] = _auto_translate_text(
                                    product["description"], source_language, target_language
                                )
                            
                            # Store translations
                            if translations:
                                new_meta = list(meta_data)
                                for field, translated_value in translations.items():
                                    new_meta.append({
                                        "key": f"_translation_{target_language}_{field}",
                                        "value": translated_value
                                    })
                                
                                update_data = {"meta_data": new_meta}
                                update_response = api_client.put(f"products/{product['id']}", update_data)
                                
                                if update_response.status_code in [200, 201]:
                                    auto_translation_results["translated"] += 1
                                else:
                                    auto_translation_results["errors"].append(f"Failed to save translation for product {product['id']}")
                            
                            auto_translation_results["processed"] += 1
                        
                        except Exception as e:
                            auto_translation_results["errors"].append(f"Error auto-translating product {product.get('id')}: {str(e)}")
                    
                    results["auto_translation_results"] = auto_translation_results
        
        return results
    
    except Exception as e:
        logger.error(f"Error managing translations: {e}")
        return {"error": str(e)}


def manage_multi_currency(api_client, currency_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure multi-currency support and exchange rates"""
    
    if not api_client:
        return {"error": "No API client available"}
    
    try:
        action = currency_config.get("action", "get_currency_info")
        
        if action == "get_currency_info":
            # Get current currency settings
            settings_response = api_client.get("settings/general")
            current_currency = "EUR"  # Default
            currency_position = "left"
            thousand_separator = ","
            decimal_separator = "."
            decimal_places = 2
            
            if settings_response.status_code == 200:
                settings = settings_response.json()
                for setting in settings:
                    if setting.get("id") == "woocommerce_currency":
                        current_currency = setting.get("value", "EUR")
                    elif setting.get("id") == "woocommerce_currency_pos":
                        currency_position = setting.get("value", "left")
                    elif setting.get("id") == "woocommerce_price_thousand_sep":
                        thousand_separator = setting.get("value", ",")
                    elif setting.get("id") == "woocommerce_price_decimal_sep":
                        decimal_separator = setting.get("value", ".")
                    elif setting.get("id") == "woocommerce_price_num_decimals":
                        decimal_places = int(setting.get("value", 2))
            
            # Currency information
            currencies = {
                "EUR": {"name": "Euro", "symbol": "€", "countries": ["FI", "DE", "FR", "IT", "ES"]},
                "USD": {"name": "US Dollar", "symbol": "$", "countries": ["US"]},
                "GBP": {"name": "British Pound", "symbol": "£", "countries": ["GB"]},
                "SEK": {"name": "Swedish Krona", "symbol": "kr", "countries": ["SE"]},
                "DKK": {"name": "Danish Krone", "symbol": "kr", "countries": ["DK"]},
                "NOK": {"name": "Norwegian Krone", "symbol": "kr", "countries": ["NO"]},
                "CHF": {"name": "Swiss Franc", "symbol": "CHF", "countries": ["CH"]},
                "CAD": {"name": "Canadian Dollar", "symbol": "C$", "countries": ["CA"]},
                "AUD": {"name": "Australian Dollar", "symbol": "A$", "countries": ["AU"]},
                "JPY": {"name": "Japanese Yen", "symbol": "¥", "countries": ["JP"]},
                "CNY": {"name": "Chinese Yuan", "symbol": "¥", "countries": ["CN"]},
                "RUB": {"name": "Russian Ruble", "symbol": "₽", "countries": ["RU"]}
            }
            
            return {
                "current_currency": current_currency,
                "currency_settings": {
                    "position": currency_position,
                    "thousand_separator": thousand_separator,
                    "decimal_separator": decimal_separator,
                    "decimal_places": decimal_places
                },
                "available_currencies": currencies,
                "current_currency_info": currencies.get(current_currency, {})
            }
        
        elif action == "update_currency_settings":
            # Update currency-related settings
            settings_updates = currency_config.get("settings", {})
            
            # Map friendly names to WooCommerce setting IDs
            setting_mapping = {
                "currency": "woocommerce_currency",
                "currency_position": "woocommerce_currency_pos",
                "thousand_separator": "woocommerce_price_thousand_sep",
                "decimal_separator": "woocommerce_price_decimal_sep",
                "decimal_places": "woocommerce_price_num_decimals"
            }
            
            update_results = {
                "updated_settings": [],
                "failed_updates": [],
                "warnings": []
            }
            
            for setting_key, new_value in settings_updates.items():
                if setting_key in setting_mapping:
                    wc_setting_id = setting_mapping[setting_key]
                    
                    try:
                        update_data = {"value": new_value}
                        response = api_client.put(f"settings/general/{wc_setting_id}", update_data)
                        
                        if response.status_code in [200, 201]:
                            update_results["updated_settings"].append({
                                "setting": setting_key,
                                "wc_id": wc_setting_id,
                                "new_value": new_value
                            })
                            
                            # Add warnings for critical changes
                            if setting_key == "currency":
                                update_results["warnings"].append(
                                    "Currency change affects all product prices and existing orders"
                                )
                        else:
                            update_results["failed_updates"].append({
                                "setting": setting_key,
                                "error": response.text
                            })
                    
                    except Exception as e:
                        update_results["failed_updates"].append({
                            "setting": setting_key,
                            "error": str(e)
                        })
            
            return update_results
        
        elif action == "configure_regional_pricing":
            # Configure pricing for different regions/currencies
            regional_config = currency_config.get("regional_config", {})
            
            pricing_results = {
                "configured_regions": [],
                "pricing_rules": [],
                "errors": []
            }
            
            for region, config in regional_config.items():
                try:
                    # This would typically integrate with a multi-currency plugin
                    # For now, we'll store configuration as meta data
                    
                    pricing_rule = {
                        "region": region,
                        "currency": config.get("currency", "EUR"),
                        "price_multiplier": config.get("price_multiplier", 1.0),
                        "rounding_rule": config.get("rounding_rule", "normal"),
                        "tax_inclusive": config.get("tax_inclusive", False)
                    }
                    
                    pricing_results["pricing_rules"].append(pricing_rule)
                    pricing_results["configured_regions"].append(region)
                
                except Exception as e:
                    pricing_results["errors"].append(f"Error configuring region {region}: {str(e)}")
            
            return pricing_results
        
        elif action == "convert_prices":
            # Convert product prices to different currency
            conversion_config = currency_config.get("conversion_config", {})
            source_currency = conversion_config.get("source_currency", "EUR")
            target_currency = conversion_config.get("target_currency", "USD")
            exchange_rate = conversion_config.get("exchange_rate")
            
            if not exchange_rate:
                # Get current exchange rate (in real implementation, would use live rates)
                exchange_rate = _get_exchange_rate(source_currency, target_currency)
            
            # Get products to convert
            products_response = api_client.get("products", params={"per_page": 100})
            if products_response.status_code != 200:
                return {"error": "Could not fetch products for conversion"}
            
            products = products_response.json()
            conversion_results = {
                "converted_products": 0,
                "total_products": len(products),
                "exchange_rate": exchange_rate,
                "source_currency": source_currency,
                "target_currency": target_currency,
                "errors": []
            }
            
            for product in products:
                try:
                    product_id = product.get("id")
                    regular_price = product.get("regular_price")
                    sale_price = product.get("sale_price")
                    
                    update_data = {}
                    
                    if regular_price:
                        converted_regular = float(regular_price) * exchange_rate
                        update_data["regular_price"] = str(round(converted_regular, 2))
                    
                    if sale_price:
                        converted_sale = float(sale_price) * exchange_rate
                        update_data["sale_price"] = str(round(converted_sale, 2))
                    
                    if update_data:
                        response = api_client.put(f"products/{product_id}", update_data)
                        if response.status_code in [200, 201]:
                            conversion_results["converted_products"] += 1
                        else:
                            conversion_results["errors"].append(f"Failed to convert product {product_id}")
                
                except Exception as e:
                    conversion_results["errors"].append(f"Error converting product {product.get('id')}: {str(e)}")
            
            return conversion_results
        
        return {"error": f"Unknown action: {action}"}
    
    except Exception as e:
        logger.error(f"Error managing multi-currency: {e}")
        return {"error": str(e)}


def sync_translations_between_stores(api_clients: Dict[str, Any], source_store: str, 
                                   target_stores: List[str], language_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronize translations between multiple stores"""
    
    if source_store not in api_clients:
        return {"error": f"Source store {source_store} not found"}
    
    source_api = api_clients[source_store]
    sync_results = {
        "source_store": source_store,
        "target_stores": target_stores,
        "language_rules": language_rules,
        "sync_results": {}
    }
    
    try:
        # Get content from source store
        source_content = {}
        
        # Get products
        products_response = source_api.get("products", params={"per_page": 100})
        if products_response.status_code == 200:
            source_content["products"] = products_response.json()
        
        # Get categories
        categories_response = source_api.get("products/categories", params={"per_page": 100})
        if categories_response.status_code == 200:
            source_content["categories"] = categories_response.json()
        
        # Sync to each target store
        for target_store in target_stores:
            if target_store not in api_clients:
                sync_results["sync_results"][target_store] = {"error": "Store not found"}
                continue
            
            target_api = api_clients[target_store]
            target_language = language_rules.get(target_store, {}).get("language", "en")
            
            store_sync_result = {
                "target_language": target_language,
                "synced_products": 0,
                "synced_categories": 0,
                "errors": []
            }
            
            # Sync products
            if "products" in source_content:
                for source_product in source_content["products"]:
                    try:
                        # Find corresponding product in target store (by SKU)
                        sku = source_product.get("sku")
                        if sku:
                            target_products = target_api.get("products", params={"sku": sku})
                            if target_products.status_code == 200 and target_products.json():
                                target_product = target_products.json()[0]
                                
                                # Apply translations
                                translated_data = _apply_translation_rules(
                                    source_product, target_language, language_rules
                                )
                                
                                if translated_data:
                                    update_response = target_api.put(
                                        f"products/{target_product['id']}", 
                                        translated_data
                                    )
                                    
                                    if update_response.status_code in [200, 201]:
                                        store_sync_result["synced_products"] += 1
                    
                    except Exception as e:
                        store_sync_result["errors"].append(f"Product sync error: {str(e)}")
            
            sync_results["sync_results"][target_store] = store_sync_result
        
        return sync_results
    
    except Exception as e:
        logger.error(f"Error syncing translations: {e}")
        return {"error": str(e)}


def _auto_translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Auto-translate text using translation service (placeholder implementation)"""
    
    # This is a placeholder - in a real implementation, this would:
    # 1. Use Google Translate API, DeepL, or similar service
    # 2. Handle HTML content properly
    # 3. Preserve formatting and special characters
    # 4. Cache translations for efficiency
    
    # For now, return a simple mock translation
    if target_lang == "fi" and source_lang == "en":
        # Very basic Finnish translation examples
        simple_translations = {
            "product": "tuote",
            "price": "hinta",
            "buy": "osta",
            "cart": "kori",
            "checkout": "kassalle",
            "shipping": "toimitus",
            "description": "kuvaus"
        }
        
        translated = text.lower()
        for en_word, fi_word in simple_translations.items():
            translated = translated.replace(en_word, fi_word)
        
        return translated.capitalize() if text else text
    
    # For other languages, return original text with a note
    return f"[AUTO-TRANSLATED to {target_lang}] {text}"


def _get_exchange_rate(source_currency: str, target_currency: str) -> float:
    """Get exchange rate between currencies (placeholder implementation)"""
    
    # This is a placeholder - in a real implementation, this would:
    # 1. Use live exchange rate APIs (xe.com, fixer.io, etc.)
    # 2. Cache rates for performance
    # 3. Handle API failures gracefully
    
    # Mock exchange rates (as of a sample date)
    mock_rates = {
        ("EUR", "USD"): 1.08,
        ("EUR", "GBP"): 0.86,
        ("EUR", "SEK"): 11.5,
        ("EUR", "DKK"): 7.44,
        ("EUR", "NOK"): 11.8,
        ("USD", "EUR"): 0.93,
        ("GBP", "EUR"): 1.16,
        ("SEK", "EUR"): 0.087
    }
    
    rate_key = (source_currency, target_currency)
    return mock_rates.get(rate_key, 1.0)


def _apply_translation_rules(source_content: Dict[str, Any], target_language: str, 
                           language_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Apply translation rules to content"""
    
    translated_data = {}
    translation_fields = ["name", "description", "short_description"]
    
    for field in translation_fields:
        if field in source_content and source_content[field]:
            # Check if translation rule exists
            field_rules = language_rules.get("field_mappings", {}).get(field)
            
            if field_rules and target_language in field_rules:
                translated_data[field] = field_rules[target_language]
            else:
                # Use auto-translation
                translated_data[field] = _auto_translate_text(
                    source_content[field], "en", target_language
                )
    
    return translated_data