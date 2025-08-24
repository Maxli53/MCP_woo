#!/usr/bin/env python3
"""
MCP Admin Suite Launcher
Unified launcher for all components:
1. MCP Inspector
2. Monitoring Dashboard  
3. Content Showcase MCP Server
"""

import asyncio
import logging
import multiprocessing
import os
import signal
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

def _run_component(config):
    """Run component in separate process - standalone function for multiprocessing"""
    try:
        if config.get("is_mcp_server"):
            # For MCP servers, run directly
            module_path = config["module"]
            module = __import__(module_path.replace("/", "."), fromlist=[""])
            
            # Run SSE mode
            asyncio.run(module.run_sse("0.0.0.0", config["port"]))
        else:
            # For web apps, use uvicorn
            uvicorn.run(
                f"{config['module']}:{config['app']}",
                host="0.0.0.0",
                port=config["port"],
                log_level="info",
                access_log=False
            )
    except Exception as e:
        logging.error(f"Failed to start {config['name']}: {e}")

class MCPLauncher:
    """Main launcher class for all MCP components"""
    
    def __init__(self):
        self.processes: List[multiprocessing.Process] = []
        self.components = {
            "inspector": {
                "name": "MCP Inspector",
                "description": "Web interface for testing MCP servers",
                "module": "web.mcp_inspector.app",
                "app": "app",
                "port": 8001,
                "enabled": True
            },
            "dashboard": {
                "name": "Monitoring Dashboard", 
                "description": "Server monitoring and analytics",
                "module": "web.monitoring_dashboard.app",
                "app": "app",
                "port": 8002,
                "enabled": True
            },
            "content_showcase": {
                "name": "Content Showcase Server",
                "description": "MCP server for WordPress content management",
                "module": "servers.content_showcase_server",
                "port": 8083,
                "enabled": True,
                "is_mcp_server": True
            }
        }
        
    def display_banner(self):
        """Display startup banner"""
        is_production = os.getenv('ENVIRONMENT') == 'production'
        domain = os.getenv('EXTERNAL_HOST', 'localhost')
        
        if is_production:
            banner = Text(f"MCP Admin Suite - {domain}", style="bold green")
            subtitle = Text("Production Server - conventum.kg", style="italic cyan")
            mode_text = "[PRODUCTION] Deployed on conventum.kg server"
        else:
            banner = Text("MCP Admin Suite", style="bold blue") 
            subtitle = Text("Development Mode", style="italic yellow")
            mode_text = "[DEVELOPMENT] Running locally"
        
        panel_content = f"""
{banner}
{subtitle}

{mode_text}

[INSPECTOR] MCP Inspector - Test and debug MCP server tools
[MONITOR] Monitoring Dashboard - Server health and analytics  
[STORE] Store Admin Tools - E-commerce management AI assistant

[WARNING] ADMIN USE ONLY - Secure your endpoints appropriately
"""
        
        console.print(Panel(panel_content, border_style="blue", padding=(1, 2)))
        
    def display_configuration(self):
        """Display current configuration"""
        table = Table(title="Component Configuration")
        table.add_column("Component", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Port", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("URL", style="blue")
        
        for key, config in self.components.items():
            status = "[SUCCESS] Enabled" if config["enabled"] else "[DISABLED] Disabled"
            url = f"http://localhost:{config['port']}"
            if key == "content_showcase":
                url += " (MCP Server)"
                
            table.add_row(
                config["name"],
                config["description"],
                str(config["port"]),
                status,
                url
            )
        
        console.print(table)
        
    def check_environment(self):
        """Check if environment is properly configured"""
        console.print("[bold yellow]Checking environment...[/bold yellow]")
        
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append("Python 3.8+ required")
            
        # Check required modules
        required_modules = [
            "fastapi", "uvicorn", "mcp", "sqlalchemy", 
            "mysql", "redis", "psutil", "jinja2"
        ]
        
        for module in required_modules:
            try:
                __import__(module.replace("-", "_"))
                console.print(f"[SUCCESS] {module}")
            except ImportError:
                issues.append(f"Missing module: {module}")
                console.print(f"[FAILED] {module}")
        
        # Check environment variables
        env_vars = {
            "STORE_DB_URL": "Database connection for store admin",
            "ADMIN_API_KEY": "API key for admin operations"
        }
        
        for var, desc in env_vars.items():
            if os.getenv(var):
                console.print(f"[SUCCESS] {var}")
            else:
                console.print(f"[WARNING] {var} (optional): {desc}")
        
        if issues:
            console.print("[bold red]Issues found:[/bold red]")
            for issue in issues:
                console.print(f"  • {issue}")
            return False
        
        console.print("[bold green]Environment check passed![/bold green]")
        return True
        
    def start_component(self, component_key: str):
        """Start a single component"""
        config = self.components[component_key]
        
        if not config["enabled"]:
            return None
        
        process = multiprocessing.Process(
            target=_run_component,
            args=(config,),
            name=f"mcp-{component_key}"
        )
        
        process.start()
        self.processes.append(process)
        
        console.print(f"[SUCCESS] Started {config['name']} on port {config['port']}")
        return process
        
    def start_all_components(self):
        """Start all enabled components"""
        console.print("[bold green]Starting all components...[/bold green]")
        
        for component_key in self.components.keys():
            self.start_component(component_key)
            time.sleep(1)  # Brief delay between starts
        
        console.print("[bold green]All components started![/bold green]")
        
    def stop_all_components(self):
        """Stop all running components"""
        console.print("[bold yellow]Stopping all components...[/bold yellow]")
        
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                    
        self.processes.clear()
        console.print("[bold green]All components stopped![/bold green]")
        
    def display_status(self):
        """Display status of all components"""
        table = Table(title="Component Status")
        table.add_column("Component", style="cyan")
        table.add_column("Port", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("PID", style="white")
        
        for i, (key, config) in enumerate(self.components.items()):
            if not config["enabled"]:
                continue
                
            if i < len(self.processes):
                process = self.processes[i]
                status = "[RUNNING] Running" if process.is_alive() else "[STOPPED] Stopped"
                pid = str(process.pid) if process.is_alive() else "N/A"
            else:
                status = "[NOT STARTED] Not Started"
                pid = "N/A"
                
            table.add_row(
                config["name"],
                str(config["port"]),
                status,
                pid
            )
        
        console.print(table)
        
    def run_interactive_mode(self):
        """Run in interactive mode"""
        console.print("[bold cyan]Interactive Mode - Available Commands:[/bold cyan]")
        console.print("  [bold]start[/bold] - Start all components")
        console.print("  [bold]stop[/bold] - Stop all components") 
        console.print("  [bold]status[/bold] - Show component status")
        console.print("  [bold]restart[/bold] - Restart all components")
        console.print("  [bold]quit[/bold] - Exit launcher")
        console.print("")
        
        while True:
            try:
                command = input("MCP Admin> ").strip().lower()
                
                if command == "start":
                    self.start_all_components()
                elif command == "stop":
                    self.stop_all_components()
                elif command == "status":
                    self.display_status()
                elif command == "restart":
                    self.stop_all_components()
                    time.sleep(2)
                    self.start_all_components()
                elif command in ["quit", "exit", "q"]:
                    self.stop_all_components()
                    break
                else:
                    console.print("[red]Unknown command. Available: start, stop, status, restart, quit[/red]")
                    
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Caught Ctrl+C, shutting down...[/bold yellow]")
                self.stop_all_components()
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            console.print("\n[bold yellow]Received shutdown signal...[/bold yellow]")
            self.stop_all_components()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def run(self, args):
        """Main run method"""
        self.display_banner()
        
        if not self.check_environment():
            console.print("[bold red]Environment check failed. Please fix issues and try again.[/bold red]")
            sys.exit(1)
            
        self.display_configuration()
        
        if args.interactive:
            self.run_interactive_mode()
        else:
            self.setup_signal_handlers()
            self.start_all_components()
            
            console.print("\n[bold green]All components running! Press Ctrl+C to stop.[/bold green]")
            console.print("[bold cyan]Access points:[/bold cyan]")
            for key, config in self.components.items():
                if config["enabled"]:
                    url = f"http://localhost:{config['port']}"
                    console.print(f"  - {config['name']}: {url}")
            
            try:
                # Keep main process alive
                while True:
                    time.sleep(1)
                    # Check if any process died
                    for process in self.processes:
                        if not process.is_alive():
                            console.print(f"[red]Process {process.name} died unexpectedly![/red]")
                            
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Shutting down...[/bold yellow]")
                self.stop_all_components()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Admin Suite Launcher")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--component", "-c",
        help="Start only specific component (inspector, dashboard, store_admin)"
    )
    parser.add_argument(
        "--check-env",
        action="store_true", 
        help="Only check environment and exit"
    )
    
    args = parser.parse_args()
    
    launcher = MCPLauncher()
    
    if args.check_env:
        launcher.check_environment()
        return
        
    if args.component:
        if args.component not in launcher.components:
            console.print(f"[red]Unknown component: {args.component}[/red]")
            console.print(f"Available: {', '.join(launcher.components.keys())}")
            sys.exit(1)
        
        # Start only specific component
        launcher.setup_signal_handlers()
        launcher.start_component(args.component)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop_all_components()
    else:
        launcher.run(args)

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)  # For Windows compatibility
    main()