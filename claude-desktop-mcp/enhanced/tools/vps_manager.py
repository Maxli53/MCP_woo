"""
Real VPS Management with SSH connections via Paramiko
"""

import os
import json
import logging
import paramiko
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VPSManager:
    """Manages real SSH connections to VPS servers"""
    
    def __init__(self):
        self.ssh_client = None
        self.sftp_client = None
        
    def connect(self, ip_address: str = None, port: int = None, 
                ssh_key_path: str = None, ssh_password: str = None, 
                username: str = "root") -> bool:
        """Establish SSH connection to VPS"""
        try:
            # Log what we're receiving
            logger.info(f"Connect called with: ip={ip_address}, port={port}, key={ssh_key_path}, password={'***' if ssh_password else None}")
            
            # Use environment defaults if not provided
            ip_address = ip_address or os.getenv('DEFAULT_VPS_IP')
            port = port or int(os.getenv('VPS_SSH_PORT', '22'))
            ssh_key_path = ssh_key_path or os.getenv('VPS_SSH_KEY_PATH')
            ssh_password = ssh_password or os.getenv('VPS_SSH_PASSWORD')
            
            # Log what we're using after defaults
            logger.info(f"Using after defaults: ip={ip_address}, port={port}, key={ssh_key_path}")
            logger.info(f"Key exists: {os.path.exists(ssh_key_path) if ssh_key_path else False}")
            
            if not ip_address:
                raise ValueError("VPS IP address is required")
            
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with key or password
            if ssh_key_path and os.path.exists(ssh_key_path):
                key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
                self.ssh_client.connect(
                    hostname=ip_address,
                    port=port,
                    username=username,
                    pkey=key,
                    timeout=30
                )
            elif ssh_password:
                self.ssh_client.connect(
                    hostname=ip_address,
                    port=port,
                    username=username,
                    password=ssh_password,
                    timeout=30
                )
            else:
                raise ValueError("SSH key or password required for authentication")
            
            # Create SFTP client for file operations
            self.sftp_client = self.ssh_client.open_sftp()
            
            logger.info(f"Successfully connected to VPS {ip_address}:{port}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect to VPS: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Connection details - IP: {ip_address}, Port: {port}, Key Path: {ssh_key_path}, Key Exists: {os.path.exists(ssh_key_path) if ssh_key_path else False}")
            return False
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute command on VPS and return output"""
        try:
            if not self.ssh_client:
                return {"error": "Not connected to VPS"}
            
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=60)
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                "success": exit_code == 0,
                "output": output,
                "error": error,
                "exit_code": exit_code
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def disconnect(self):
        """Close SSH connection"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()


def provision_ubuntu_vps(ip_address: str = None, ssh_key_path: str = None,
                         ssh_password: str = None, ubuntu_version: str = "22.04",
                         hostname: str = None, php_version: str = "8.1") -> Dict[str, Any]:
    """Provision Ubuntu VPS with LEMP stack - REAL implementation"""
    
    vps = VPSManager()
    
    try:
        # Connect to VPS
        ip_address = ip_address or os.getenv('DEFAULT_VPS_IP')
        if not vps.connect(ip_address=ip_address, ssh_key_path=ssh_key_path, 
                          ssh_password=ssh_password):
            return {"error": "Failed to connect to VPS"}
        
        results = []
        
        # Update system
        results.append(("System update", vps.execute_command("apt-get update")))
        
        # Install LEMP stack
        commands = [
            ("Install Nginx", "apt-get install -y nginx"),
            ("Install MySQL", f"apt-get install -y mysql-server"),
            ("Install PHP", f"apt-get install -y php{php_version}-fpm php{php_version}-mysql php{php_version}-curl php{php_version}-xml php{php_version}-gd php{php_version}-mbstring"),
            ("Install WordPress CLI", "curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x wp-cli.phar && mv wp-cli.phar /usr/local/bin/wp"),
            ("Install Certbot", "apt-get install -y certbot python3-certbot-nginx"),
            ("Install fail2ban", "apt-get install -y fail2ban"),
            ("Configure firewall", "ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable")
        ]
        
        for description, command in commands:
            results.append((description, vps.execute_command(command)))
        
        # Set hostname if provided
        if hostname:
            vps.execute_command(f"hostnamectl set-hostname {hostname}")
        
        vps.disconnect()
        
        return {
            "success": True,
            "ip_address": ip_address,
            "ubuntu_version": ubuntu_version,
            "php_version": php_version,
            "provisioning_steps": results,
            "message": "VPS provisioned successfully with LEMP stack"
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}


