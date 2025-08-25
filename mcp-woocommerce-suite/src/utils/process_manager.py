"""
Process Manager - Manages MCP services and background processes
"""

import os
import sys
import subprocess
import psutil
import threading
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages MCP service processes"""
    
    def __init__(self):
        self.processes = {}
        self.service_configs = {
            'mcp_server': {
                'name': 'MCP Server',
                'script': 'src/mcp_server/woocommerce_mcp.py',
                'port': 8083,
                'python': True
            },
            'inspector': {
                'name': 'MCP Inspector',
                'script': 'src/web/inspector/app.py',
                'port': 8001,
                'python': True
            },
            'dashboard': {
                'name': 'Monitoring Dashboard',
                'script': 'src/web/dashboard/app.py',
                'port': 8002,
                'python': True
            }
        }
        self.tunnel_manager = None
    
    def start_service(self, service_id: str) -> bool:
        """Start a specific service"""
        if service_id not in self.service_configs:
            logger.error(f"Unknown service: {service_id}")
            return False
        
        if self.is_service_running(service_id):
            logger.warning(f"Service {service_id} is already running")
            return True
        
        config = self.service_configs[service_id]
        
        try:
            if config.get('python'):
                # Start Python service
                script_path = settings.base_dir / config['script']
                cmd = [sys.executable, str(script_path)]
            else:
                # Start other service
                cmd = config['command']
            
            # Set environment variables
            env = os.environ.copy()
            env['PYTHONPATH'] = str(settings.base_dir)
            env['MCP_SERVICE'] = service_id
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(settings.base_dir)
            )
            
            self.processes[service_id] = {
                'process': process,
                'pid': process.pid,
                'started': time.time(),
                'config': config
            }
            
            logger.info(f"Started {config['name']} (PID: {process.pid})")
            
            # Start log monitoring thread
            self._start_log_monitor(service_id, process)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {service_id}: {e}")
            return False
    
    def stop_service(self, service_id: str) -> bool:
        """Stop a specific service"""
        if service_id not in self.processes:
            logger.warning(f"Service {service_id} is not running")
            return True
        
        try:
            process_info = self.processes[service_id]
            process = process_info['process']
            
            # Terminate gracefully
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not terminated
                process.kill()
                process.wait()
            
            del self.processes[service_id]
            logger.info(f"Stopped {self.service_configs[service_id]['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop {service_id}: {e}")
            return False
    
    def restart_service(self, service_id: str) -> bool:
        """Restart a specific service"""
        self.stop_service(service_id)
        time.sleep(1)
        return self.start_service(service_id)
    
    def start_all_services(self) -> bool:
        """Start all configured services"""
        success = True
        for service_id in self.service_configs:
            if not self.start_service(service_id):
                success = False
        
        # Auto-start tunnel if configured
        if settings.tunnel.auto_start and settings.tunnel.enabled:
            from .tunnel_manager import TunnelManager
            if not self.tunnel_manager:
                self.tunnel_manager = TunnelManager()
            self.tunnel_manager.start_tunnel()
        
        return success
    
    def stop_all_services(self) -> bool:
        """Stop all running services"""
        success = True
        
        # Stop tunnel first
        if self.tunnel_manager:
            self.tunnel_manager.stop_tunnel()
        
        # Stop all services
        for service_id in list(self.processes.keys()):
            if not self.stop_service(service_id):
                success = False
        
        return success
    
    def is_service_running(self, service_id: str) -> bool:
        """Check if a service is running"""
        if service_id not in self.processes:
            return False
        
        process = self.processes[service_id]['process']
        return process.poll() is None
    
    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get detailed status of a service"""
        if service_id not in self.service_configs:
            return {'error': 'Unknown service'}
        
        config = self.service_configs[service_id]
        status = {
            'name': config['name'],
            'running': self.is_service_running(service_id),
            'port': config.get('port')
        }
        
        if service_id in self.processes:
            process_info = self.processes[service_id]
            status.update({
                'pid': process_info['pid'],
                'uptime': time.time() - process_info['started'],
                'memory': self._get_process_memory(process_info['pid']),
                'cpu': self._get_process_cpu(process_info['pid'])
            })
        
        return status
    
    def get_all_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        return {
            service_id: self.get_service_status(service_id)
            for service_id in self.service_configs
        }
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is active"""
        if self.tunnel_manager:
            return self.tunnel_manager.is_tunnel_active()
        return False
    
    def get_tunnel_urls(self) -> Dict[str, str]:
        """Get tunnel URLs"""
        if self.tunnel_manager:
            return self.tunnel_manager.get_tunnel_urls()
        return {}
    
    def _get_process_memory(self, pid: int) -> float:
        """Get process memory usage in MB"""
        try:
            process = psutil.Process(pid)
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0
    
    def _get_process_cpu(self, pid: int) -> float:
        """Get process CPU usage percentage"""
        try:
            process = psutil.Process(pid)
            return process.cpu_percent(interval=0.1)
        except:
            return 0
    
    def _start_log_monitor(self, service_id: str, process: subprocess.Popen):
        """Start thread to monitor service logs"""
        def monitor_output():
            for line in iter(process.stdout.readline, b''):
                if line:
                    self._log_service_output(service_id, line.decode('utf-8', errors='ignore'))
        
        thread = threading.Thread(target=monitor_output)
        thread.daemon = True
        thread.start()
    
    def _log_service_output(self, service_id: str, message: str):
        """Log service output"""
        # Save to log file
        log_dir = settings.logs_dir / service_id
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"{service_id}_{time.strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}")
    
    def check_port_availability(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except:
                return False
    
    def kill_process_on_port(self, port: int) -> bool:
        """Kill process using a specific port"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        process.kill()
                    return True
        except Exception as e:
            logger.error(f"Failed to kill process on port {port}: {e}")
        return False
    
    def enable_windows_startup(self) -> bool:
        """Enable application startup on Windows boot"""
        if os.name != 'nt':
            return False
        
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            app_path = sys.executable
            if app_path.endswith('python.exe'):
                # Running from Python, use the main script
                app_path = f'"{app_path}" "{settings.base_dir / "main.py"}"'
            else:
                # Compiled executable
                app_path = f'"{app_path}"'
            
            winreg.SetValueEx(
                key,
                "MCP WooCommerce Suite",
                0,
                winreg.REG_SZ,
                app_path
            )
            
            winreg.CloseKey(key)
            logger.info("Enabled Windows startup")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable Windows startup: {e}")
            return False
    
    def disable_windows_startup(self) -> bool:
        """Disable application startup on Windows boot"""
        if os.name != 'nt':
            return False
        
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, "MCP WooCommerce Suite")
            except FileNotFoundError:
                pass
            
            winreg.CloseKey(key)
            logger.info("Disabled Windows startup")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable Windows startup: {e}")
            return False