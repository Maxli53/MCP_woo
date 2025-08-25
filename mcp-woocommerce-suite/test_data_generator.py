"""
Test Data Generation System for MCP WooCommerce Suite
Creates comprehensive test datasets for all testing scenarios
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import csv
import os
from pathlib import Path

class TestDataGenerator:
    def __init__(self):
        self.base_path = Path("test_data")
        self.base_path.mkdir(exist_ok=True)
        
        # Snowmobile categories and brands
        self.categories = [
            "Mountain Sleds", "Trail Sleds", "Crossovers", 
            "Touring Sleds", "Performance Sleds", "Utility Sleds",
            "Youth Sleds", "Electric Sleds"
        ]
        
        self.brands = [
            "Lynx", "Ski-Doo", "Polaris", "Arctic Cat", 
            "Yamaha", "Tundra", "Alpina", "Taiga"
        ]
        
        self.models = {
            "Lynx": ["Commander", "Rave", "BoonDocker", "Adventure", "49 Ranger"],
            "Ski-Doo": ["Summit", "MXZ", "Grand Touring", "Expedition", "Freeride"],
            "Polaris": ["RMK", "Indy", "Switchback", "Titan", "Pro-RMK"],
            "Arctic Cat": ["Mountain Cat", "ZR", "Pantera", "Bearcat", "Riot"],
            "Yamaha": ["Mountain Max", "SRViper", "VK Professional", "Sidewinder"],
            "Tundra": ["LT", "Xtreme", "Sport"],
            "Alpina": ["Sherpa", "Bigfoot"],
            "Taiga": ["Nomad", "Ekko"]
        }
        
    def generate_product_id(self) -> str:
        """Generate unique product ID"""
        return f"PROD-{random.randint(1000, 9999)}"
    
    def generate_sku(self, brand: str, model: str) -> str:
        """Generate realistic SKU"""
        brand_code = brand[:3].upper()
        model_code = model.replace(" ", "")[:4].upper()
        year = random.choice([2023, 2024, 2025])
        variant = random.randint(1, 9)
        return f"{brand_code}-{model_code}-{year}-{variant}"
    
    def generate_price(self, category: str) -> float:
        """Generate realistic pricing based on category"""
        price_ranges = {
            "Mountain Sleds": (18000, 35000),
            "Trail Sleds": (12000, 28000),
            "Crossovers": (15000, 32000),
            "Touring Sleds": (14000, 25000),
            "Performance Sleds": (20000, 40000),
            "Utility Sleds": (8000, 18000),
            "Youth Sleds": (3000, 8000),
            "Electric Sleds": (15000, 30000)
        }
        min_price, max_price = price_ranges.get(category, (10000, 25000))
        return round(random.uniform(min_price, max_price), 2)
    
    def generate_product(self, product_id: str = None) -> Dict[str, Any]:
        """Generate a single realistic product"""
        if not product_id:
            product_id = self.generate_product_id()
            
        brand = random.choice(self.brands)
        model = random.choice(self.models[brand])
        category = random.choice(self.categories)
        
        # Generate engine specs
        engine_sizes = [600, 650, 700, 800, 850, 900, 1000]
        engine_size = random.choice(engine_sizes)
        
        # Generate realistic name
        year = random.choice([2023, 2024, 2025])
        name = f"{brand} {model} {engine_size} ({year})"
        
        # Generate description
        features = [
            "Advanced suspension system",
            "High-performance engine",
            "Lightweight chassis",
            "Electronic fuel injection",
            "Digital display",
            "Heated grips",
            "LED lighting system",
            "Premium track system"
        ]
        selected_features = random.sample(features, random.randint(3, 6))
        description = f"Professional {category.lower().rstrip('s')} featuring {', '.join(selected_features[:-1])}, and {selected_features[-1]}."
        
        product = {
            "id": product_id,
            "name": name,
            "sku": self.generate_sku(brand, model),
            "type": "simple",
            "status": random.choice(["publish", "publish", "publish", "draft"]),  # 75% published
            "featured": random.choice([True, False, False, False]),  # 25% featured
            "catalog_visibility": "visible",
            "description": description,
            "short_description": f"{brand} {model} - {engine_size}cc snowmobile",
            "price": str(self.generate_price(category)),
            "regular_price": str(self.generate_price(category)),
            "sale_price": "",
            "on_sale": False,
            "purchasable": True,
            "total_sales": random.randint(0, 100),
            "virtual": False,
            "downloadable": False,
            "downloads": [],
            "download_limit": -1,
            "download_expiry": -1,
            "external_url": "",
            "button_text": "",
            "tax_status": "taxable",
            "tax_class": "",
            "manage_stock": True,
            "stock_quantity": random.randint(0, 50),
            "stock_status": "instock" if random.random() > 0.1 else "outofstock",
            "backorders": "no",
            "low_stock_amount": 5,
            "sold_individually": False,
            "weight": str(random.randint(200, 350)),  # kg
            "dimensions": {
                "length": str(random.randint(300, 350)),  # cm
                "width": str(random.randint(110, 130)),   # cm
                "height": str(random.randint(120, 140))   # cm
            },
            "shipping_required": True,
            "shipping_taxable": True,
            "shipping_class": "",
            "shipping_class_id": 0,
            "reviews_allowed": True,
            "average_rating": str(round(random.uniform(3.5, 5.0), 1)),
            "rating_count": random.randint(0, 50),
            "related_ids": [],
            "upsell_ids": [],
            "cross_sell_ids": [],
            "parent_id": 0,
            "purchase_note": "",
            "categories": [
                {
                    "id": hash(category) % 1000,
                    "name": category,
                    "slug": category.lower().replace(" ", "-")
                }
            ],
            "tags": [
                {"id": hash(brand) % 1000, "name": brand, "slug": brand.lower()},
                {"id": hash(f"{engine_size}cc") % 1000, "name": f"{engine_size}cc", "slug": f"{engine_size}cc"}
            ],
            "images": [
                {
                    "id": random.randint(1000, 9999),
                    "date_created": datetime.now().isoformat(),
                    "date_modified": datetime.now().isoformat(),
                    "src": f"https://example.com/images/{product_id}-main.jpg",
                    "name": f"{name} - Main Image",
                    "alt": f"{name} main product image"
                }
            ],
            "attributes": [
                {
                    "id": 1,
                    "name": "Brand",
                    "position": 0,
                    "visible": True,
                    "variation": False,
                    "options": [brand]
                },
                {
                    "id": 2,
                    "name": "Engine Size",
                    "position": 1,
                    "visible": True,
                    "variation": False,
                    "options": [f"{engine_size}cc"]
                },
                {
                    "id": 3,
                    "name": "Year",
                    "position": 2,
                    "visible": True,
                    "variation": False,
                    "options": [str(year)]
                }
            ],
            "default_attributes": [],
            "variations": [],
            "grouped_products": [],
            "menu_order": 0,
            "meta_data": [
                {
                    "id": random.randint(10000, 99999),
                    "key": "_test_data",
                    "value": "generated"
                }
            ],
            "date_created": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "date_modified": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "permalink": f"https://example.com/product/{name.lower().replace(' ', '-')}"
        }
        
        return product
    
    def generate_store_config(self, store_id: str, name: str, url: str) -> Dict[str, Any]:
        """Generate test store configuration"""
        return {
            "id": store_id,
            "name": name,
            "url": url,
            "consumer_key": f"ck_{uuid.uuid4().hex[:32]}",
            "consumer_secret": f"cs_{uuid.uuid4().hex[:32]}",
            "status": random.choice(["connected", "connected", "error", "disconnected"]),
            "added": datetime.now().isoformat(),
            "last_sync": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            "product_count": random.randint(10, 1000),
            "api_version": "wc/v3",
            "wp_version": "6.3.2",
            "wc_version": "8.2.1"
        }
    
    def generate_test_stores(self, count: int = 5) -> Dict[str, Any]:
        """Generate multiple test stores"""
        stores = {}
        
        # Always include RideBase.fi as store_0
        stores["store_0"] = {
            "id": "store_0",
            "name": "RideBase.fi",
            "url": "https://ridebase.fi",
            "consumer_key": "ck_f6ad7b402ad502bcccd39616c94717f282954278",
            "consumer_secret": "cs_9732d3b1cfe2db9fffd47316e99884efecac4b9c",
            "status": "connected",
            "added": "2025-08-25T21:43:46.540141"
        }
        
        # Generate additional test stores
        test_store_names = [
            "Arctic Adventures", "Snow Peak Sports", "Winter Rides Co",
            "Mountain Sleds Pro", "Trail Blazer Store", "Nordic Power",
            "Frozen Motorsports", "Summit Snowmobiles", "Blizzard Bikes"
        ]
        
        for i in range(1, count):
            store_id = f"store_{i}"
            store_name = test_store_names[i-1] if i-1 < len(test_store_names) else f"Test Store {i}"
            store_url = f"https://{store_name.lower().replace(' ', '')}.test.com"
            stores[store_id] = self.generate_store_config(store_id, store_name, store_url)
        
        return stores
    
    def generate_product_dataset(self, count: int = 1000) -> List[Dict[str, Any]]:
        """Generate large product dataset"""
        products = []
        
        # Include some products based on RideBase.fi patterns
        ridebase_products = [
            ("Lynx Commander 900", "LYX-CMD-2024-1"),
            ("Lynx Rave 850", "LYX-RAV-2024-2"),
            ("Ski-Doo Summit 850", "SKI-SUM-2024-3"),
            ("Polaris RMK 800", "POL-RMK-2024-4")
        ]
        
        for name, sku in ridebase_products:
            product = self.generate_product()
            product["name"] = name
            product["sku"] = sku
            products.append(product)
        
        # Generate remaining products
        for i in range(len(ridebase_products), count):
            products.append(self.generate_product())
        
        return products
    
    def create_csv_dataset(self, products: List[Dict[str, Any]], filename: str = "test_products.csv"):
        """Export products to CSV for import testing"""
        csv_path = self.base_path / filename
        
        fieldnames = [
            "ID", "Type", "SKU", "Name", "Published", "Featured", 
            "Visibility", "Short Description", "Description", "Date Sale From",
            "Date Sale To", "Tax Status", "Tax Class", "In Stock",
            "Stock", "Low Stock Amount", "Backorders", "Sold Individually",
            "Weight", "Length", "Width", "Height", "Allow Reviews",
            "Purchase Note", "Sale Price", "Regular Price", "Categories",
            "Tags", "Shipping Class", "Images", "Download Limit",
            "Download Expiry Days", "Parent", "Grouped Products",
            "Upsells", "Cross-sells", "External URL", "Button Text",
            "Position", "Attribute 1 Name", "Attribute 1 Value",
            "Attribute 2 Name", "Attribute 2 Value", "Attribute 3 Name", 
            "Attribute 3 Value"
        ]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                row = {
                    "ID": product["id"],
                    "Type": product["type"],
                    "SKU": product["sku"],
                    "Name": product["name"],
                    "Published": "1" if product["status"] == "publish" else "0",
                    "Featured": "1" if product["featured"] else "0",
                    "Visibility": product["catalog_visibility"],
                    "Short Description": product["short_description"],
                    "Description": product["description"],
                    "Tax Status": product["tax_status"],
                    "In Stock": "1" if product["stock_status"] == "instock" else "0",
                    "Stock": product["stock_quantity"],
                    "Low Stock Amount": product["low_stock_amount"],
                    "Weight": product["weight"],
                    "Length": product["dimensions"]["length"],
                    "Width": product["dimensions"]["width"],
                    "Height": product["dimensions"]["height"],
                    "Allow Reviews": "1" if product["reviews_allowed"] else "0",
                    "Regular Price": product["regular_price"],
                    "Categories": ", ".join([cat["name"] for cat in product["categories"]]),
                    "Tags": ", ".join([tag["name"] for tag in product["tags"]]),
                    "Images": product["images"][0]["src"] if product["images"] else "",
                    "Attribute 1 Name": product["attributes"][0]["name"] if product["attributes"] else "",
                    "Attribute 1 Value": ", ".join(product["attributes"][0]["options"]) if product["attributes"] else "",
                    "Attribute 2 Name": product["attributes"][1]["name"] if len(product["attributes"]) > 1 else "",
                    "Attribute 2 Value": ", ".join(product["attributes"][1]["options"]) if len(product["attributes"]) > 1 else "",
                    "Attribute 3 Name": product["attributes"][2]["name"] if len(product["attributes"]) > 2 else "",
                    "Attribute 3 Value": ", ".join(product["attributes"][2]["options"]) if len(product["attributes"]) > 2 else ""
                }
                writer.writerow(row)
        
        print(f"CSV dataset created: {csv_path}")
    
    def create_test_scenarios(self):
        """Create specific test scenario datasets"""
        scenarios = {
            "unit_tests": 50,
            "integration_tests": 200,
            "performance_tests": 1000,
            "stress_tests": 5000,
            "edge_cases": 10
        }
        
        for scenario, count in scenarios.items():
            products = self.generate_product_dataset(count)
            
            # Save JSON
            json_path = self.base_path / f"{scenario}_products.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            
            # Save CSV
            self.create_csv_dataset(products, f"{scenario}_products.csv")
            
            print(f"Created {scenario}: {count} products")
    
    def create_edge_case_data(self):
        """Create edge case test data"""
        edge_cases = []
        
        # Empty/minimal product
        minimal = self.generate_product()
        minimal.update({
            "name": "",
            "description": "",
            "price": "0",
            "stock_quantity": 0,
            "weight": ""
        })
        edge_cases.append(minimal)
        
        # Very expensive product
        expensive = self.generate_product()
        expensive.update({
            "name": "Ultra Premium Snowmobile",
            "price": "99999.99",
            "regular_price": "99999.99"
        })
        edge_cases.append(expensive)
        
        # Product with special characters
        special_chars = self.generate_product()
        special_chars.update({
            "name": "Spëçîål Chåråctér§ Tëst Prõdúct™",
            "description": "Product with émojis 🏔️❄️🏂 and special chars: àáâãäåæçèéêë"
        })
        edge_cases.append(special_chars)
        
        # Very long names/descriptions
        long_data = self.generate_product()
        long_data.update({
            "name": "This is an extremely long product name that exceeds normal length limits and tests system boundaries" * 3,
            "description": "Very long description " * 100
        })
        edge_cases.append(long_data)
        
        return edge_cases
    
    def setup_complete_test_environment(self):
        """Set up complete test data environment"""
        print("Setting up complete test data environment...")
        
        # Generate stores
        stores = self.generate_test_stores(8)
        stores_path = self.base_path / "test_stores.json"
        with open(stores_path, 'w', encoding='utf-8') as f:
            json.dump(stores, f, indent=2)
        print(f"Test stores created: {stores_path}")
        
        # Generate test scenarios
        self.create_test_scenarios()
        
        # Create edge cases
        edge_cases = self.create_edge_case_data()
        edge_path = self.base_path / "edge_cases.json"
        with open(edge_path, 'w', encoding='utf-8') as f:
            json.dump(edge_cases, f, indent=2, ensure_ascii=False)
        print(f"Edge cases created: {edge_path}")
        
        # Create mock API responses
        self.create_mock_responses()
        
        print("\nComplete test environment setup finished!")
        print(f"All test data saved to: {self.base_path.absolute()}")
        
    def create_mock_responses(self):
        """Create mock API response files"""
        mock_dir = self.base_path / "mock_responses"
        mock_dir.mkdir(exist_ok=True)
        
        # Mock successful responses
        success_responses = {
            "store_connection_success": {
                "status": "connected",
                "response_time": 0.234,
                "woocommerce_version": "8.2.1",
                "wordpress_version": "6.3.2"
            },
            "product_list_success": {
                "products": self.generate_product_dataset(10),
                "total_count": 27,
                "page": 1,
                "per_page": 10
            },
            "product_update_success": {
                "id": "PROD-1234",
                "status": "updated",
                "changes": ["price", "stock_quantity"]
            }
        }
        
        # Mock error responses
        error_responses = {
            "store_connection_error": {
                "error": "authentication_failed",
                "message": "Invalid consumer key or secret",
                "code": 401
            },
            "product_not_found": {
                "error": "product_not_found",
                "message": "Product with SKU 'INVALID' not found",
                "code": 404
            },
            "rate_limit_exceeded": {
                "error": "rate_limit_exceeded", 
                "message": "Too many requests. Try again later.",
                "code": 429,
                "retry_after": 60
            }
        }
        
        # Save mock responses
        for name, response in {**success_responses, **error_responses}.items():
            mock_path = mock_dir / f"{name}.json"
            with open(mock_path, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2)
        
        print(f"Mock API responses created: {mock_dir}")

def main():
    """Main execution function"""
    generator = TestDataGenerator()
    generator.setup_complete_test_environment()

if __name__ == "__main__":
    main()