def get_vps_resources(vps_ip: str = None, ssh_key_path: str = None) -> Dict[str, Any]:
    """Get REAL VPS resource usage"""
    
    vps = VPSManager()
    
    try:
        vps_ip = vps_ip or os.getenv('DEFAULT_VPS_IP')
        logger.info(f"get_vps_resources called with: vps_ip={vps_ip}, ssh_key_path={ssh_key_path}")
        
        if not vps.connect(ip_address=vps_ip, ssh_key_path=ssh_key_path):
            error_details = {
                "error": "Failed to connect to VPS",
                "vps_ip": vps_ip,
                "ssh_key_path": ssh_key_path,
                "env_ip": os.getenv('DEFAULT_VPS_IP'),
                "env_port": os.getenv('VPS_SSH_PORT'),
                "env_key": os.getenv('VPS_SSH_KEY_PATH'),
                "key_exists": os.path.exists(ssh_key_path) if ssh_key_path else os.path.exists(os.getenv('VPS_SSH_KEY_PATH', ''))
            }
            return error_details
        
        # Get hostname
        hostname = vps.execute_command("hostname")
        
        # Get system info
        system_info = vps.execute_command("cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"'")
        uptime_info = vps.execute_command("uptime")
        
        # Get CPU info - updated to work with the actual top output format
        cpu_usage_raw = vps.execute_command("top -bn1 | grep '%Cpu(s)'")
        cpu_usage_str = "0"
        if cpu_usage_raw.get('output'):
            # Parse '%Cpu(s):  0.0 us,  3.0 sy,  0.0 ni, 93.9 id' format
            parts = cpu_usage_raw['output'].split(',')
            if len(parts) >= 4:
                idle = float(parts[3].split()[0])  # Get idle percentage
                cpu_usage_str = str(100 - idle)  # Calculate usage
        
        cpu_cores = vps.execute_command("nproc")
        cpu_model = vps.execute_command("cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2")
        
        # Get memory info
        mem_info = vps.execute_command("free -m | grep Mem")
        mem_parts = mem_info['output'].split() if mem_info.get('output') else []
        
        # Get disk info
        disk_info = vps.execute_command("df -h / | tail -1")
        disk_parts = disk_info['output'].split() if disk_info.get('output') else []
        
        # Get network info
        net_info = vps.execute_command("ip -s link show | grep -A1 'eth0\\|ens'")
        
        vps.disconnect()
        
        return {
            "success": True,
            "vps_ip": vps_ip,
            "hostname": hostname['output'].strip() if hostname.get('output') else "Unknown",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "os": system_info['output'].strip() if system_info.get('output') else "Unknown",
                "uptime": uptime_info['output'].strip() if uptime_info.get('output') else "Unknown"
            },
            "cpu": {
                "usage_percent": float(cpu_usage_str),
                "cores": int(cpu_cores['output'].strip()) if cpu_cores.get('output') else 0,
                "model": cpu_model['output'].strip() if cpu_model.get('output') else "Unknown"
            },
            "memory": {
                "total_mb": int(mem_parts[1]) if len(mem_parts) > 1 else 0,
                "used_mb": int(mem_parts[2]) if len(mem_parts) > 2 else 0,
                "free_mb": int(mem_parts[3]) if len(mem_parts) > 3 else 0,
                "usage_percent": (int(mem_parts[2]) / int(mem_parts[1]) * 100) if len(mem_parts) > 2 and int(mem_parts[1]) > 0 else 0
            },
            "disk": {
                "filesystem": disk_parts[0] if disk_parts else "Unknown",
                "total_size": disk_parts[1] if len(disk_parts) > 1 else "Unknown",
                "used_size": disk_parts[2] if len(disk_parts) > 2 else "Unknown",
                "available_size": disk_parts[3] if len(disk_parts) > 3 else "Unknown",
                "usage_percent": disk_parts[4] if len(disk_parts) > 4 else "Unknown",
                # Parse to GB values for compatibility
                "total_gb": float(disk_parts[1].rstrip('G')) if len(disk_parts) > 1 and 'G' in disk_parts[1] else 0,
                "used_gb": float(disk_parts[2].rstrip('G')) if len(disk_parts) > 2 and 'G' in disk_parts[2] else 0
            }
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}


