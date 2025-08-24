#!/usr/bin/env python3
"""
Upload Complete PHP MCP Suite to conventum.kg
Deploy all components of the MCP Admin Suite
"""

import os
import sys
from ftplib import FTP
from pathlib import Path
import time

# FTP Configuration
FTP_HOST = "conventum.kg"
FTP_USER = "user133859"  # Replace with actual FTP username
FTP_PASS = ""  # User needs to provide FTP password

def upload_file(ftp, local_path, remote_path):
    """Upload a single file to FTP server"""
    try:
        with open(local_path, 'rb') as file:
            ftp.storbinary(f'STOR {remote_path}', file)
        print(f"✓ Uploaded: {local_path} -> {remote_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to upload {local_path}: {e}")
        return False

def create_remote_directory(ftp, path):
    """Create directory on remote server if it doesn't exist"""
    try:
        ftp.mkd(path)
        print(f"✓ Created directory: {path}")
    except Exception as e:
        if "exists" not in str(e).lower():
            print(f"⚠ Directory creation note: {path} - {e}")

def main():
    """Main upload function"""
    if not FTP_PASS:
        print("Please set FTP_PASS in the script before running")
        sys.exit(1)
    
    print("🚀 Starting MCP Admin Suite Deployment")
    print("=" * 50)
    
    # Files to upload
    files_to_upload = [
        ('index.php', 'showcase/index.php'),
        ('mcp_inspector.php', 'showcase/mcp_inspector.php'),
        ('monitoring_dashboard.php', 'showcase/monitoring_dashboard.php'),
        ('content_analyzer.php', 'showcase/analyzer.php'),  # Keep existing name
        ('auto_improver.php', 'showcase/auto_improver.php'),
        ('showcase_manager.php', 'showcase/showcase_manager.php'),
        ('wp_api_setup.php', 'showcase/wp_api_setup.php')
    ]
    
    try:
        # Connect to FTP
        print("Connecting to FTP server...")
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd('/')  # Change to root directory
        
        print(f"✓ Connected to {FTP_HOST}")
        
        # Ensure showcase directory exists
        create_remote_directory(ftp, 'showcase')
        
        # Upload files
        successful_uploads = 0
        for local_file, remote_file in files_to_upload:
            local_path = Path(__file__).parent / local_file
            
            if local_path.exists():
                if upload_file(ftp, local_path, remote_file):
                    successful_uploads += 1
                time.sleep(0.5)  # Brief delay between uploads
            else:
                print(f"✗ Local file not found: {local_path}")
        
        ftp.quit()
        
        print("\n" + "=" * 50)
        print(f"📊 Deployment Summary:")
        print(f"   Successful uploads: {successful_uploads}/{len(files_to_upload)}")
        print(f"   Main URL: https://conventum.kg/showcase/")
        print(f"   MCP Inspector: https://conventum.kg/showcase/mcp_inspector.php")
        print(f"   System Dashboard: https://conventum.kg/showcase/monitoring_dashboard.php")
        print(f"   Content Analyzer: https://conventum.kg/showcase/analyzer.php")
        print(f"   Auto Improver: https://conventum.kg/showcase/auto_improver.php")
        
        if successful_uploads == len(files_to_upload):
            print("\n🎉 Complete MCP Admin Suite deployed successfully!")
        else:
            print(f"\n⚠ Partial deployment - {len(files_to_upload) - successful_uploads} files failed")
            
    except Exception as e:
        print(f"✗ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()