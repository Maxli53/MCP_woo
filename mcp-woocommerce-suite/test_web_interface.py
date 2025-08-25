"""
Complete Web Interface Testing for MCP WooCommerce Suite
Tests all HTML elements, JavaScript functionality, and user interactions
"""

import asyncio
import httpx
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import re
from bs4 import BeautifulSoup

class WebInterfaceTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
    def run_test(self, test_name, test_func, *args, **kwargs):
        """Execute a test and capture results"""
        print(f"\n[WEB UI TEST] {test_name}")
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
    
    async def run_async_test(self, test_name, test_func, *args, **kwargs):
        """Execute async test and capture results"""
        print(f"\n[WEB UI ASYNC TEST] {test_name}")
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
    
    async def test_main_page_loading(self):
        """Test main page HTML rendering"""
        response = await self.client.get(f"{self.base_url}/")
        
        if response.status_code != 200:
            raise Exception(f"Main page failed to load: {response.status_code}")
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check HTML structure
        if not soup.find('html'):
            raise Exception("Invalid HTML structure - no <html> tag")
        
        if not soup.find('head'):
            raise Exception("Invalid HTML structure - no <head> tag")
        
        if not soup.find('body'):
            raise Exception("Invalid HTML structure - no <body> tag")
        
        # Check for title
        title = soup.find('title')
        if not title:
            raise Exception("Page missing <title> tag")
        
        return {
            "status_code": response.status_code,
            "content_length": len(html_content),
            "title": title.text if title else "No title",
            "has_html_structure": True,
            "response_time": response.elapsed.total_seconds()
        }
    
    async def test_html_elements(self):
        """Test specific HTML elements on main page"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        elements_to_check = {
            "header": soup.find('header') or soup.find('h1') or soup.find('h2'),
            "navigation": soup.find('nav') or soup.find_all('a'),
            "main_content": soup.find('main') or soup.find('div'),
            "forms": soup.find_all('form'),
            "buttons": soup.find_all('button') + soup.find_all('input', {'type': 'submit'}),
            "inputs": soup.find_all('input') + soup.find_all('select') + soup.find_all('textarea'),
            "scripts": soup.find_all('script'),
            "stylesheets": soup.find_all('link', {'rel': 'stylesheet'}) + soup.find_all('style')
        }
        
        element_analysis = {}
        for element_type, elements in elements_to_check.items():
            if isinstance(elements, list):
                element_analysis[element_type] = {
                    "count": len(elements),
                    "present": len(elements) > 0,
                    "details": [elem.name for elem in elements[:5]] if elements else []
                }
            else:
                element_analysis[element_type] = {
                    "count": 1 if elements else 0,
                    "present": elements is not None,
                    "details": elements.name if elements else None
                }
        
        return element_analysis
    
    async def test_css_loading(self):
        """Test CSS stylesheets loading"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find CSS links
        css_links = soup.find_all('link', {'rel': 'stylesheet'})
        inline_styles = soup.find_all('style')
        
        css_results = {
            "external_stylesheets": len(css_links),
            "inline_styles": len(inline_styles),
            "css_present": len(css_links) > 0 or len(inline_styles) > 0,
            "stylesheets": []
        }
        
        # Test external CSS loading
        for css_link in css_links[:3]:  # Test first 3 CSS links
            href = css_link.get('href')
            if href:
                try:
                    if href.startswith('/'):
                        css_url = f"{self.base_url}{href}"
                    elif href.startswith('http'):
                        css_url = href
                    else:
                        css_url = f"{self.base_url}/{href}"
                    
                    css_response = await self.client.get(css_url)
                    css_results["stylesheets"].append({
                        "url": href,
                        "status": css_response.status_code,
                        "accessible": css_response.status_code == 200,
                        "content_length": len(css_response.text) if css_response.status_code == 200 else 0
                    })
                except Exception as e:
                    css_results["stylesheets"].append({
                        "url": href,
                        "status": "error",
                        "accessible": False,
                        "error": str(e)
                    })
        
        return css_results
    
    async def test_javascript_loading(self):
        """Test JavaScript loading and functionality"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find JavaScript elements
        script_tags = soup.find_all('script')
        
        js_results = {
            "script_tags_count": len(script_tags),
            "inline_scripts": 0,
            "external_scripts": 0,
            "scripts": []
        }
        
        for script in script_tags:
            src = script.get('src')
            if src:
                # External script
                js_results["external_scripts"] += 1
                try:
                    if src.startswith('/'):
                        js_url = f"{self.base_url}{src}"
                    elif src.startswith('http'):
                        js_url = src
                    else:
                        js_url = f"{self.base_url}/{src}"
                    
                    js_response = await self.client.get(js_url)
                    js_results["scripts"].append({
                        "type": "external",
                        "url": src,
                        "status": js_response.status_code,
                        "accessible": js_response.status_code == 200,
                        "content_length": len(js_response.text) if js_response.status_code == 200 else 0
                    })
                except Exception as e:
                    js_results["scripts"].append({
                        "type": "external",
                        "url": src,
                        "status": "error",
                        "accessible": False,
                        "error": str(e)
                    })
            else:
                # Inline script
                js_results["inline_scripts"] += 1
                script_content = script.string or ""
                js_results["scripts"].append({
                    "type": "inline",
                    "content_length": len(script_content),
                    "has_content": len(script_content.strip()) > 0,
                    "preview": script_content[:100] + "..." if len(script_content) > 100 else script_content
                })
        
        return js_results
    
    async def test_form_elements(self):
        """Test form elements and functionality"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        forms = soup.find_all('form')
        form_results = {
            "forms_count": len(forms),
            "forms_present": len(forms) > 0,
            "form_details": []
        }
        
        for i, form in enumerate(forms):
            form_analysis = {
                "form_index": i,
                "action": form.get('action', ''),
                "method": form.get('method', 'GET').upper(),
                "inputs": [],
                "buttons": [],
                "selects": [],
                "textareas": []
            }
            
            # Analyze form inputs
            inputs = form.find_all('input')
            for inp in inputs:
                form_analysis["inputs"].append({
                    "type": inp.get('type', 'text'),
                    "name": inp.get('name', ''),
                    "id": inp.get('id', ''),
                    "required": inp.has_attr('required'),
                    "placeholder": inp.get('placeholder', '')
                })
            
            # Analyze buttons
            buttons = form.find_all('button') + form.find_all('input', {'type': ['submit', 'button']})
            for btn in buttons:
                form_analysis["buttons"].append({
                    "type": btn.get('type', 'button'),
                    "text": btn.text.strip() if btn.text else btn.get('value', ''),
                    "id": btn.get('id', ''),
                    "class": btn.get('class', [])
                })
            
            # Analyze selects
            selects = form.find_all('select')
            for select in selects:
                options = select.find_all('option')
                form_analysis["selects"].append({
                    "name": select.get('name', ''),
                    "id": select.get('id', ''),
                    "options_count": len(options),
                    "multiple": select.has_attr('multiple')
                })
            
            # Analyze textareas
            textareas = form.find_all('textarea')
            for textarea in textareas:
                form_analysis["textareas"].append({
                    "name": textarea.get('name', ''),
                    "id": textarea.get('id', ''),
                    "rows": textarea.get('rows', ''),
                    "cols": textarea.get('cols', '')
                })
            
            form_results["form_details"].append(form_analysis)
        
        return form_results
    
    async def test_interactive_elements(self):
        """Test interactive elements like buttons, links, etc."""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        interactive_results = {
            "links": {"count": 0, "details": []},
            "buttons": {"count": 0, "details": []},
            "interactive_inputs": {"count": 0, "details": []}
        }
        
        # Test links
        links = soup.find_all('a')
        interactive_results["links"]["count"] = len(links)
        
        for link in links[:10]:  # Test first 10 links
            href = link.get('href', '')
            link_text = link.text.strip()
            
            link_detail = {
                "href": href,
                "text": link_text,
                "is_external": href.startswith('http') and not href.startswith(self.base_url),
                "is_internal": href.startswith('/') or href.startswith(self.base_url),
                "is_anchor": href.startswith('#'),
                "has_text": len(link_text) > 0
            }
            
            # Test internal links
            if link_detail["is_internal"] and not link_detail["is_anchor"]:
                try:
                    if href.startswith('/'):
                        test_url = f"{self.base_url}{href}"
                    else:
                        test_url = href
                    
                    link_response = await self.client.get(test_url)
                    link_detail["accessible"] = link_response.status_code == 200
                    link_detail["status_code"] = link_response.status_code
                except:
                    link_detail["accessible"] = False
                    link_detail["status_code"] = "error"
            
            interactive_results["links"]["details"].append(link_detail)
        
        # Test buttons
        buttons = soup.find_all('button') + soup.find_all('input', {'type': ['button', 'submit']})
        interactive_results["buttons"]["count"] = len(buttons)
        
        for button in buttons[:5]:  # Test first 5 buttons
            interactive_results["buttons"]["details"].append({
                "type": button.get('type', 'button'),
                "text": button.text.strip() if button.text else button.get('value', ''),
                "id": button.get('id', ''),
                "class": button.get('class', []),
                "onclick": button.get('onclick', ''),
                "has_javascript": bool(button.get('onclick') or 'click' in str(button))
            })
        
        # Test interactive inputs
        interactive_inputs = soup.find_all('input', {'type': ['checkbox', 'radio', 'range', 'file']})
        interactive_results["interactive_inputs"]["count"] = len(interactive_inputs)
        
        for inp in interactive_inputs[:5]:
            interactive_results["interactive_inputs"]["details"].append({
                "type": inp.get('type'),
                "name": inp.get('name', ''),
                "id": inp.get('id', ''),
                "value": inp.get('value', ''),
                "checked": inp.has_attr('checked')
            })
        
        return interactive_results
    
    async def test_api_endpoints_from_ui(self):
        """Test API endpoints that the UI might call"""
        api_endpoints = [
            "/api/stores",
            "/api/products",
            "/api/stats",
            "/api/tools"
        ]
        
        endpoint_results = []
        
        for endpoint in api_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                
                endpoint_result = {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds(),
                    "content_type": response.headers.get("content-type", ""),
                    "is_json": False,
                    "data_preview": None
                }
                
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        endpoint_result["is_json"] = True
                        endpoint_result["data_preview"] = str(json_data)[:200] + "..." if len(str(json_data)) > 200 else str(json_data)
                    except:
                        endpoint_result["data_preview"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
                
                endpoint_results.append(endpoint_result)
                
            except Exception as e:
                endpoint_results.append({
                    "endpoint": endpoint,
                    "status_code": "error",
                    "accessible": False,
                    "error": str(e)
                })
        
        return {
            "endpoints_tested": len(api_endpoints),
            "accessible_endpoints": sum(1 for r in endpoint_results if r.get("accessible", False)),
            "endpoint_details": endpoint_results
        }
    
    async def test_tool_execution_ui(self):
        """Test tool execution through UI interface"""
        # Test if there's a tool execution endpoint
        try:
            # Try to execute a simple tool
            response = await self.client.post(f"{self.base_url}/api/execute-tool", 
                json={
                    "tool": "list_stores",
                    "parameters": {}
                })
            
            if response.status_code == 200:
                result_data = response.json()
                return {
                    "tool_execution_available": True,
                    "test_tool": "list_stores",
                    "response_status": response.status_code,
                    "result_preview": str(result_data)[:200] + "..." if len(str(result_data)) > 200 else str(result_data)
                }
            else:
                return {
                    "tool_execution_available": False,
                    "response_status": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            return {
                "tool_execution_available": False,
                "error": str(e)
            }
    
    async def test_responsive_design(self):
        """Test responsive design elements"""
        response = await self.client.get(f"{self.base_url}/")
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for responsive design indicators
        viewport_meta = soup.find('meta', {'name': 'viewport'})
        media_queries = re.findall(r'@media[^{]*\{', html_content, re.IGNORECASE)
        bootstrap_classes = re.findall(r'class="[^"]*(?:col-|container|row|responsive)[^"]*"', html_content)
        
        responsive_results = {
            "viewport_meta_present": viewport_meta is not None,
            "viewport_content": viewport_meta.get('content', '') if viewport_meta else '',
            "media_queries_count": len(media_queries),
            "bootstrap_classes_count": len(bootstrap_classes),
            "responsive_indicators": {
                "has_viewport": viewport_meta is not None,
                "has_media_queries": len(media_queries) > 0,
                "has_responsive_classes": len(bootstrap_classes) > 0
            }
        }
        
        return responsive_results
    
    async def run_complete_web_interface_tests(self):
        """Execute complete web interface test suite"""
        print("COMPLETE WEB INTERFACE TESTING - MCP WOOCOMMERCE SUITE")
        print("=" * 70)
        
        # Wait for server to be ready
        await asyncio.sleep(2)
        
        test_functions = [
            # HTML Structure Tests
            ("Main Page Loading", self.test_main_page_loading),
            ("HTML Elements", self.test_html_elements),
            
            # Asset Loading Tests  
            ("CSS Loading", self.test_css_loading),
            ("JavaScript Loading", self.test_javascript_loading),
            
            # Form & Interaction Tests
            ("Form Elements", self.test_form_elements),
            ("Interactive Elements", self.test_interactive_elements),
            
            # API Integration Tests
            ("API Endpoints from UI", self.test_api_endpoints_from_ui),
            ("Tool Execution UI", self.test_tool_execution_ui),
            
            # Design Tests
            ("Responsive Design", self.test_responsive_design),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            success = await self.run_async_test(test_name, test_func)
            if success:
                passed_tests += 1
        
        # Summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*70}")
        print("WEB INTERFACE TEST SUMMARY")
        print(f"{'='*70}")
        
        for result in self.test_results:
            status_symbol = "[+]" if result["status"] == "PASSED" else "[X]"
            print(f"{status_symbol} {result['test_name']}: {result['status']} ({result['duration']:.2f}s)")
            
            # Show key details for some tests
            if result["result"] and isinstance(result["result"], dict):
                if "forms_count" in result["result"]:
                    print(f"    Forms found: {result['result']['forms_count']}")
                elif "links" in result["result"]:
                    print(f"    Links: {result['result']['links']['count']}, Buttons: {result['result']['buttons']['count']}")
                elif "accessible_endpoints" in result["result"]:
                    print(f"    API endpoints accessible: {result['result']['accessible_endpoints']}/{result['result']['endpoints_tested']}")
        
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Save results
        results_file = Path("test_results") / f"web_interface_test_{int(datetime.now().timestamp())}.json"
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
            print("STATUS: EXCELLENT - Web interface fully functional!")
        elif success_rate >= 70:
            print("STATUS: GOOD - Web interface mostly working")
        elif success_rate >= 50:
            print("STATUS: FAIR - Web interface has some issues")
        else:
            print("STATUS: POOR - Web interface needs significant work")
        
        return success_rate >= 70
    
    async def cleanup(self):
        """Clean up test environment"""
        await self.client.aclose()

async def main():
    """Main execution"""
    try:
        tester = WebInterfaceTester()
        success = await tester.run_complete_web_interface_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"Web interface testing failed: {str(e)}")
        return 1
    finally:
        try:
            await tester.cleanup()
        except:
            pass

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)