def list_stores_on_vps(vps_ip: str = None, ssh_key_path: str = None) -> Dict[str, Any]:
    """List REAL WooCommerce stores on VPS"""
    
    vps = VPSManager()
    
    try:
        vps_ip = vps_ip or os.getenv('DEFAULT_VPS_IP')
        logger.info(f"list_stores_on_vps called with: vps_ip={vps_ip}, ssh_key_path={ssh_key_path}")
        
        if not vps.connect(ip_address=vps_ip, ssh_key_path=ssh_key_path):
            return {
                "error": "Failed to connect to VPS",
                "debug_info": {
                    "vps_ip": vps_ip,
                    "ssh_key_path": ssh_key_path,
                    "env_key": os.getenv('VPS_SSH_KEY_PATH'),
                    "key_exists": os.path.exists(ssh_key_path) if ssh_key_path else os.path.exists(os.getenv('VPS_SSH_KEY_PATH', ''))
                }
            }
        
        # Find all WordPress installations
        wp_sites = vps.execute_command("find /var/www -name 'wp-config.php' -type f 2>/dev/null")
        
        stores = []
        if wp_sites.get('output'):
            for wp_config in wp_sites['output'].strip().split('\n'):
                if wp_config:
                    # Get site directory
                    site_dir = os.path.dirname(wp_config)
                    
                    # Get domain from nginx config
                    nginx_result = vps.execute_command(f"grep -l '{site_dir}' /etc/nginx/sites-enabled/* | head -1")
                    domain = "unknown"
                    if nginx_result.get('output'):
                        nginx_file = nginx_result['output'].strip()
                        domain_result = vps.execute_command(f"grep server_name {nginx_file} | head -1 | awk '{{print $2}}' | tr -d ';'")
                        if domain_result.get('output'):
                            domain = domain_result['output'].strip()
                    
                    # Check if WooCommerce is installed
                    woo_check = vps.execute_command(f"cd {site_dir} && wp plugin is-installed woocommerce --allow-root 2>/dev/null && echo 'yes' || echo 'no'")
                    has_woocommerce = woo_check.get('output', '').strip() == 'yes'
                    
                    # Get site info
                    site_title = vps.execute_command(f"cd {site_dir} && wp option get blogname --allow-root 2>/dev/null")
                    
                    # Get disk usage
                    disk_usage = vps.execute_command(f"du -sh {site_dir} | awk '{{print $1}}'")
                    
                    stores.append({
                        "domain": domain,
                        "path": site_dir,
                        "name": site_title['output'].strip() if site_title.get('output') else "Unknown",
                        "has_woocommerce": has_woocommerce,
                        "disk_usage": disk_usage['output'].strip() if disk_usage.get('output') else "Unknown"
                    })
        
        vps.disconnect()
        
        return {
            "success": True,
            "vps_ip": vps_ip,
            "total_stores": len(stores),
            "stores": stores
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}


