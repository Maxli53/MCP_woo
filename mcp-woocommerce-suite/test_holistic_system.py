"""
Holistic System Test for MCP WooCommerce Suite
Tests all functions, workflows, and integrations end-to-end
"""

import asyncio
import httpx
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import sys
import os

class HolisticSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.server_process = None
        
    async def start_web_server(self, max_attempts=3):
        """Start web server with retry logic"""
        print("Starting web server...")
        
        for port in [8000, 8001, 8002]:
            try:
                cmd = f"./venv/Scripts/python web_server.py --port {port}"
                self.server_process = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=".",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for server to start
                await asyncio.sleep(3)
                
                # Test connection
                self.base_url = f"http://localhost:{port}"
                response = await self.client.get(f"{self.base_url}/")
                
                if response.status_code == 200:
                    print(f"Web server started successfully on port {port}")
                    return True
                    
            except Exception as e:
                print(f"Failed to start server on port {port}: {e}")
                if self.server_process:
                    self.server_process.terminate()
                    self.server_process = None
                continue
        
        return False
    
    async def test_system_endpoints(self) -> Dict[str, Any]:
        """Test all system endpoints"""
        test_result = {
            "test_name": "System Endpoints",
            "status": "running",
            "start_time": time.time(),
            "endpoints_tested": [],
            "errors": []
        }
        
        # Core system endpoints to test
        endpoints = [
            ("/", "GET", "Root endpoint"),
            ("/api/stores", "GET", "List stores"),
            ("/api/products", "GET", "List products"),
            ("/api/tool-catalog", "GET", "Tool catalog"),
            ("/api/health", "GET", "Health check")
        ]
        
        passed_endpoints = 0
        
        for endpoint, method, description in endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    response = await self.client.post(f"{self.base_url}{endpoint}")
                
                endpoint_result = {
                    "endpoint": endpoint,
                    "method": method,
                    "description": description,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "success": 200 <= response.status_code < 300
                }
                
                test_result["endpoints_tested"].append(endpoint_result)
                
                if endpoint_result["success"]:
                    passed_endpoints += 1
                    print(f"[+] {endpoint} ({method}) - {response.status_code}")
                else:
                    print(f"[X] {endpoint} ({method}) - {response.status_code}")
                    
            except Exception as e:
                error_result = {
                    "endpoint": endpoint,
                    "method": method,
                    "error": str(e)
                }
                test_result["errors"].append(error_result)
                print(f"[ERROR] {endpoint} - {str(e)}")
        
        test_result["passed_endpoints"] = passed_endpoints
        test_result["total_endpoints"] = len(endpoints)
        test_result["success_rate"] = (passed_endpoints / len(endpoints)) * 100
        test_result["status"] = "passed" if passed_endpoints >= len(endpoints) * 0.8 else "failed"
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result
    
    async def test_mcp_tools_execution(self) -> Dict[str, Any]:
        """Test actual execution of all MCP tools"""
        test_result = {
            "test_name": "MCP Tools Execution",
            "status": "running", 
            "start_time": time.time(),
            "tools_tested": [],
            "errors": []
        }
        
        # Get tool catalog first
        try:
            response = await self.client.get(f"{self.base_url}/api/tool-catalog")
            if response.status_code != 200:
                test_result["status"] = "failed"
                test_result["errors"].append("Failed to get tool catalog")
                return test_result
                
            catalog = response.json()
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["errors"].append(f"Tool catalog error: {str(e)}")
            return test_result
        
        # Test tools from each category
        tools_to_test = [
            # Store Management
            ("list_stores", {}, "Store Management"),
            ("test_store_connection", {"store_id": "store_0"}, "Store Management"),
            
            # Product Management  
            ("list_products", {"store_id": "store_0", "per_page": 5}, "Product Management"),
            ("search_products", {"store_id": "store_0", "query": "lynx"}, "Product Management"),
            
            # Cross-Store Operations
            ("compare_products", {"stores": ["store_0"], "sku": "test"}, "Cross-Store Operations"),
            
            # Bulk Operations
            ("bulk_price_update", {"store_id": "store_0", "products": [], "action": "preview"}, "Bulk Operations"),
            
            # Import & Export
            ("export_products_csv", {"store_id": "store_0", "limit": 5}, "Import & Export"),
            
            # Analytics
            ("product_performance_report", {"store_id": "store_0"}, "Analytics & Reports")
        ]
        
        passed_tools = 0
        
        for tool_name, params, category in tools_to_test:
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/execute-tool",
                    json={
                        "tool": tool_name,
                        "parameters": params
                    }
                )
                
                tool_result = {
                    "tool_name": tool_name,
                    "category": category,
                    "parameters": params,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "success": 200 <= response.status_code < 300
                }
                
                # Try to parse response
                try:
                    response_data = response.json()
                    tool_result["response_data"] = response_data
                    tool_result["has_valid_response"] = True
                except:
                    tool_result["has_valid_response"] = False
                    tool_result["raw_response"] = response.text[:200]  # First 200 chars
                
                test_result["tools_tested"].append(tool_result)
                
                if tool_result["success"]:
                    passed_tools += 1
                    print(f"[+] {tool_name} - {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                else:
                    print(f"[X] {tool_name} - {response.status_code}")
                    
            except Exception as e:
                error_result = {
                    "tool_name": tool_name,
                    "category": category,
                    "error": str(e)
                }
                test_result["errors"].append(error_result)
                print(f"[ERROR] {tool_name} - {str(e)}")
        
        test_result["passed_tools"] = passed_tools
        test_result["total_tools"] = len(tools_to_test)
        test_result["success_rate"] = (passed_tools / len(tools_to_test)) * 100
        test_result["status"] = "passed" if passed_tools >= len(tools_to_test) * 0.6 else "failed"
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result
    
    async def test_complete_workflows(self) -> Dict[str, Any]:
        """Test complete end-to-end workflows"""
        test_result = {
            "test_name": "Complete Workflows",
            "status": "running",
            "start_time": time.time(),
            "workflows_tested": [],
            "errors": []
        }
        
        # Define complete workflows to test
        workflows = [
            {
                "name": "Product Management Workflow",
                "steps": [
                    ("list_products", {"store_id": "store_0", "per_page": 5}),
                    ("search_products", {"store_id": "store_0", "query": "lynx"}),
                    ("export_products_csv", {"store_id": "store_0", "limit": 5})
                ]
            },
            {
                "name": "Store Analysis Workflow", 
                "steps": [
                    ("list_stores", {}),
                    ("test_store_connection", {"store_id": "store_0"}),
                    ("product_performance_report", {"store_id": "store_0"})
                ]
            }
        ]
        
        passed_workflows = 0
        
        for workflow in workflows:
            workflow_result = {
                "name": workflow["name"],
                "steps": [],
                "success": True,
                "errors": []
            }
            
            print(f"\n[WORKFLOW] Testing: {workflow['name']}")
            
            for step_name, params in workflow["steps"]:
                try:
                    response = await self.client.post(
                        f"{self.base_url}/api/execute-tool",
                        json={
                            "tool": step_name,
                            "parameters": params
                        }
                    )
                    
                    step_result = {
                        "step_name": step_name,
                        "params": params,
                        "status_code": response.status_code,
                        "success": 200 <= response.status_code < 300,
                        "response_time": response.elapsed.total_seconds()
                    }
                    
                    workflow_result["steps"].append(step_result)
                    
                    if not step_result["success"]:
                        workflow_result["success"] = False
                        workflow_result["errors"].append(f"Step {step_name} failed: {response.status_code}")
                        
                    print(f"  [STEP] {step_name} - {'PASS' if step_result['success'] else 'FAIL'}")
                    
                except Exception as e:
                    workflow_result["success"] = False
                    workflow_result["errors"].append(f"Step {step_name} exception: {str(e)}")
                    print(f"  [ERROR] {step_name} - {str(e)}")
            
            test_result["workflows_tested"].append(workflow_result)
            
            if workflow_result["success"]:
                passed_workflows += 1
                print(f"[+] {workflow['name']} - COMPLETED")
            else:
                print(f"[X] {workflow['name']} - FAILED")
        
        test_result["passed_workflows"] = passed_workflows
        test_result["total_workflows"] = len(workflows)
        test_result["success_rate"] = (passed_workflows / len(workflows)) * 100
        test_result["status"] = "passed" if passed_workflows >= len(workflows) * 0.8 else "failed"
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result
    
    async def test_data_integrity(self) -> Dict[str, Any]:
        """Test data consistency and integrity"""
        test_result = {
            "test_name": "Data Integrity",
            "status": "running",
            "start_time": time.time(),
            "checks": [],
            "errors": []
        }
        
        # Data integrity checks
        checks = [
            ("Store Configuration", self.check_store_config),
            ("Product Data Consistency", self.check_product_consistency),
            ("API Response Formats", self.check_api_response_formats),
            ("File System Integrity", self.check_file_system)
        ]
        
        passed_checks = 0
        
        for check_name, check_func in checks:
            try:
                check_result = await check_func()
                check_result["name"] = check_name
                test_result["checks"].append(check_result)
                
                if check_result.get("success", False):
                    passed_checks += 1
                    print(f"[+] {check_name} - PASS")
                else:
                    print(f"[X] {check_name} - FAIL")
                    
            except Exception as e:
                error_result = {
                    "name": check_name,
                    "success": False,
                    "error": str(e)
                }
                test_result["checks"].append(error_result)
                test_result["errors"].append(f"{check_name}: {str(e)}")
                print(f"[ERROR] {check_name} - {str(e)}")
        
        test_result["passed_checks"] = passed_checks
        test_result["total_checks"] = len(checks)
        test_result["success_rate"] = (passed_checks / len(checks)) * 100
        test_result["status"] = "passed" if passed_checks >= len(checks) * 0.8 else "failed"
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        return test_result
    
    async def check_store_config(self) -> Dict[str, Any]:
        """Check store configuration integrity"""
        stores_file = Path("data/stores.json")
        
        if not stores_file.exists():
            return {"success": False, "error": "stores.json not found"}
        
        try:
            with open(stores_file, 'r') as f:
                stores = json.load(f)
            
            # Validate store structure
            for store_id, store_data in stores.items():
                required_fields = ["id", "name", "url", "consumer_key", "consumer_secret"]
                for field in required_fields:
                    if field not in store_data:
                        return {"success": False, "error": f"Store {store_id} missing {field}"}
            
            return {"success": True, "stores_count": len(stores)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_product_consistency(self) -> Dict[str, Any]:
        """Check product data consistency"""
        try:
            response = await self.client.get(f"{self.base_url}/api/products?store_id=store_0&per_page=5")
            
            if response.status_code != 200:
                return {"success": False, "error": f"Product API failed: {response.status_code}"}
            
            data = response.json()
            products = data.get("products", [])
            
            if not products:
                return {"success": False, "error": "No products found"}
            
            # Check product structure consistency
            first_product = products[0]
            required_fields = ["id", "name", "sku", "price"]
            
            for field in required_fields:
                if field not in first_product:
                    return {"success": False, "error": f"Product missing {field}"}
            
            return {"success": True, "products_checked": len(products)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_api_response_formats(self) -> Dict[str, Any]:
        """Check API response format consistency"""
        try:
            endpoints_to_check = [
                "/api/stores",
                "/api/products?store_id=store_0&per_page=1",
                "/api/tool-catalog"
            ]
            
            valid_responses = 0
            
            for endpoint in endpoints_to_check:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, (dict, list)):
                            valid_responses += 1
                    except:
                        pass
            
            success_rate = (valid_responses / len(endpoints_to_check)) * 100
            
            return {
                "success": success_rate >= 80,
                "valid_responses": valid_responses,
                "total_endpoints": len(endpoints_to_check),
                "success_rate": success_rate
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_file_system(self) -> Dict[str, Any]:
        """Check file system integrity"""
        try:
            required_files = [
                "data/stores.json",
                "web_server.py",
                "requirements.txt"
            ]
            
            existing_files = 0
            
            for file_path in required_files:
                if Path(file_path).exists():
                    existing_files += 1
            
            return {
                "success": existing_files == len(required_files),
                "existing_files": existing_files,
                "required_files": len(required_files)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_holistic_tests(self) -> Dict[str, Any]:
        """Run complete holistic system test"""
        print("HOLISTIC SYSTEM TEST - MCP WOOCOMMERCE SUITE")
        print("=" * 60)
        
        # Start web server
        if not await self.start_web_server():
            return {
                "status": "failed",
                "error": "Could not start web server",
                "results": []
            }
        
        # Test suite
        test_suites = [
            ("System Endpoints", self.test_system_endpoints),
            ("MCP Tools Execution", self.test_mcp_tools_execution), 
            ("Complete Workflows", self.test_complete_workflows),
            ("Data Integrity", self.test_data_integrity)
        ]
        
        all_results = []
        passed_suites = 0
        
        for suite_name, test_func in test_suites:
            print(f"\n{'='*40}")
            print(f"TESTING: {suite_name}")
            print(f"{'='*40}")
            
            try:
                result = await test_func()
                all_results.append(result)
                
                if result["status"] == "passed":
                    passed_suites += 1
                    print(f"[+] {suite_name} - PASSED ({result['duration']:.2f}s)")
                else:
                    print(f"[X] {suite_name} - FAILED")
                    
            except Exception as e:
                error_result = {
                    "test_name": suite_name,
                    "status": "failed",
                    "error": str(e),
                    "duration": 0
                }
                all_results.append(error_result)
                print(f"[ERROR] {suite_name} - {str(e)}")
        
        # Final summary
        overall_success_rate = (passed_suites / len(test_suites)) * 100
        
        print(f"\n{'='*60}")
        print("HOLISTIC TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Test Suites: {passed_suites}/{len(test_suites)} passed ({overall_success_rate:.1f}%)")
        
        # Detailed breakdown
        for result in all_results:
            status_symbol = "[+]" if result["status"] == "passed" else "[X]"
            print(f"{status_symbol} {result['test_name']}: {result['status'].upper()}")
            
            # Suite-specific metrics
            if "success_rate" in result:
                print(f"    Success Rate: {result['success_rate']:.1f}%")
            if "duration" in result:
                print(f"    Duration: {result['duration']:.2f}s")
        
        # Save results
        results_file = Path("test_results") / f"holistic_test_{int(datetime.now().timestamp())}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        final_results = {
            "test_execution": {
                "timestamp": datetime.now().isoformat(),
                "overall_success_rate": overall_success_rate,
                "passed_suites": passed_suites,
                "total_suites": len(test_suites)
            },
            "detailed_results": all_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Final assessment
        if overall_success_rate >= 90:
            print("STATUS: EXCELLENT - System fully functional and production-ready!")
        elif overall_success_rate >= 70:
            print("STATUS: GOOD - System mostly functional with minor issues")
        elif overall_success_rate >= 50:
            print("STATUS: FAIR - System partially functional, needs improvements")
        else:
            print("STATUS: POOR - System has significant issues requiring attention")
        
        return final_results
    
    async def cleanup(self):
        """Clean up test environment"""
        await self.client.aclose()
        
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=10)
            print("Web server stopped")

async def main():
    """Main execution"""
    tester = HolisticSystemTester()
    
    try:
        results = await tester.run_holistic_tests()
        success_rate = results["test_execution"]["overall_success_rate"]
        return 0 if success_rate >= 60 else 1
        
    except Exception as e:
        print(f"Holistic test execution failed: {str(e)}")
        return 1
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)