"""
Wizard Interface Testing for MCP WooCommerce Suite
Tests all wizard functionality, step navigation, and form interactions
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import re

class WizardInterfaceTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
    async def run_async_test(self, test_name, test_func, *args, **kwargs):
        """Execute async test and capture results"""
        print(f"\n[WIZARD TEST] {test_name}")
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
    
    async def test_wizard_main_page(self):
        """Test main wizard interface page"""
        response = await self.client.get(f"{self.base_url}/")
        
        if response.status_code != 200:
            raise Exception(f"Wizard page failed to load: {response.status_code}")
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for wizard-specific elements
        wizard_indicators = {
            "title_mentions_wizard": "wizard" in soup.title.text.lower() if soup.title else False,
            "has_tool_categories": False,
            "has_step_navigation": False,
            "has_progress_indicators": False,
            "interactive_elements": 0
        }
        
        # Check for tool categories or wizard sections
        category_indicators = [
            "store management", "product management", "bulk operations",
            "import", "export", "analytics", "cross-store"
        ]
        
        page_text = html_content.lower()
        for category in category_indicators:
            if category in page_text:
                wizard_indicators["has_tool_categories"] = True
                break
        
        # Check for step navigation
        step_indicators = ["step", "next", "previous", "back", "continue", "finish"]
        for indicator in step_indicators:
            if indicator in page_text:
                wizard_indicators["has_step_navigation"] = True
                break
        
        # Check for progress indicators
        progress_indicators = ["progress", "step 1", "step 2", "%", "complete"]
        for indicator in progress_indicators:
            if indicator in page_text:
                wizard_indicators["has_progress_indicators"] = True
                break
        
        # Count interactive elements
        buttons = soup.find_all('button')
        links = soup.find_all('a')
        inputs = soup.find_all('input')
        selects = soup.find_all('select')
        
        wizard_indicators["interactive_elements"] = len(buttons) + len(links) + len(inputs) + len(selects)
        
        return {
            "page_loaded": True,
            "content_length": len(html_content),
            "title": soup.title.text if soup.title else "No title",
            "wizard_elements": wizard_indicators,
            "buttons_count": len(buttons),
            "response_time": response.elapsed.total_seconds()
        }
    
    async def test_tool_categories(self):
        """Test tool category organization in wizard"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for tool categories mentioned in the interface
        expected_categories = [
            "Store Management",
            "Product Management", 
            "Cross-Store Operations",
            "Bulk Operations",
            "Import & Export",
            "Store Deployment",
            "Data Quality & Validation",
            "Analytics & Reports"
        ]
        
        found_categories = []
        page_text = html_content
        
        for category in expected_categories:
            if category.lower() in page_text.lower():
                found_categories.append(category)
        
        # Look for category-like structures (divs, sections, etc.)
        category_elements = []
        
        # Check for divs or sections that might represent categories
        potential_category_divs = soup.find_all(['div', 'section'], class_=re.compile(r'category|tool|group', re.I))
        category_elements.extend(potential_category_divs)
        
        return {
            "expected_categories": len(expected_categories),
            "found_categories": len(found_categories),
            "categories_found": found_categories,
            "category_elements_count": len(category_elements),
            "coverage_percentage": (len(found_categories) / len(expected_categories)) * 100
        }
    
    async def test_tool_execution_interface(self):
        """Test tool execution interface"""
        # Test the tool execution endpoint
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                json={
                    "tool": "list_stores",
                    "parameters": {}
                })
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "tool_execution_works": True,
                    "response_time": response.elapsed.total_seconds(),
                    "result_has_data": bool(result),
                    "result_preview": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                }
            else:
                raise Exception(f"Tool execution failed: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Tool execution interface error: {str(e)}")
    
    async def test_wizard_navigation(self):
        """Test wizard navigation elements"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for navigation elements
        navigation_elements = {
            "buttons": [],
            "links": [],
            "navigation_indicators": []
        }
        
        # Analyze buttons for navigation purposes
        buttons = soup.find_all('button')
        for button in buttons:
            button_text = button.text.strip().lower()
            button_info = {
                "text": button.text.strip(),
                "id": button.get('id', ''),
                "class": button.get('class', []),
                "onclick": button.get('onclick', ''),
                "is_navigation": any(nav_word in button_text for nav_word in ['next', 'back', 'previous', 'continue', 'start', 'finish'])
            }
            navigation_elements["buttons"].append(button_info)
        
        # Analyze links for navigation
        links = soup.find_all('a')
        for link in links[:10]:  # First 10 links
            link_text = link.text.strip().lower()
            link_info = {
                "text": link.text.strip(),
                "href": link.get('href', ''),
                "is_navigation": any(nav_word in link_text for nav_word in ['next', 'back', 'previous', 'continue', 'start'])
            }
            navigation_elements["links"].append(link_info)
        
        # Look for progress or step indicators
        progress_patterns = [
            r'step\s+\d+',
            r'progress[:\s]*\d+%?',
            r'\d+\s*/\s*\d+',
            r'stage\s+\d+'
        ]
        
        for pattern in progress_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            navigation_elements["navigation_indicators"].extend(matches)
        
        return {
            "total_buttons": len(buttons),
            "navigation_buttons": sum(1 for b in navigation_elements["buttons"] if b["is_navigation"]),
            "total_links": len(links),
            "navigation_links": sum(1 for l in navigation_elements["links"] if l["is_navigation"]),
            "progress_indicators": len(navigation_elements["navigation_indicators"]),
            "has_navigation": len(navigation_elements["navigation_indicators"]) > 0 or 
                            sum(1 for b in navigation_elements["buttons"] if b["is_navigation"]) > 0
        }
    
    async def test_wizard_help_system(self):
        """Test wizard help and guidance system"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for help elements
        help_elements = {
            "help_buttons": [],
            "tooltips": [],
            "help_text": [],
            "documentation_links": []
        }
        
        # Find help buttons or links
        help_indicators = soup.find_all(['button', 'a'], text=re.compile(r'help|guide|info|documentation', re.I))
        help_elements["help_buttons"] = [elem.text.strip() for elem in help_indicators]
        
        # Look for tooltip attributes
        tooltip_elements = soup.find_all(attrs={"title": True}) + soup.find_all(attrs={"data-tooltip": True})
        help_elements["tooltips"] = [elem.get('title') or elem.get('data-tooltip', '') for elem in tooltip_elements]
        
        # Look for help text or descriptions
        help_text_elements = soup.find_all(['p', 'div', 'span'], class_=re.compile(r'help|description|info', re.I))
        help_elements["help_text"] = [elem.text.strip()[:100] for elem in help_text_elements if elem.text.strip()]
        
        # Look for documentation links
        doc_links = soup.find_all('a', href=re.compile(r'doc|help|guide|manual', re.I))
        help_elements["documentation_links"] = [link.get('href') for link in doc_links]
        
        return {
            "help_buttons_count": len(help_elements["help_buttons"]),
            "tooltips_count": len(help_elements["tooltips"]),
            "help_text_sections": len(help_elements["help_text"]),
            "documentation_links": len(help_elements["documentation_links"]),
            "has_help_system": any(len(v) > 0 for v in help_elements.values()),
            "help_elements_sample": {k: v[:3] for k, v in help_elements.items()}  # First 3 of each
        }
    
    async def test_wizard_data_validation(self):
        """Test wizard data validation and error handling"""
        # Test with invalid data to see how the wizard handles it
        validation_tests = []
        
        # Test 1: Invalid store data
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                json={
                    "tool": "list_stores",
                    "parameters": {"invalid_param": "test"}
                })
            
            validation_tests.append({
                "test": "invalid_parameters",
                "response_code": response.status_code,
                "handled_gracefully": response.status_code in [200, 400, 422],  # Expected error codes
                "response_preview": response.text[:200] if response.text else "No response"
            })
        except Exception as e:
            validation_tests.append({
                "test": "invalid_parameters",
                "response_code": "exception",
                "handled_gracefully": False,
                "error": str(e)
            })
        
        # Test 2: Missing required parameters
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                json={})
            
            validation_tests.append({
                "test": "missing_parameters",
                "response_code": response.status_code,
                "handled_gracefully": response.status_code in [400, 422],  # Expected error codes
                "response_preview": response.text[:200] if response.text else "No response"
            })
        except Exception as e:
            validation_tests.append({
                "test": "missing_parameters",
                "response_code": "exception", 
                "handled_gracefully": False,
                "error": str(e)
            })
        
        # Test 3: Malformed JSON
        try:
            response = await self.client.post(f"{self.base_url}/api/execute-tool",
                data="invalid json")
            
            validation_tests.append({
                "test": "malformed_json",
                "response_code": response.status_code,
                "handled_gracefully": response.status_code in [400, 422],
                "response_preview": response.text[:200] if response.text else "No response"
            })
        except Exception as e:
            validation_tests.append({
                "test": "malformed_json",
                "response_code": "exception",
                "handled_gracefully": False,
                "error": str(e)
            })
        
        graceful_handling_count = sum(1 for test in validation_tests if test["handled_gracefully"])
        
        return {
            "validation_tests_count": len(validation_tests),
            "gracefully_handled": graceful_handling_count,
            "validation_score": (graceful_handling_count / len(validation_tests)) * 100 if validation_tests else 0,
            "test_details": validation_tests
        }
    
    async def test_wizard_responsiveness(self):
        """Test wizard responsiveness and mobile compatibility"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for responsive design elements
        responsive_elements = {
            "viewport_meta": False,
            "responsive_css": False,
            "mobile_friendly_navigation": False,
            "touch_friendly_buttons": False
        }
        
        # Check viewport meta tag
        viewport = soup.find('meta', {'name': 'viewport'})
        responsive_elements["viewport_meta"] = viewport is not None
        
        # Check for responsive CSS patterns
        css_patterns = [
            r'@media.*\(max-width',
            r'@media.*\(min-width',
            r'responsive',
            r'mobile',
            r'tablet'
        ]
        
        for pattern in css_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                responsive_elements["responsive_css"] = True
                break
        
        # Check for mobile-friendly navigation
        nav_elements = soup.find_all(['nav', 'div'], class_=re.compile(r'nav|menu|mobile', re.I))
        responsive_elements["mobile_friendly_navigation"] = len(nav_elements) > 0
        
        # Check for touch-friendly buttons (adequate size/spacing)
        buttons = soup.find_all('button')
        large_buttons = 0
        for button in buttons:
            button_class = ' '.join(button.get('class', []))
            if any(size_class in button_class.lower() for size_class in ['large', 'lg', 'big', 'touch']):
                large_buttons += 1
        
        responsive_elements["touch_friendly_buttons"] = large_buttons > 0 or len(buttons) <= 5  # Few buttons likely larger
        
        return {
            "responsive_score": sum(responsive_elements.values()) / len(responsive_elements) * 100,
            "responsive_features": responsive_elements,
            "viewport_content": viewport.get('content', '') if viewport else '',
            "total_buttons": len(buttons),
            "navigation_elements": len(nav_elements)
        }
    
    async def run_wizard_interface_tests(self):
        """Execute complete wizard interface test suite"""
        print("WIZARD INTERFACE TESTING - MCP WOOCOMMERCE SUITE")
        print("=" * 60)
        
        # Wait for server to be ready
        await asyncio.sleep(1)
        
        test_functions = [
            # Core Wizard Tests
            ("Wizard Main Page", self.test_wizard_main_page),
            ("Tool Categories", self.test_tool_categories),
            ("Tool Execution Interface", self.test_tool_execution_interface),
            
            # Navigation & UX Tests
            ("Wizard Navigation", self.test_wizard_navigation),
            ("Help System", self.test_wizard_help_system),
            ("Data Validation", self.test_wizard_data_validation),
            
            # Responsive Design Tests
            ("Wizard Responsiveness", self.test_wizard_responsiveness),
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
        print("WIZARD INTERFACE TEST SUMMARY")
        print(f"{'='*60}")
        
        for result in self.test_results:
            status_symbol = "[+]" if result["status"] == "PASSED" else "[X]"
            print(f"{status_symbol} {result['test_name']}: {result['status']} ({result['duration']:.2f}s)")
            
            # Show key details
            if result["result"] and isinstance(result["result"], dict):
                if "coverage_percentage" in result["result"]:
                    print(f"    Coverage: {result['result']['coverage_percentage']:.1f}%")
                elif "validation_score" in result["result"]:
                    print(f"    Validation Score: {result['result']['validation_score']:.1f}%")
                elif "responsive_score" in result["result"]:
                    print(f"    Responsive Score: {result['result']['responsive_score']:.1f}%")
        
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Save results
        results_file = Path("test_results") / f"wizard_interface_test_{int(datetime.now().timestamp())}.json"
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
            print("STATUS: EXCELLENT - Wizard interface fully functional!")
        elif success_rate >= 70:
            print("STATUS: GOOD - Wizard interface mostly working")
        elif success_rate >= 50:
            print("STATUS: FAIR - Wizard interface has some issues")
        else:
            print("STATUS: POOR - Wizard interface needs significant work")
        
        return success_rate >= 70
    
    async def cleanup(self):
        """Clean up test environment"""
        await self.client.aclose()

async def main():
    """Main execution"""
    try:
        tester = WizardInterfaceTester()
        success = await tester.run_wizard_interface_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"Wizard interface testing failed: {str(e)}")
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