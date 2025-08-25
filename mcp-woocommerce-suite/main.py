"""
MCP WooCommerce Suite - Main Entry Point
Professional WooCommerce Store Management System
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings
from src.gui.main_window import main as gui_main
from src.mcp_server.woocommerce_mcp import main as mcp_main


def setup_logging():
    """Setup application logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if settings.monitoring.log_format == 'json':
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(log_format)
    else:
        formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # File handler
    log_file = settings.logs_dir / 'mcp_woocommerce.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=100*1024*1024,  # 100MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.monitoring.log_level),
        handlers=[console_handler, file_handler]
    )


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='MCP WooCommerce Suite - Professional Store Management'
    )
    
    parser.add_argument(
        '--mode',
        choices=['gui', 'server', 'inspector', 'dashboard'],
        default='gui',
        help='Application mode to run'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no GUI)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Override debug setting if specified
    if args.debug:
        settings.debug = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting MCP WooCommerce Suite v{settings.app_version}")
    logger.info(f"Mode: {args.mode}")
    
    try:
        if args.mode == 'gui' and not args.headless:
            # Run GUI application
            logger.info("Launching GUI application...")
            gui_main()
        elif args.mode == 'server':
            # Run MCP server only
            logger.info("Starting MCP server...")
            import asyncio
            from src.mcp_server.woocommerce_mcp import WooCommerceMCPServer
            server = WooCommerceMCPServer()
            asyncio.run(server.run())
        elif args.mode == 'inspector':
            # Run Inspector web interface
            logger.info("Starting MCP Inspector...")
            from src.web.inspector.app import run_inspector
            run_inspector()
        elif args.mode == 'dashboard':
            # Run Monitoring Dashboard
            logger.info("Starting Monitoring Dashboard...")
            from src.web.dashboard.app import run_dashboard
            run_dashboard()
        else:
            # Headless mode - run all services
            logger.info("Running in headless mode...")
            from src.utils.process_manager import ProcessManager
            pm = ProcessManager()
            pm.start_all_services()
            
            # Keep running
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down services...")
                pm.stop_all_services()
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()