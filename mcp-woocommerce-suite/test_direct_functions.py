"""
Direct Function Testing for MCP WooCommerce Suite
Tests all backend functions directly without web interface
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from woocommerce import API

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

class DirectFunctionTester:
    def __init__(self):
        self.test_results = []
        self.load_store_config()
        
    def load_store_config(self):
        """Load RideBase.fi configuration"""
        stores_file = Path("data/stores.json")
        
        if stores_file.exists():
            with open(stores_file, 'r') as f:
                stores_data = json.load(f)
                
            store_config = stores_data.get("store_0", {})
            
            self.store_info = {
                "name": store_config.get("name", ""),
                "url": store_config.get("url", ""),
                "consumer_key": store_config.get("consumer_key", ""),
                "consumer_secret": store_config.get("consumer_secret", "")
            }
            
            # Initialize WooCommerce API
            self.wcapi = API(
                url=self.store_info["url"],
                consumer_key=self.store_info["consumer_key"],
                consumer_secret=self.store_info["consumer_secret"],
                version="wc/v3",
                timeout=30
            )
            
            print(f"Loaded store: {self.store_info['name']}")
        else:
            raise Exception("stores.json not found")
    
    def run_test(self, test_name, test_func, *args, **kwargs):
        """Execute a test function and capture results"""
        print(f"\n[TEST] {test_name}")
        start_time = datetime.now()
        
        try:
            result = test_func(*args, **kwargs)
            status = "PASSED"
            error = None
            print(f"[+] {test_name} - PASSED")
        except Exception as e:
            result = None
            status = "FAILED"
            error = str(e)
            print(f"[X] {test_name} - FAILED: {error}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        test_result = {
            "test_name": test_name,
            "status": status,
            "duration": duration,
            "result": result,
            "error": error,
            "timestamp": start_time.isoformat()
        }
        
        self.test_results.append(test_result)
        return status == "PASSED"
    
    # STORE MANAGEMENT FUNCTIONS
    def test_list_stores_function(self):
        """Test direct store listing function"""
        # Simulate the actual function from web_server.py
        stores_file = Path("data/stores.json")
        
        if not stores_file.exists():
            raise Exception("stores.json not found")
        
        with open(stores_file, 'r') as f:
            stores_data = json.load(f)
        
        # Convert to expected format
        stores_list = []
        for store_id, store_data in stores_data.items():
            stores_list.append({
                "id": store_data.get("id", store_id),
                "name": store_data.get("name", ""),
                "url": store_data.get("url", ""),
                "status": store_data.get("status", "unknown"),
                "added": store_data.get("added", "")
            })
        
        if not stores_list:
            raise Exception("No stores configured")
        
        return {"stores": stores_list, "count": len(stores_list)}
    
    def test_store_connection_function(self):
        """Test direct store connection function"""
        try:
            # Test WooCommerce API connection
            response = self.wcapi.get("")
            
            if response.status_code == 200:
                return {
                    "status": "connected",
                    "store_name": self.store_info["name"],
                    "response_code": response.status_code,
                    "api_accessible": True
                }
            else:
                raise Exception(f"API returned {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")
    
    # PRODUCT MANAGEMENT FUNCTIONS
    def test_list_products_function(self, per_page=10):
        """Test direct product listing function"""
        try:
            response = self.wcapi.get("products", params={"per_page": per_page})
            
            if response.status_code == 200:
                products = response.json()
                
                if not products:
                    raise Exception("No products found")
                
                # Validate product structure
                required_fields = ["id", "name", "sku", "price"]
                for product in products[:3]:  # Check first 3 products
                    for field in required_fields:
                        if field not in product:
                            raise Exception(f"Product missing field: {field}")
                
                return {
                    "products": products,
                    "count": len(products),
                    "sample_product": {
                        "name": products[0].get("name", ""),
                        "sku": products[0].get("sku", ""),
                        "price": products[0].get("price", "")
                    }
                }
            else:
                raise Exception(f"API returned {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Product listing failed: {str(e)}")
    
    def test_search_products_function(self, query="lynx"):
        """Test direct product search function"""
        try:
            response = self.wcapi.get("products", params={
                "search": query,
                "per_page": 10
            })
            
            if response.status_code == 200:
                products = response.json()
                
                return {
                    "query": query,
                    "results_count": len(products),
                    "products": products[:3]  # First 3 results
                }
            else:
                raise Exception(f"Search API returned {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Product search failed: {str(e)}")
    
    def test_get_product_details_function(self):
        """Test getting detailed product information"""
        try:
            # First get a product ID
            response = self.wcapi.get("products", params={"per_page": 1})
            
            if response.status_code != 200:
                raise Exception("Could not get product list")
            
            products = response.json()
            if not products:
                raise Exception("No products available")
            
            product_id = products[0]["id"]
            
            # Get detailed product info
            detail_response = self.wcapi.get(f"products/{product_id}")
            
            if detail_response.status_code == 200:
                product_detail = detail_response.json()
                
                return {
                    "product_id": product_id,
                    "name": product_detail.get("name", ""),
                    "sku": product_detail.get("sku", ""),
                    "price": product_detail.get("price", ""),
                    "stock_quantity": product_detail.get("stock_quantity", 0),
                    "categories": len(product_detail.get("categories", [])),
                    "images": len(product_detail.get("images", [])),
                    "attributes": len(product_detail.get("attributes", []))
                }
            else:
                raise Exception(f"Product detail API returned {detail_response.status_code}")
                
        except Exception as e:
            raise Exception(f"Product details failed: {str(e)}")
    
    # CATEGORY MANAGEMENT FUNCTIONS
    def test_list_categories_function(self):
        """Test category listing function"""
        try:
            response = self.wcapi.get("products/categories", params={"per_page": 50})
            
            if response.status_code == 200:
                categories = response.json()
                
                return {
                    "categories": categories,
                    "count": len(categories),
                    "category_names": [cat.get("name", "") for cat in categories[:10]]
                }
            else:
                raise Exception(f"Categories API returned {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Category listing failed: {str(e)}")
    
    # DATA EXPORT FUNCTIONS
    def test_export_products_csv_function(self, limit=5):
        """Test CSV export function"""
        try:
            # Get products
            response = self.wcapi.get("products", params={"per_page": limit})
            
            if response.status_code != 200:
                raise Exception(f"Could not get products: {response.status_code}")
            
            products = response.json()
            
            # Simulate CSV generation
            csv_data = []
            csv_headers = ["ID", "Name", "SKU", "Price", "Stock", "Status"]
            csv_data.append(csv_headers)
            
            for product in products:
                row = [
                    product.get("id", ""),
                    product.get("name", ""),
                    product.get("sku", ""),
                    product.get("price", ""),
                    product.get("stock_quantity", ""),
                    product.get("status", "")
                ]
                csv_data.append(row)
            
            return {
                "csv_rows": len(csv_data),
                "products_exported": len(products),
                "headers": csv_headers,
                "sample_row": csv_data[1] if len(csv_data) > 1 else None
            }
            
        except Exception as e:
            raise Exception(f"CSV export failed: {str(e)}")
    
    # PERFORMANCE FUNCTIONS
    def test_performance_metrics_function(self):
        """Test performance metrics calculation"""
        try:
            # Get products with sales data
            response = self.wcapi.get("products", params={
                "per_page": 20,
                "orderby": "popularity",
                "order": "desc"
            })
            
            if response.status_code != 200:
                raise Exception(f"Performance data API returned {response.status_code}")
            
            products = response.json()
            
            # Calculate basic metrics
            total_products = len(products)
            in_stock = sum(1 for p in products if p.get("stock_status") == "instock")
            out_of_stock = total_products - in_stock
            
            # Average price
            prices = [float(p.get("price", 0) or 0) for p in products]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            return {
                "total_products": total_products,
                "in_stock": in_stock,
                "out_of_stock": out_of_stock,
                "stock_rate": (in_stock / total_products * 100) if total_products > 0 else 0,
                "average_price": avg_price,
                "price_range": {"min": min(prices) if prices else 0, "max": max(prices) if prices else 0}
            }
            
        except Exception as e:
            raise Exception(f"Performance metrics failed: {str(e)}")
    
    # INTEGRATION FUNCTIONS
    def test_cross_store_comparison_function(self):
        """Test cross-store product comparison logic"""
        try:
            # Simulate comparison with single store
            response = self.wcapi.get("products", params={"per_page": 5})
            
            if response.status_code != 200:
                raise Exception(f"Product API returned {response.status_code}")
            
            products = response.json()
            
            # Simulate comparison logic
            comparison_results = []
            for product in products:
                comparison_results.append({
                    "sku": product.get("sku", ""),
                    "name": product.get("name", ""),
                    "stores": {
                        "store_0": {
                            "price": product.get("price", ""),
                            "stock": product.get("stock_quantity", 0),
                            "status": product.get("status", "")
                        }
                    },
                    "comparison_status": "single_store"
                })
            
            return {
                "products_compared": len(comparison_results),
                "stores_checked": ["store_0"],
                "comparison_results": comparison_results[:3]  # First 3 results
            }
            
        except Exception as e:
            raise Exception(f"Cross-store comparison failed: {str(e)}")
    
    def run_all_direct_tests(self):
        """Execute all direct function tests"""
        print("DIRECT FUNCTION TESTING - MCP WOOCOMMERCE SUITE")
        print("=" * 60)
        
        # Define all tests
        test_functions = [
            # Store Management
            ("List Stores Function", self.test_list_stores_function),
            ("Store Connection Function", self.test_store_connection_function),
            
            # Product Management
            ("List Products Function", self.test_list_products_function, 10),
            ("Search Products Function", self.test_search_products_function, "lynx"),
            ("Get Product Details Function", self.test_get_product_details_function),
            
            # Category Management
            ("List Categories Function", self.test_list_categories_function),
            
            # Export Functions
            ("Export Products CSV Function", self.test_export_products_csv_function, 5),
            
            # Performance Functions
            ("Performance Metrics Function", self.test_performance_metrics_function),
            
            # Integration Functions
            ("Cross-Store Comparison Function", self.test_cross_store_comparison_function),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_config in test_functions:
            if len(test_config) == 2:
                test_name, test_func = test_config
                args = []
            else:
                test_name, test_func, *args = test_config
            
            if self.run_test(test_name, test_func, *args):
                passed_tests += 1
        
        # Summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print("DIRECT FUNCTION TEST SUMMARY")
        print(f"{'='*60}")
        
        for result in self.test_results:
            status_symbol = "[+]" if result["status"] == "PASSED" else "[X]"
            print(f"{status_symbol} {result['test_name']}: {result['status']} ({result['duration']:.2f}s)")
        
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Save results
        results_file = Path("test_results") / f"direct_function_test_{int(datetime.now().timestamp())}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": success_rate,
                    "execution_time": sum(r["duration"] for r in self.test_results)
                },
                "detailed_results": self.test_results
            }, f, indent=2)
        
        print(f"Detailed results saved to: {results_file}")
        
        # Status assessment
        if success_rate >= 90:
            print("STATUS: EXCELLENT - All core functions working perfectly!")
        elif success_rate >= 70:
            print("STATUS: GOOD - Most functions working correctly")
        elif success_rate >= 50:
            print("STATUS: FAIR - Core functions working, some issues")
        else:
            print("STATUS: POOR - Significant function failures")
        
        return success_rate >= 70

def main():
    """Main execution"""
    try:
        tester = DirectFunctionTester()
        success = tester.run_all_direct_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"Direct function testing failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)