def deploy_store_to_vps(vps_ip: str = None, domain: str = None, store_name: str = None,
                        admin_email: str = None, admin_user: str = "admin",
                        admin_password: str = None, ssl_enabled: bool = True,
                        php_version: str = "8.1", ssh_key_path: str = None) -> Dict[str, Any]:
    """Deploy REAL WooCommerce store to VPS"""
    
    vps = VPSManager()
    
    try:
        vps_ip = vps_ip or os.getenv('DEFAULT_VPS_IP')
        if not vps.connect(ip_address=vps_ip, ssh_key_path=ssh_key_path):
            return {"error": "Failed to connect to VPS"}
        
        if not all([domain, store_name, admin_email]):
            return {"error": "Domain, store name and admin email are required"}
        
        # Generate password if not provided
        if not admin_password:
            admin_password = f"wp_{domain.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}"
        
        site_path = f"/var/www/{domain}"
        
        # Create directory
        vps.execute_command(f"mkdir -p {site_path}")
        
        # Download WordPress
        vps.execute_command(f"cd {site_path} && wp core download --allow-root")
        
        # Create wp-config
        db_name = domain.replace('.', '_').replace('-', '_')
        db_password = f"db_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        vps.execute_command(f"""
            mysql -e "CREATE DATABASE IF NOT EXISTS {db_name};"
            mysql -e "CREATE USER IF NOT EXISTS '{db_name}'@'localhost' IDENTIFIED BY '{db_password}';"
            mysql -e "GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_name}'@'localhost';"
            mysql -e "FLUSH PRIVILEGES;"
        """)
        
        vps.execute_command(f"cd {site_path} && wp config create --dbname={db_name} --dbuser={db_name} --dbpass={db_password} --allow-root")
        
        # Install WordPress
        vps.execute_command(f"cd {site_path} && wp core install --url={domain} --title='{store_name}' --admin_user={admin_user} --admin_password={admin_password} --admin_email={admin_email} --allow-root")
        
        # Install and activate WooCommerce
        vps.execute_command(f"cd {site_path} && wp plugin install woocommerce --activate --allow-root")
        
        # Create nginx config
        nginx_config = f"""
