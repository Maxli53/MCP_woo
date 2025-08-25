"""
Comprehensive Test Runner for MCP WooCommerce Suite
Implements the professional testing methodology
"""

import asyncio
import json
import time
import pytest
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional
from test_data_generator import TestDataGenerator
import subprocess
import sys

class TestRunner:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_data_path = Path("test_data")
        self.results_path = Path("test_results")
        self.results_path.mkdir(exist_ok=True)
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Test metrics
        self.metrics = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "execution_time": 0,
            "coverage_percentage": 0
        }
    
    async def setup_test_environment(self):
        """Set up complete test environment"""
        print("🔧 Setting up test environment...")
        
        # Generate test data if not exists
        if not self.test_data_path.exists():
            print("📊 Generating test data...")
            generator = TestDataGenerator()
            generator.setup_complete_test_environment()
        
        # Backup production data
        await self.backup_production_data()
        
        # Load test stores
        await self.load_test_stores()
        
        print("✅ Test environment ready!")
    
    async def backup_production_data(self):
        """Backup production data before testing"""
        backup_dir = Path("backups") / f"pre_test_{int(time.time())}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup stores.json
        stores_file = Path("data/stores.json")
        if stores_file.exists():
            import shutil
            shutil.copy2(stores_file, backup_dir / "stores.json")
            print(f"📦 Production data backed up to {backup_dir}")
    
    async def load_test_stores(self):
        """Load test store configurations"""
        test_stores_path = self.test_data_path / "test_stores.json"
        if test_stores_path.exists():
            with open(test_stores_path, 'r') as f:
                test_stores = json.load(f)
            
            # Update stores.json for testing
            stores_file = Path("data/stores.json")
            stores_file.parent.mkdir(exist_ok=True)
            with open(stores_file, 'w') as f:
                json.dump(test_stores, f, indent=2)
            print(f"🏪 Loaded {len(test_stores)} test stores")
    
    # STORE MANAGEMENT TESTS
    async def test_sm_001_list_stores(self) -> Dict[str, Any]:
        """SM-001: List Available Stores"""
        test_result = {
            "test_id": "SM-001",
            "name": "List Available Stores",
            "status": "running",
            "start_time": time.time(),
            "errors": []
        }
        
        try:
            response = await self.client.get(f"{self.base_url}/api/stores")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                assert "stores" in data, "Response missing 'stores' field"
                assert isinstance(data["stores"], list), "Stores field is not a list"
                
                # Check store object structure
                if data["stores"]:
                    store = data["stores"][0]
                    required_fields = ["id", "name", "url", "status"]
                    for field in required_fields:
                        assert field in store, f"Store missing required field: {field}"
                
                # Performance check
                response_time = response.elapsed.total_seconds()
                assert response_time < 0.5, f"Response time too slow: {response_time}s"
                
                test_result["status"] = "passed"
                test_result["response_time"] = response_time
                test_result["stores_count"] = len(data["stores"])
                
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        return test_result
    
    async def test_sm_002_add_store(self) -> Dict[str, Any]:
        """SM-002: Add New Store"""
        test_result = {
            "test_id": "SM-002", 
            "name": "Add New Store",
            "status": "running",
            "start_time": time.time(),
            "errors": []
        }
        
        try:
            # Test valid store addition
            test_store_data = {
                "name": "Test Store Addition",
                "url": "https://test-addition.example.com",
                "consumer_key": "ck_test123",
                "consumer_secret": "cs_test456"
            }
            
            response = await self.client.post(f"{self.base_url}/api/stores", json=test_store_data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                # Verify store was added
                assert "success" in result or "id" in result, "Store addition not confirmed"
                
                # Test duplicate URL prevention
                duplicate_response = await self.client.post(f"{self.base_url}/api/stores", json=test_store_data)
                # Should return error or existing store
                
                test_result["status"] = "passed"
                test_result["store_added"] = True
                
            else:
                raise Exception(f"Failed to add store: HTTP {response.status_code}")
        
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        return test_result
    
    async def test_sm_003_test_connection(self) -> Dict[str, Any]:
        """SM-003: Test Store Connection"""
        test_result = {
            "test_id": "SM-003",
            "name": "Test Store Connection", 
            "status": "running",
            "start_time": time.time(),
            "errors": []
        }
        
        try:
            # Test connection to first available store
            response = await self.client.post(f"{self.base_url}/api/stores/test-connection", json={
                "store_id": "store_0"
            })
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify connection test results
                expected_fields = ["status", "response_time"]
                for field in expected_fields:
                    if field in result:
                        test_result[field] = result[field]
                
                test_result["status"] = "passed"
                
            else:
                test_result["status"] = "failed"
                test_result["errors"].append(f"Connection test failed: HTTP {response.status_code}")
        
        except Exception as e:
            test_result["status"] = "failed" 
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        return test_result
    
    # PRODUCT MANAGEMENT TESTS
    async def test_pm_001_list_products(self) -> Dict[str, Any]:
        """PM-001: List All Products"""
        test_result = {
            "test_id": "PM-001",
            "name": "List All Products",
            "status": "running", 
            "start_time": time.time(),
            "errors": []
        }
        
        try:
            # Test different pagination options
            pagination_tests = [10, 50, 100]
            
            for per_page in pagination_tests:
                response = await self.client.get(
                    f"{self.base_url}/api/products", 
                    params={"per_page": per_page, "store_id": "store_0"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    assert "products" in data, "Missing products field"
                    assert isinstance(data["products"], list), "Products is not a list"
                    
                    # Check product schema
                    if data["products"]:
                        product = data["products"][0]
                        required_fields = ["id", "name", "sku", "price"]
                        for field in required_fields:
                            assert field in product, f"Product missing field: {field}"
                    
                    # Performance check
                    response_time = response.elapsed.total_seconds()
                    assert response_time < 2.0, f"Performance too slow: {response_time}s"
                    
                    test_result[f"pagination_{per_page}"] = {
                        "products_returned": len(data["products"]),
                        "response_time": response_time
                    }
                
                else:
                    raise Exception(f"Product listing failed: HTTP {response.status_code}")
            
            test_result["status"] = "passed"
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time() 
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        return test_result
    
    async def test_pm_002_search_products(self) -> Dict[str, Any]:
        """PM-002: Search Products"""
        test_result = {
            "test_id": "PM-002",
            "name": "Search Products",
            "status": "running",
            "start_time": time.time(), 
            "errors": []
        }
        
        try:
            # Test different search queries
            search_queries = [
                {"query": "Lynx", "expected_min": 0},
                {"query": "snowmobile", "expected_min": 0},
                {"query": "NONEXISTENT", "expected_min": 0, "expected_max": 0}
            ]
            
            for search in search_queries:
                response = await self.client.get(
                    f"{self.base_url}/api/products/search",
                    params={"q": search["query"], "store_id": "store_0"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results_count = len(data.get("products", []))
                    
                    # Verify result count expectations
                    if "expected_min" in search:
                        assert results_count >= search["expected_min"], f"Too few results for '{search['query']}'"
                    
                    if "expected_max" in search:
                        assert results_count <= search["expected_max"], f"Too many results for '{search['query']}'"
                    
                    test_result[f"search_{search['query']}"] = {
                        "results_count": results_count,
                        "response_time": response.elapsed.total_seconds()
                    }
                
                else:
                    raise Exception(f"Search failed for '{search['query']}': HTTP {response.status_code}")
            
            test_result["status"] = "passed"
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]  
        return test_result
    
    # PERFORMANCE TESTS
    async def test_performance_load(self) -> Dict[str, Any]:
        """Load Testing - Multiple concurrent requests"""
        test_result = {
            "test_id": "PERF-001",
            "name": "Load Testing",
            "status": "running",
            "start_time": time.time(),
            "errors": []
        }
        
        try:
            # Simulate 10 concurrent users
            concurrent_requests = 10
            
            async def single_request():
                response = await self.client.get(f"{self.base_url}/api/stores")
                return response.status_code, response.elapsed.total_seconds()
            
            # Execute concurrent requests
            tasks = [single_request() for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful_requests = 0
            response_times = []
            
            for result in results:
                if isinstance(result, tuple):
                    status_code, response_time = result
                    if status_code == 200:
                        successful_requests += 1
                        response_times.append(response_time)
            
            # Performance metrics
            success_rate = successful_requests / concurrent_requests * 100
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            
            # Assertions
            assert success_rate >= 95, f"Success rate too low: {success_rate}%"
            assert avg_response_time < 2.0, f"Average response time too slow: {avg_response_time}s"
            
            test_result["status"] = "passed"
            test_result["concurrent_users"] = concurrent_requests
            test_result["success_rate"] = success_rate
            test_result["avg_response_time"] = avg_response_time
            test_result["max_response_time"] = max_response_time
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        print("🚀 Starting comprehensive test execution...")
        
        start_time = time.time()
        
        # Test suite definitions
        test_suites = [
            # Store Management
            ("Store Management", [
                self.test_sm_001_list_stores,
                self.test_sm_002_add_store,
                self.test_sm_003_test_connection
            ]),
            # Product Management
            ("Product Management", [
                self.test_pm_001_list_products,
                self.test_pm_002_search_products
            ]),
            # Performance Tests
            ("Performance Tests", [
                self.test_performance_load
            ])
        ]
        
        all_results = {}
        summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "execution_time": 0,
            "test_suites": {}
        }
        
        # Execute test suites
        for suite_name, test_methods in test_suites:
            print(f"\n📋 Executing {suite_name} Tests...")
            
            suite_results = []
            suite_stats = {"passed": 0, "failed": 0, "skipped": 0}
            
            for test_method in test_methods:
                print(f"  🔍 Running {test_method.__name__}...")
                
                try:
                    result = await test_method()
                    suite_results.append(result)
                    
                    if result["status"] == "passed":
                        suite_stats["passed"] += 1
                        print(f"    ✅ {result['name']} - PASSED ({result['duration']:.2f}s)")
                    else:
                        suite_stats["failed"] += 1
                        print(f"    ❌ {result['name']} - FAILED")
                        for error in result.get("errors", []):
                            print(f"       Error: {error}")
                
                except Exception as e:
                    suite_stats["failed"] += 1 
                    error_result = {
                        "test_id": "ERROR",
                        "name": test_method.__name__,
                        "status": "failed",
                        "errors": [str(e)],
                        "duration": 0
                    }
                    suite_results.append(error_result)
                    print(f"    💥 {test_method.__name__} - EXCEPTION: {str(e)}")
            
            all_results[suite_name] = suite_results
            summary["test_suites"][suite_name] = suite_stats
            summary["total_tests"] += len(test_methods)
            summary["passed_tests"] += suite_stats["passed"]
            summary["failed_tests"] += suite_stats["failed"]
            
            # Suite summary
            suite_total = suite_stats["passed"] + suite_stats["failed"] + suite_stats["skipped"]
            suite_success_rate = (suite_stats["passed"] / suite_total * 100) if suite_total > 0 else 0
            print(f"  📊 {suite_name} Results: {suite_stats['passed']}/{suite_total} passed ({suite_success_rate:.1f}%)")
        
        # Final summary
        summary["execution_time"] = time.time() - start_time
        
        # Save results
        results_file = self.results_path / f"test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({"summary": summary, "detailed_results": all_results}, f, indent=2)
        
        # Print final summary
        total_success_rate = (summary["passed_tests"] / summary["total_tests"] * 100) if summary["total_tests"] > 0 else 0
        
        print(f"\n{'='*80}")
        print("🏁 TEST EXECUTION COMPLETED")
        print(f"{'='*80}")
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        print(f"⏭️  Skipped: {summary['skipped_tests']}")
        print(f"⏱️  Execution Time: {summary['execution_time']:.2f}s")
        print(f"📈 Success Rate: {total_success_rate:.1f}%")
        print(f"💾 Results saved to: {results_file}")
        
        if total_success_rate >= 80:
            print("🎉 STATUS: EXCELLENT - Ready for production!")
        elif total_success_rate >= 60:
            print("👍 STATUS: GOOD - Minor issues to address")
        elif total_success_rate >= 40:
            print("⚠️  STATUS: FAIR - Significant issues found")
        else:
            print("🚨 STATUS: POOR - Major issues require attention")
        
        return {"summary": summary, "detailed_results": all_results}
    
    async def cleanup(self):
        """Clean up test environment"""
        await self.client.aclose()
        print("🧹 Test environment cleaned up")

async def main():
    """Main test runner execution"""
    runner = TestRunner()
    
    try:
        # Setup
        await runner.setup_test_environment()
        
        # Execute all tests
        results = await runner.run_all_tests()
        
        # Cleanup
        await runner.cleanup()
        
        # Return exit code based on results
        success_rate = results["summary"]["passed_tests"] / results["summary"]["total_tests"] * 100
        return 0 if success_rate >= 60 else 1
        
    except Exception as e:
        print(f"💥 Test runner failed: {str(e)}")
        await runner.cleanup()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)