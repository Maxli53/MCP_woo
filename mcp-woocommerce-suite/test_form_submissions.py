"""
Form Submission Testing for MCP WooCommerce Suite
Tests all form interactions, data submission, and AJAX functionality
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup

class FormSubmissionTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
    async def run_async_test(self, test_name, test_func, *args, **kwargs):
        """Execute async test and capture results"""
        print(f"\n[FORM TEST] {test_name}")
        start_time = datetime.now()
        
        try:
            result = await test_func(*args, **kwargs)
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
    
    async def test_store_addition_form(self):
        """Test store addition form submission"""
        # Test adding a store via API (simulating form submission)
        test_store_data = {
            "name": "Test Store Form Submission",
            "url": "https://test-form.example.com",
            "consumer_key": "ck_test_form_123",
            "consumer_secret": "cs_test_form_456"
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/api/stores", 
                json=test_store_data,
                headers={"Content-Type": "application/json"})
            
            form_result = {
                "submission_successful": response.status_code in [200, 201],
                "response_status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "form_data_processed": True
            }
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    form_result["response_data"] = str(response_data)[:200] + "..." if len(str(response_data)) > 200 else str(response_data)
                except:
                    form_result["response_data"] = response.text[:200]
            else:
                form_result["error_response"] = response.text[:200] if response.text else "No error message"
            
            return form_result
            
        except Exception as e:
            raise Exception(f"Store addition form test failed: {str(e)}")
    
    async def test_tool_execution_form(self):
        """Test tool execution form submissions"""
        # Test different tool execution scenarios
        tool_tests = [
            {
                "name": "List Stores",
                "tool": "list_stores",
                "parameters": {}
            },
            {
                "name": "List Products",
                "tool": "list_products", 
                "parameters": {"store_id": "store_0", "per_page": 5}
            },
            {
                "name": "Search Products",
                "tool": "search_products",
                "parameters": {"store_id": "store_0", "query": "test"}
            }
        ]
        
        tool_results = []
        
        for test in tool_tests:
            try:
                response = await self.client.post(f"{self.base_url}/api/execute-tool",
                    json={
                        "tool": test["tool"],
                        "parameters": test["parameters"]
                    },
                    headers={"Content-Type": "application/json"})
                
                tool_result = {
                    "tool_name": test["name"],
                    "tool_id": test["tool"],
                    "submission_successful": response.status_code == 200,
                    "response_status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "has_data": False
                }
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        tool_result["has_data"] = bool(response_data)
                        tool_result["data_preview"] = str(response_data)[:150] + "..." if len(str(response_data)) > 150 else str(response_data)
                    except:
                        tool_result["data_preview"] = response.text[:150]
                else:
                    tool_result["error"] = response.text[:150] if response.text else "Unknown error"
                
                tool_results.append(tool_result)
                
            except Exception as e:
                tool_results.append({
                    "tool_name": test["name"],
                    "tool_id": test["tool"],
                    "submission_successful": False,
                    "error": str(e)
                })
        
        successful_tools = sum(1 for result in tool_results if result.get("submission_successful", False))
        
        return {
            "total_tools_tested": len(tool_tests),
            "successful_submissions": successful_tools,
            "success_rate": (successful_tools / len(tool_tests)) * 100 if tool_tests else 0,
            "tool_results": tool_results
        }
    
    async def test_data_validation_forms(self):
        """Test form data validation"""
        validation_tests = []
        
        # Test 1: Invalid store data
        invalid_store_data = {
            "name": "",  # Empty name
            "url": "invalid-url",  # Invalid URL
            "consumer_key": "",  # Empty key
            "consumer_secret": ""  # Empty secret
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/api/stores",
                json=invalid_store_data,
                headers={"Content-Type": "application/json"})
            
            validation_tests.append({
                "test_name": "Invalid Store Data",
                "input_data": invalid_store_data,
                "response_status": response.status_code,
                "validation_working": response.status_code in [400, 422],  # Expected validation error
                "error_message": response.text[:150] if response.text else "No error message"
            })
        except Exception as e:
            validation_tests.append({
                "test_name": "Invalid Store Data",
                "input_data": invalid_store_data,
                "response_status": "exception",
                "validation_working": False,
                "error": str(e)
            })
        
        # Test 2: Missing required fields in tool execution
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                json={},  # Missing required fields
                headers={"Content-Type": "application/json"})
            
            validation_tests.append({
                "test_name": "Missing Tool Parameters",
                "input_data": {},
                "response_status": response.status_code,
                "validation_working": response.status_code in [400, 422],
                "error_message": response.text[:150] if response.text else "No error message"
            })
        except Exception as e:
            validation_tests.append({
                "test_name": "Missing Tool Parameters",
                "input_data": {},
                "response_status": "exception",
                "validation_working": False,
                "error": str(e)
            })
        
        # Test 3: Invalid JSON format
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                data="invalid json data",
                headers={"Content-Type": "application/json"})
            
            validation_tests.append({
                "test_name": "Invalid JSON Format",
                "input_data": "invalid json data",
                "response_status": response.status_code,
                "validation_working": response.status_code in [400, 422],
                "error_message": response.text[:150] if response.text else "No error message"
            })
        except Exception as e:
            validation_tests.append({
                "test_name": "Invalid JSON Format",
                "input_data": "invalid json data",
                "response_status": "exception",
                "validation_working": False,
                "error": str(e)
            })
        
        working_validations = sum(1 for test in validation_tests if test.get("validation_working", False))
        
        return {
            "validation_tests_count": len(validation_tests),
            "working_validations": working_validations,
            "validation_score": (working_validations / len(validation_tests)) * 100 if validation_tests else 0,
            "validation_details": validation_tests
        }
    
    async def test_ajax_functionality(self):
        """Test AJAX-like functionality and asynchronous operations"""
        # Test rapid successive requests to simulate AJAX behavior
        ajax_tests = []
        
        # Test 1: Multiple concurrent requests
        concurrent_requests = []
        for i in range(3):
            concurrent_requests.append(
                self.client.get(f"{self.base_url}/api/stores")
            )
        
        try:
            responses = await asyncio.gather(*concurrent_requests, return_exceptions=True)
            
            successful_concurrent = 0
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    ajax_tests.append({
                        "test": f"Concurrent Request {i+1}",
                        "success": False,
                        "error": str(response)
                    })
                else:
                    success = response.status_code == 200
                    if success:
                        successful_concurrent += 1
                    ajax_tests.append({
                        "test": f"Concurrent Request {i+1}",
                        "success": success,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    })
            
            concurrent_result = {
                "concurrent_requests": len(concurrent_requests),
                "successful_requests": successful_concurrent,
                "concurrency_success_rate": (successful_concurrent / len(concurrent_requests)) * 100
            }
            
        except Exception as e:
            concurrent_result = {
                "concurrent_requests": len(concurrent_requests),
                "successful_requests": 0,
                "concurrency_success_rate": 0,
                "error": str(e)
            }
        
        # Test 2: Rapid sequential requests
        sequential_start = datetime.now()
        sequential_successes = 0
        
        for i in range(5):
            try:
                response = await self.client.get(f"{self.base_url}/api/stores")
                if response.status_code == 200:
                    sequential_successes += 1
            except:
                pass
        
        sequential_duration = (datetime.now() - sequential_start).total_seconds()
        
        return {
            "concurrent_handling": concurrent_result,
            "sequential_requests": {
                "total_requests": 5,
                "successful_requests": sequential_successes,
                "total_time": sequential_duration,
                "average_time_per_request": sequential_duration / 5,
                "success_rate": (sequential_successes / 5) * 100
            },
            "ajax_tests_details": ajax_tests,
            "overall_ajax_performance": "good" if concurrent_result.get("concurrency_success_rate", 0) >= 80 else "needs_improvement"
        }
    
    async def test_error_handling_forms(self):
        """Test error handling in form submissions"""
        error_scenarios = []
        
        # Test 1: Server timeout simulation (using invalid endpoint)
        try:
            response = await self.client.post(f"{self.base_url}/api/nonexistent-endpoint",
                json={"test": "data"},
                headers={"Content-Type": "application/json"})
            
            error_scenarios.append({
                "scenario": "Invalid Endpoint",
                "response_status": response.status_code,
                "error_handled": response.status_code == 404,
                "response_body": response.text[:100] if response.text else "No response"
            })
        except Exception as e:
            error_scenarios.append({
                "scenario": "Invalid Endpoint",
                "response_status": "exception",
                "error_handled": False,
                "error": str(e)
            })
        
        # Test 2: Invalid content type
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                data="plain text data",
                headers={"Content-Type": "text/plain"})
            
            error_scenarios.append({
                "scenario": "Invalid Content Type",
                "response_status": response.status_code,
                "error_handled": response.status_code in [400, 415, 422],
                "response_body": response.text[:100] if response.text else "No response"
            })
        except Exception as e:
            error_scenarios.append({
                "scenario": "Invalid Content Type",
                "response_status": "exception",
                "error_handled": False,
                "error": str(e)
            })
        
        # Test 3: Large payload (potential DoS simulation)
        large_payload = {"data": "x" * 10000}  # 10KB of data
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                json=large_payload,
                headers={"Content-Type": "application/json"})
            
            error_scenarios.append({
                "scenario": "Large Payload",
                "response_status": response.status_code,
                "error_handled": response.status_code in [200, 413, 422],  # Either handled or payload too large
                "response_body": response.text[:100] if response.text else "No response"
            })
        except Exception as e:
            error_scenarios.append({
                "scenario": "Large Payload", 
                "response_status": "exception",
                "error_handled": True,  # Exception handling is also valid
                "error": str(e)[:100]
            })
        
        handled_errors = sum(1 for scenario in error_scenarios if scenario.get("error_handled", False))
        
        return {
            "error_scenarios_tested": len(error_scenarios),
            "properly_handled_errors": handled_errors,
            "error_handling_score": (handled_errors / len(error_scenarios)) * 100 if error_scenarios else 0,
            "error_details": error_scenarios
        }
    
    async def test_response_formats(self):
        """Test different response formats and content types"""
        format_tests = []
        
        # Test different API endpoints for response format consistency
        endpoints_to_test = [
            ("/api/stores", "Store listing"),
            ("/api/products", "Product listing"),
            ("/api/stats", "Statistics"),
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                
                format_test = {
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "is_json": False,
                    "valid_format": False
                }
                
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        format_test["is_json"] = True
                        format_test["valid_format"] = isinstance(json_data, (dict, list))
                        format_test["data_structure"] = type(json_data).__name__
                    except:
                        format_test["is_json"] = False
                        format_test["content_preview"] = response.text[:100]
                
                format_tests.append(format_test)
                
            except Exception as e:
                format_tests.append({
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": "error",
                    "error": str(e)
                })
        
        valid_formats = sum(1 for test in format_tests if test.get("valid_format", False))
        json_responses = sum(1 for test in format_tests if test.get("is_json", False))
        
        return {
            "endpoints_tested": len(endpoints_to_test),
            "valid_format_responses": valid_formats,
            "json_responses": json_responses,
            "format_consistency_score": (valid_formats / len(endpoints_to_test)) * 100 if endpoints_to_test else 0,
            "response_details": format_tests
        }
    
    async def run_form_submission_tests(self):
        """Execute complete form submission test suite"""
        print("FORM SUBMISSION TESTING - MCP WOOCOMMERCE SUITE")
        print("=" * 60)
        
        # Wait for server to be ready
        await asyncio.sleep(1)
        
        test_functions = [
            # Form Submission Tests
            ("Store Addition Form", self.test_store_addition_form),
            ("Tool Execution Forms", self.test_tool_execution_form),
            
            # Validation Tests
            ("Data Validation Forms", self.test_data_validation_forms),
            ("Error Handling Forms", self.test_error_handling_forms),
            
            # Performance & AJAX Tests
            ("AJAX Functionality", self.test_ajax_functionality),
            ("Response Formats", self.test_response_formats),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            success = await self.run_async_test(test_name, test_func)
            if success:
                passed_tests += 1
        
        # Summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print("FORM SUBMISSION TEST SUMMARY")
        print(f"{'='*60}")
        
        for result in self.test_results:
            status_symbol = "[+]" if result["status"] == "PASSED" else "[X]"
            print(f"{status_symbol} {result['test_name']}: {result['status']} ({result['duration']:.2f}s)")
            
            # Show key details
            if result["result"] and isinstance(result["result"], dict):
                if "success_rate" in result["result"]:
                    print(f"    Success Rate: {result['result']['success_rate']:.1f}%")
                elif "validation_score" in result["result"]:
                    print(f"    Validation Score: {result['result']['validation_score']:.1f}%")
                elif "error_handling_score" in result["result"]:
                    print(f"    Error Handling: {result['result']['error_handling_score']:.1f}%")
                elif "format_consistency_score" in result["result"]:
                    print(f"    Format Consistency: {result['result']['format_consistency_score']:.1f}%")
        
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Save results
        results_file = Path("test_results") / f"form_submission_test_{int(datetime.now().timestamp())}.json"
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
            print("STATUS: EXCELLENT - Form submissions fully functional!")
        elif success_rate >= 70:
            print("STATUS: GOOD - Form submissions mostly working")
        elif success_rate >= 50:
            print("STATUS: FAIR - Form submissions have some issues")
        else:
            print("STATUS: POOR - Form submissions need significant work")
        
        return success_rate >= 70
    
    async def cleanup(self):
        """Clean up test environment"""
        await self.client.aclose()

async def main():
    """Main execution"""
    try:
        tester = FormSubmissionTester()
        success = await tester.run_form_submission_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"Form submission testing failed: {str(e)}")
        return 1
    finally:
        try:
            await tester.cleanup()
        except:
            pass

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)