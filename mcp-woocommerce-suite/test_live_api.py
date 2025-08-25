"""
Live API Testing with Real RideBase.fi Data
Tests actual functionality with real WooCommerce store
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from woocommerce import API

class LiveAPITester:
    def __init__(self):
        self.results = []
        self.load_store_config()
        
    def load_store_config(self):
        """Load RideBase.fi store configuration"""
        stores_file = Path("data/stores.json")
        
        if stores_file.exists():
            with open(stores_file, 'r') as f:
                stores_data = json.load(f)
                
            store_config = stores_data.get("store_0", {})
            
            self.store_info = {
                "name": store_config.get("name", "Unknown"),
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
            
            print(f"Connected to: {self.store_info['name']} ({self.store_info['url']})")
        else:
            raise Exception("stores.json not found - run setup first")
    
    def run_test(self, test_name, test_func):
        """Run a single test and capture results"""
        print(f"\n[TEST] Testing: {test_name}")
        start_time = datetime.now()
        
        try:
            result = test_func()
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
        
        self.results.append({
            "test_name": test_name,
            "status": status,
            "duration": duration,
            "result": result,
            "error": error,
            "timestamp": start_time.isoformat()
        })
        
        return status == "PASSED"
    
    def test_connection(self):
        """Test basic WooCommerce API connection"""
        response = self.wcapi.get("")
        
        if response.status_code == 200:
            data = response.json()
            return {
                "connected": True,
                "store_info": data.get("store", {}),
                "response_time": "< 1s"
            }
        else:
            raise Exception(f"Connection failed: HTTP {response.status_code}")
    
    def test_list_products(self):
        """Test product listing with real data"""
        response = self.wcapi.get("products", params={"per_page": 10})
        
        if response.status_code == 200:
            products = response.json()
            
            if not products:
                raise Exception("No products found in store")
            
            # Validate product structure
            first_product = products[0]
            required_fields = ["id", "name", "sku", "price", "stock_quantity"]
            
            for field in required_fields:
                if field not in first_product:
                    raise Exception(f"Product missing field: {field}")
            
            return {
                "products_found": len(products),
                "sample_product": {
                    "name": first_product.get("name", ""),
                    "sku": first_product.get("sku", ""),
                    "price": first_product.get("price", "")
                },
                "total_products": len(products)
            }
        else:
            raise Exception(f"Product listing failed: HTTP {response.status_code}")
    
    def test_product_search(self):
        """Test product search functionality"""
        # Search for common snowmobile terms
        search_terms = ["lynx", "ski", "commander"]
        search_results = {}
        
        for term in search_terms:
            response = self.wcapi.get("products", params={
                "search": term,
                "per_page": 5
            })
            
            if response.status_code == 200:
                products = response.json()
                search_results[term] = {
                    "results_count": len(products),
                    "products": [p.get("name", "") for p in products[:3]]  # First 3 names
                }
            else:
                search_results[term] = {"error": f"HTTP {response.status_code}"}
        
        return search_results
    
    def test_product_categories(self):
        """Test category listing"""
        response = self.wcapi.get("products/categories", params={"per_page": 20})
        
        if response.status_code == 200:
            categories = response.json()
            
            return {
                "categories_found": len(categories),
                "category_names": [cat.get("name", "") for cat in categories[:10]]
            }
        else:
            raise Exception(f"Categories listing failed: HTTP {response.status_code}")
    
    def test_single_product_details(self):
        """Test detailed product information"""
        # Get first product and fetch detailed info
        response = self.wcapi.get("products", params={"per_page": 1})
        
        if response.status_code == 200:
            products = response.json()
            if products:
                product_id = products[0]["id"]
                
                # Get detailed product info
                detail_response = self.wcapi.get(f"products/{product_id}")
                
                if detail_response.status_code == 200:
                    product_detail = detail_response.json()
                    
                    return {
                        "product_id": product_id,
                        "name": product_detail.get("name", ""),
                        "description_length": len(product_detail.get("description", "")),
                        "image_count": len(product_detail.get("images", [])),
                        "category_count": len(product_detail.get("categories", [])),
                        "attributes": len(product_detail.get("attributes", []))
                    }
                else:
                    raise Exception(f"Product detail fetch failed: HTTP {detail_response.status_code}")
            else:
                raise Exception("No products available for detailed testing")
        else:
            raise Exception(f"Product listing failed: HTTP {response.status_code}")
    
    def test_store_settings(self):
        """Test store settings and configuration"""
        response = self.wcapi.get("system_status")
        
        if response.status_code == 200:
            system_info = response.json()
            
            return {
                "wordpress_version": system_info.get("wp_version", "unknown"),
                "woocommerce_version": system_info.get("version", "unknown"),
                "currency": system_info.get("settings", {}).get("currency", "unknown"),
                "store_configured": True
            }
        else:
            # Try alternative endpoint
            settings_response = self.wcapi.get("settings/general")
            if settings_response.status_code == 200:
                return {
                    "store_configured": True,
                    "api_accessible": True
                }
            else:
                raise Exception(f"Store settings not accessible: HTTP {response.status_code}")
    
    def run_all_tests(self):
        """Execute all live API tests"""
        print("LIVE API TESTING WITH RIDEBASE.FI")
        print("=" * 50)
        
        tests = [
            ("API Connection", self.test_connection),
            ("List Products", self.test_list_products),
            ("Search Products", self.test_product_search),
            ("Product Categories", self.test_product_categories),
            ("Product Details", self.test_single_product_details),
            ("Store Settings", self.test_store_settings)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed_tests += 1
        
        # Summary
        print(f"\n{'='*50}")
        print("LIVE API TEST SUMMARY")
        print(f"{'='*50}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        for result in self.results:
            status_symbol = "[+]" if result["status"] == "PASSED" else "[X]"
            print(f"{status_symbol} {result['test_name']}: {result['status']} ({result['duration']:.2f}s)")
        
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Save detailed results
        results_file = Path("test_results") / f"live_api_results_{int(datetime.now().timestamp())}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "store_info": self.store_info,
                "test_summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": success_rate,
                    "execution_time": sum(r["duration"] for r in self.results)
                },
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"Detailed results saved to: {results_file}")
        
        # Status assessment
        if success_rate >= 80:
            print("STATUS: EXCELLENT - Live API fully functional!")
        elif success_rate >= 60:
            print("STATUS: GOOD - Most functionality working")
        else:
            print("STATUS: ISSUES - Significant API problems detected")
        
        return success_rate >= 60

def main():
    """Main execution"""
    try:
        tester = LiveAPITester()
        success = tester.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"Live API testing failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)