server {{
    listen 80;
    listen [::]:80;
    server_name {domain} www.{domain};
    root {site_path};
    index index.php index.html;
    
    location / {{
        try_files $uri $uri/ /index.php?$args;
    }}
    
    location ~ \\.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php{php_version}-fpm.sock;
    }}
    
    location ~ /\\.ht {{
        deny all;
    }}
}}
        """
        
        vps.execute_command(f"echo '{nginx_config}' > /etc/nginx/sites-available/{domain}")
        vps.execute_command(f"ln -sf /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")
        vps.execute_command("nginx -s reload")
        
        # Setup SSL if enabled
        if ssl_enabled:
            vps.execute_command(f"certbot --nginx -d {domain} -d www.{domain} --non-interactive --agree-tos --email {admin_email}")
        
        # Set proper permissions
        vps.execute_command(f"chown -R www-data:www-data {site_path}")
        vps.execute_command(f"chmod -R 755 {site_path}")
        
        vps.disconnect()
        
        return {
            "success": True,
            "vps_ip": vps_ip,
            "domain": domain,
            "store_name": store_name,
            "admin_url": f"https://{domain}/wp-admin" if ssl_enabled else f"http://{domain}/wp-admin",
            "admin_user": admin_user,
            "admin_password": admin_password,
            "admin_email": admin_email,
            "ssl_enabled": ssl_enabled,
            "woocommerce_api_url": f"https://{domain}/wp-json/wc/v3/" if ssl_enabled else f"http://{domain}/wp-json/wc/v3/",
            "message": f"WooCommerce store '{store_name}' deployed successfully to {domain}"
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}


def monitor_store_on_vps(vps_ip: str = None, domain: str = None, ssh_key_path: str = None) -> Dict[str, Any]:
    """Monitor REAL store on VPS"""
    
    vps = VPSManager()
    
    try:
        vps_ip = vps_ip or os.getenv('DEFAULT_VPS_IP')
        if not vps.connect(ip_address=vps_ip, ssh_key_path=ssh_key_path):
            return {"error": "Failed to connect to VPS"}
        
        if not domain:
            return {"error": "Domain is required"}
        
        site_path = f"/var/www/{domain}"
        
        # Check if site exists
        site_exists = vps.execute_command(f"test -d {site_path} && echo 'yes' || echo 'no'")
        if site_exists.get('output', '').strip() != 'yes':
            return {"error": f"Site {domain} not found on VPS"}
        
        # Check site status with curl
        response_time = vps.execute_command(f"curl -o /dev/null -s -w '%{{time_total}}' http://{domain}")
        
        # Check SSL certificate
        ssl_check = vps.execute_command(f"echo | openssl s_client -servername {domain} -connect {domain}:443 2>/dev/null | openssl x509 -noout -dates")
        
        # Get PHP processes
        php_processes = vps.execute_command(f"ps aux | grep php{os.getenv('PHP_VERSION', '8.1')}-fpm | grep -v grep | wc -l")
        
        # Get MySQL connections
        mysql_connections = vps.execute_command("mysqladmin processlist | wc -l")
        
        # Get disk usage
        disk_usage = vps.execute_command(f"du -sh {site_path}")
        db_size = vps.execute_command(f"cd {site_path} && wp db size --allow-root 2>/dev/null")
        
        # Get recent access logs
        access_count = vps.execute_command(f"grep {domain} /var/log/nginx/access.log | wc -l")
        
        # Get WooCommerce orders (if WooCommerce installed)
        recent_orders = vps.execute_command(f"cd {site_path} && wp wc shop_order list --fields=id --format=count --allow-root 2>/dev/null")
        
        vps.disconnect()
        
        return {
            "success": True,
            "vps_ip": vps_ip,
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "site_exists": True,
            "response_time_seconds": float(response_time['output']) if response_time.get('output') else 0,
            "ssl_info": ssl_check['output'] if ssl_check.get('output') else "No SSL",
            "php_processes": int(php_processes['output']) if php_processes.get('output') else 0,
            "mysql_connections": int(mysql_connections['output']) if mysql_connections.get('output') else 0,
            "disk_usage": disk_usage['output'].strip() if disk_usage.get('output') else "Unknown",
            "database_size": db_size['output'].strip() if db_size.get('output') else "Unknown",
            "total_access_logs": int(access_count['output']) if access_count.get('output') else 0,
            "woocommerce_orders": int(recent_orders['output']) if recent_orders.get('output') else 0
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}


def backup_vps_store(vps_ip: str = None, domain: str = None, include_database: bool = True,
                     ssh_key_path: str = None) -> Dict[str, Any]:
    """Create REAL backup of WooCommerce store"""
    
    vps = VPSManager()
    
    try:
        vps_ip = vps_ip or os.getenv('DEFAULT_VPS_IP')
        if not vps.connect(ip_address=vps_ip, ssh_key_path=ssh_key_path):
            return {"error": "Failed to connect to VPS"}
        
        if not domain:
            return {"error": "Domain is required"}
        
        site_path = f"/var/www/{domain}"
        backup_dir = "/var/backups/wordpress"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{domain}_backup_{timestamp}.tar.gz"
        
        # Create backup directory
        vps.execute_command(f"mkdir -p {backup_dir}")
        
        # Export database if needed
        if include_database:
            db_backup = f"{backup_dir}/{domain}_db_{timestamp}.sql"
            vps.execute_command(f"cd {site_path} && wp db export {db_backup} --allow-root")
        
        # Create tar backup
        if include_database:
            vps.execute_command(f"tar -czf {backup_dir}/{backup_filename} -C /var/www {domain} -C {backup_dir} {domain}_db_{timestamp}.sql")
            vps.execute_command(f"rm {backup_dir}/{domain}_db_{timestamp}.sql")
        else:
            vps.execute_command(f"tar -czf {backup_dir}/{backup_filename} -C /var/www {domain}")
        
        # Get backup size
        backup_size = vps.execute_command(f"du -h {backup_dir}/{backup_filename} | awk '{{print $1}}'")
        
        vps.disconnect()
        
        return {
            "success": True,
            "vps_ip": vps_ip,
            "domain": domain,
            "backup_file": f"{backup_dir}/{backup_filename}",
            "backup_size": backup_size['output'].strip() if backup_size.get('output') else "Unknown",
            "database_included": include_database,
            "timestamp": datetime.now().isoformat(),
            "message": f"Backup created successfully for {domain}"
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}


def execute_vps_command(vps_ip: str = None, command: str = None, ssh_key_path: str = None) -> Dict[str, Any]:
    """Execute REAL command on VPS"""
    
    vps = VPSManager()
    
    try:
        vps_ip = vps_ip or os.getenv('DEFAULT_VPS_IP')
        logger.info(f"execute_vps_command called with: vps_ip={vps_ip}, command={command}, ssh_key_path={ssh_key_path}")
        
        if not command:
            return {"error": "Command is required"}
        
        # Security check
        dangerous_commands = ['rm -rf /', 'format', 'mkfs', 'dd if=/dev/zero', 'shutdown', 'reboot']
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            return {"error": "Command rejected for security reasons"}
        
        if not vps.connect(ip_address=vps_ip, ssh_key_path=ssh_key_path):
            return {
                "error": "Failed to connect to VPS", 
                "debug_info": {
                    "vps_ip": vps_ip,
                    "ssh_key_path": ssh_key_path,
                    "env_key": os.getenv('VPS_SSH_KEY_PATH'),
                    "key_exists": os.path.exists(ssh_key_path) if ssh_key_path else os.path.exists(os.getenv('VPS_SSH_KEY_PATH', ''))
                }
            }
        
        result = vps.execute_command(command)
        vps.disconnect()
        
        return {
            "success": result.get('exit_code') == 0,
            "vps_ip": vps_ip,
            "command": command,
            "output": result.get('output', ''),
            "error": result.get('error', ''),
            "exit_code": result.get('exit_code', -1),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}


def optimize_vps_performance(vps_ip: str = None, ssh_key_path: str = None) -> Dict[str, Any]:
    """Optimize REAL VPS performance"""
    
    vps = VPSManager()
    
    try:
        vps_ip = vps_ip or os.getenv('DEFAULT_VPS_IP')
        if not vps.connect(ip_address=vps_ip, ssh_key_path=ssh_key_path):
            return {"error": "Failed to connect to VPS"}
        
        optimizations = []
        
        # MySQL optimizations
        mysql_opt = vps.execute_command("""
            mysql -e "SET GLOBAL query_cache_size = 268435456;"
            mysql -e "SET GLOBAL query_cache_type = 1;"
            mysql -e "SET GLOBAL max_connections = 200;"
        """)
        optimizations.append(("MySQL query cache and connections", mysql_opt.get('exit_code') == 0))
        
        # PHP OPcache
        php_opt = vps.execute_command("""
            echo 'opcache.enable=1' >> /etc/php/8.1/fpm/conf.d/10-opcache.ini
            echo 'opcache.memory_consumption=256' >> /etc/php/8.1/fpm/conf.d/10-opcache.ini
            systemctl restart php8.1-fpm
        """)
        optimizations.append(("PHP OPcache configuration", php_opt.get('exit_code') == 0))
        
        # Nginx optimizations
        nginx_opt = vps.execute_command("""
            sed -i 's/# gzip_/gzip_/g' /etc/nginx/nginx.conf
            nginx -s reload
        """)
        optimizations.append(("Nginx gzip compression", nginx_opt.get('exit_code') == 0))
        
        # Clean temp files
        clean_opt = vps.execute_command("""
            apt-get clean
            journalctl --vacuum-time=3d
            find /tmp -type f -atime +7 -delete
        """)
        optimizations.append(("Clean temporary files", clean_opt.get('exit_code') == 0))
        
        # Optimize all MySQL databases
        db_opt = vps.execute_command("mysqlcheck -o --all-databases")
        optimizations.append(("Optimize MySQL databases", db_opt.get('exit_code') == 0))
        
        vps.disconnect()
        
        return {
            "success": True,
            "vps_ip": vps_ip,
            "optimizations_applied": [opt[0] for opt in optimizations if opt[1]],
            "optimizations_failed": [opt[0] for opt in optimizations if not opt[1]],
            "timestamp": datetime.now().isoformat(),
            "message": "VPS optimization completed"
        }
        
    except Exception as e:
        vps.disconnect()
        return {"error": str(e)}