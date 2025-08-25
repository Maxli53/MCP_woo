"""
LocalTunnel Manager - Handles LocalTunnel connections and fallback to ngrok
"""

import os
import subprocess
import threading
import time
import json
import re
from typing import Dict, Optional, Any
from pathlib import Path
import logging
import requests

from ..config.settings import settings

logger = logging.getLogger(__name__)


class TunnelManager:
    """Manages LocalTunnel and ngrok connections"""
    
    def __init__(self):
        self.tunnel_process = None
        self.tunnel_urls = {}
        self.tunnel_thread = None
        self.is_running = False
        self.tunnel_type = None  # 'localtunnel' or 'ngrok'
    
    def start_tunnel(self, subdomain: str = None) -> bool:
        """Start tunnel with LocalTunnel or fallback to ngrok"""
        if self.is_running:
            logger.warning("Tunnel is already running")
            return False
        
        subdomain = subdomain or settings.tunnel.subdomain
        
        # Try LocalTunnel first
        if self._start_localtunnel(subdomain):
            self.tunnel_type = 'localtunnel'
            logger.info(f"LocalTunnel started with subdomain: {subdomain}")
            return True
        
        # Fallback to ngrok if enabled
        if settings.tunnel.fallback_to_ngrok and settings.tunnel.ngrok_auth_token:
            if self._start_ngrok(subdomain):
                self.tunnel_type = 'ngrok'
                logger.info(f"ngrok started as fallback")
                return True
        
        logger.error("Failed to start any tunnel service")
        return False
    
    def _start_localtunnel(self, subdomain: str) -> bool:
        """Start LocalTunnel service"""
        try:
            # Install localtunnel if not present
            self._ensure_localtunnel_installed()
            
            # Start tunnel for each service
            self.tunnel_urls = {}
            
            for service_name, port in settings.tunnel.port_mapping.items():
                cmd = [
                    "npx", "localtunnel",
                    "--port", str(port),
                    "--subdomain", f"{subdomain}-{service_name}"
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True
                )
                
                # Wait for URL
                time.sleep(2)
                
                # Parse output for URL
                output = process.stdout.readline()
                match = re.search(r'https://[^\s]+', output)
                if match:
                    url = match.group(0)
                    self.tunnel_urls[service_name] = url
                    logger.info(f"LocalTunnel URL for {service_name}: {url}")
            
            self.is_running = True
            self._start_health_monitor()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start LocalTunnel: {e}")
            return False
    
    def _start_ngrok(self, subdomain: str) -> bool:
        """Start ngrok as fallback"""
        try:
            # Configure ngrok auth token
            subprocess.run(
                ["ngrok", "config", "add-authtoken", settings.tunnel.ngrok_auth_token],
                check=True,
                capture_output=True
            )
            
            # Create ngrok configuration file
            config = {
                "version": "2",
                "authtoken": settings.tunnel.ngrok_auth_token,
                "tunnels": {}
            }
            
            for service_name, port in settings.tunnel.port_mapping.items():
                config["tunnels"][service_name] = {
                    "proto": "http",
                    "addr": port,
                    "subdomain": f"{subdomain}-{service_name}" if subdomain else None
                }
            
            config_file = Path.home() / ".ngrok_mcp.yml"
            with open(config_file, 'w') as f:
                import yaml
                yaml.dump(config, f)
            
            # Start ngrok with all tunnels
            self.tunnel_process = subprocess.Popen(
                ["ngrok", "start", "--all", "--config", str(config_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for ngrok to start
            time.sleep(3)
            
            # Get tunnel URLs from ngrok API
            try:
                response = requests.get("http://localhost:4040/api/tunnels")
                if response.status_code == 200:
                    tunnels = response.json()["tunnels"]
                    for tunnel in tunnels:
                        name = tunnel["name"]
                        url = tunnel["public_url"]
                        if url.startswith("https"):
                            self.tunnel_urls[name] = url
                            logger.info(f"ngrok URL for {name}: {url}")
            except:
                logger.warning("Could not fetch ngrok URLs from API")
            
            self.is_running = True
            self._start_health_monitor()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ngrok: {e}")
            return False
    
    def _ensure_localtunnel_installed(self):
        """Ensure LocalTunnel is installed via npm"""
        try:
            # Check if npm is available
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
            
            # Install localtunnel globally if not present
            result = subprocess.run(
                ["npm", "list", "-g", "localtunnel"],
                capture_output=True,
                text=True
            )
            
            if "localtunnel" not in result.stdout:
                logger.info("Installing LocalTunnel...")
                subprocess.run(
                    ["npm", "install", "-g", "localtunnel"],
                    check=True,
                    capture_output=True
                )
                logger.info("LocalTunnel installed successfully")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install LocalTunnel: {e}")
            raise
    
    def stop_tunnel(self):
        """Stop tunnel service"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.tunnel_process:
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
            self.tunnel_process = None
        
        # Kill any remaining localtunnel processes
        if self.tunnel_type == 'localtunnel':
            if os.name == 'nt':
                subprocess.run(["taskkill", "/F", "/IM", "lt.exe"], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "localtunnel"], capture_output=True)
        
        self.tunnel_urls = {}
        self.tunnel_type = None
        logger.info("Tunnel stopped")
    
    def get_tunnel_urls(self) -> Dict[str, str]:
        """Get current tunnel URLs"""
        return self.tunnel_urls.copy()
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is active"""
        return self.is_running and len(self.tunnel_urls) > 0
    
    def _start_health_monitor(self):
        """Start health monitoring thread"""
        if self.tunnel_thread and self.tunnel_thread.is_alive():
            return
        
        self.tunnel_thread = threading.Thread(target=self._monitor_tunnel_health)
        self.tunnel_thread.daemon = True
        self.tunnel_thread.start()
    
    def _monitor_tunnel_health(self):
        """Monitor tunnel health and restart if needed"""
        retry_count = 0
        max_retries = settings.tunnel.retry_attempts
        
        while self.is_running:
            time.sleep(settings.tunnel.health_check_interval)
            
            # Check if tunnel URLs are accessible
            all_healthy = True
            for service, url in self.tunnel_urls.items():
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code >= 500:
                        all_healthy = False
                        logger.warning(f"Tunnel unhealthy for {service}: {url}")
                except:
                    all_healthy = False
                    logger.warning(f"Cannot reach tunnel for {service}: {url}")
            
            if not all_healthy:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error("Tunnel health check failed. Restarting...")
                    self.restart_tunnel()
                    retry_count = 0
            else:
                retry_count = 0
    
    def restart_tunnel(self):
        """Restart tunnel service"""
        subdomain = settings.tunnel.subdomain
        self.stop_tunnel()
        time.sleep(2)
        self.start_tunnel(subdomain)
    
    def get_public_url(self, service: str) -> Optional[str]:
        """Get public URL for a specific service"""
        return self.tunnel_urls.get(service)