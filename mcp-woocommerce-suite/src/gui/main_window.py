"""
Professional GUI Application for MCP WooCommerce Suite
Modern desktop interface with system tray integration
"""

import sys
import os
import json
import asyncio
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QTextEdit, QListWidget,
    QGroupBox, QGridLayout, QSystemTrayIcon, QMenu, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QProgressBar, QStatusBar, QToolBar, QMenuBar, QDialog,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QFileDialog
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSettings, QSize, QUrl
)
from PyQt6.QtGui import (
    QIcon, QAction, QPalette, QColor, QFont, QPixmap
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

import psutil
import requests

from ..config.settings import settings
from ..utils.tunnel_manager import TunnelManager
from ..utils.process_manager import ProcessManager


class ServiceMonitorThread(QThread):
    """Thread for monitoring service status"""
    status_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.process_manager = ProcessManager()
    
    def run(self):
        while self.running:
            try:
                status = {
                    'mcp_server': self.process_manager.is_service_running('mcp_server'),
                    'inspector': self.process_manager.is_service_running('inspector'),
                    'dashboard': self.process_manager.is_service_running('dashboard'),
                    'tunnel': self.process_manager.is_tunnel_active(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent
                }
                
                # Check tunnel URLs
                if status['tunnel']:
                    status['tunnel_urls'] = self.process_manager.get_tunnel_urls()
                else:
                    status['tunnel_urls'] = {}
                
                self.status_updated.emit(status)
            except Exception as e:
                print(f"Monitor error: {e}")
            
            self.msleep(5000)  # Update every 5 seconds
    
    def stop(self):
        self.running = False


class MCPWooCommerceSuite(QMainWindow):
    """Main GUI Application Window"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('MCPWooCommerce', 'Suite')
        self.process_manager = ProcessManager()
        self.tunnel_manager = TunnelManager()
        self.monitor_thread = None
        self.tray_icon = None
        self.init_ui()
        self.setup_system_tray()
        self.start_monitoring()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MCP WooCommerce Suite - Professional Store Management")
        self.setGeometry(100, 100, settings.gui.window_width, settings.gui.window_height)
        
        # Set application style
        self.set_theme(settings.gui.theme)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status indicators
        self.create_status_panel()
        
        # Create main content area with tabs
        self.create_main_tabs()
        
        # Create status bar
        self.create_status_bar()
        
        # Add widgets to main layout
        main_layout.addWidget(self.status_panel)
        main_layout.addWidget(self.tab_widget, stretch=1)
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        import_action = QAction('Import Products', self)
        import_action.triggered.connect(self.import_products)
        file_menu.addAction(import_action)
        
        export_action = QAction('Export Products', self)
        export_action.triggered.connect(self.export_products)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Services menu
        services_menu = menubar.addMenu('&Services')
        
        start_all_action = QAction('Start All Services', self)
        start_all_action.triggered.connect(self.start_all_services)
        services_menu.addAction(start_all_action)
        
        stop_all_action = QAction('Stop All Services', self)
        stop_all_action.triggered.connect(self.stop_all_services)
        services_menu.addAction(stop_all_action)
        
        services_menu.addSeparator()
        
        restart_action = QAction('Restart Services', self)
        restart_action.triggered.connect(self.restart_services)
        services_menu.addAction(restart_action)
        
        # Stores menu
        stores_menu = menubar.addMenu('&Stores')
        
        add_store_action = QAction('Add Store', self)
        add_store_action.triggered.connect(self.show_add_store_dialog)
        stores_menu.addAction(add_store_action)
        
        manage_stores_action = QAction('Manage Stores', self)
        manage_stores_action.triggered.connect(self.show_manage_stores_dialog)
        stores_menu.addAction(manage_stores_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        backup_action = QAction('Backup Manager', self)
        backup_action.triggered.connect(self.show_backup_manager)
        tools_menu.addAction(backup_action)
        
        validator_action = QAction('Data Validator', self)
        validator_action.triggered.connect(self.show_data_validator)
        tools_menu.addAction(validator_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        docs_action = QAction('Documentation', self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Start button
        self.start_btn = QAction("▶ Start All", self)
        self.start_btn.triggered.connect(self.start_all_services)
        toolbar.addAction(self.start_btn)
        
        # Stop button
        self.stop_btn = QAction("⏹ Stop All", self)
        self.stop_btn.triggered.connect(self.stop_all_services)
        toolbar.addAction(self.stop_btn)
        
        toolbar.addSeparator()
        
        # Tunnel button
        self.tunnel_btn = QAction("🌐 Connect Tunnel", self)
        self.tunnel_btn.triggered.connect(self.toggle_tunnel)
        toolbar.addAction(self.tunnel_btn)
        
        toolbar.addSeparator()
        
        # Quick access buttons
        inspector_btn = QAction("🔍 Inspector", self)
        inspector_btn.triggered.connect(self.open_inspector)
        toolbar.addAction(inspector_btn)
        
        dashboard_btn = QAction("📊 Dashboard", self)
        dashboard_btn.triggered.connect(self.open_dashboard)
        toolbar.addAction(dashboard_btn)
        
        toolbar.addSeparator()
        
        # Refresh button
        refresh_btn = QAction("🔄 Refresh", self)
        refresh_btn.triggered.connect(self.refresh_status)
        toolbar.addAction(refresh_btn)
    
    def create_status_panel(self):
        """Create status indicators panel"""
        self.status_panel = QGroupBox("Service Status")
        layout = QHBoxLayout()
        
        # Service status indicators
        self.service_indicators = {}
        services = [
            ('MCP Server', 'mcp_server'),
            ('Inspector', 'inspector'),
            ('Dashboard', 'dashboard'),
            ('Tunnel', 'tunnel')
        ]
        
        for label, service_id in services:
            indicator_widget = QWidget()
            indicator_layout = QVBoxLayout(indicator_widget)
            
            status_label = QLabel("●")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet("font-size: 24px; color: gray;")
            
            name_label = QLabel(label)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            indicator_layout.addWidget(status_label)
            indicator_layout.addWidget(name_label)
            
            self.service_indicators[service_id] = status_label
            layout.addWidget(indicator_widget)
        
        # System metrics
        layout.addStretch()
        
        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        
        self.cpu_label = QLabel("CPU: 0%")
        self.memory_label = QLabel("Memory: 0%")
        self.disk_label = QLabel("Disk: 0%")
        
        metrics_layout.addWidget(QLabel("System:"), 0, 0)
        metrics_layout.addWidget(self.cpu_label, 0, 1)
        metrics_layout.addWidget(self.memory_label, 1, 1)
        metrics_layout.addWidget(self.disk_label, 2, 1)
        
        layout.addWidget(metrics_widget)
        
        # Tunnel URLs
        self.tunnel_info = QTextEdit()
        self.tunnel_info.setReadOnly(True)
        self.tunnel_info.setMaximumHeight(80)
        self.tunnel_info.setPlaceholderText("Tunnel URLs will appear here when connected...")
        layout.addWidget(self.tunnel_info)
        
        self.status_panel.setLayout(layout)
    
    def create_main_tabs(self):
        """Create main content tabs"""
        self.tab_widget = QTabWidget()
        
        # Dashboard tab
        self.dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Stores tab
        self.stores_tab = self.create_stores_tab()
        self.tab_widget.addTab(self.stores_tab, "Stores")
        
        # Products tab
        self.products_tab = self.create_products_tab()
        self.tab_widget.addTab(self.products_tab, "Products")
        
        # Operations tab
        self.operations_tab = self.create_operations_tab()
        self.tab_widget.addTab(self.operations_tab, "Operations")
        
        # Logs tab
        self.logs_tab = self.create_logs_tab()
        self.tab_widget.addTab(self.logs_tab, "Logs")
        
        # Settings tab
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
    
    def create_dashboard_tab(self):
        """Create dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Quick stats
        stats_group = QGroupBox("Quick Statistics")
        stats_layout = QGridLayout()
        
        self.stats_labels = {
            'total_stores': QLabel("0"),
            'total_products': QLabel("0"),
            'active_operations': QLabel("0"),
            'last_sync': QLabel("Never")
        }
        
        stats_layout.addWidget(QLabel("Total Stores:"), 0, 0)
        stats_layout.addWidget(self.stats_labels['total_stores'], 0, 1)
        stats_layout.addWidget(QLabel("Total Products:"), 0, 2)
        stats_layout.addWidget(self.stats_labels['total_products'], 0, 3)
        stats_layout.addWidget(QLabel("Active Operations:"), 1, 0)
        stats_layout.addWidget(self.stats_labels['active_operations'], 1, 1)
        stats_layout.addWidget(QLabel("Last Sync:"), 1, 2)
        stats_layout.addWidget(self.stats_labels['last_sync'], 1, 3)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.activity_list = QListWidget()
        activity_layout.addWidget(self.activity_list)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QGridLayout()
        
        sync_btn = QPushButton("Sync All Stores")
        sync_btn.clicked.connect(self.sync_all_stores)
        actions_layout.addWidget(sync_btn, 0, 0)
        
        backup_btn = QPushButton("Create Backup")
        backup_btn.clicked.connect(self.create_backup)
        actions_layout.addWidget(backup_btn, 0, 1)
        
        import_btn = QPushButton("Import Products")
        import_btn.clicked.connect(self.import_products)
        actions_layout.addWidget(import_btn, 1, 0)
        
        export_btn = QPushButton("Export Products")
        export_btn.clicked.connect(self.export_products)
        actions_layout.addWidget(export_btn, 1, 1)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        return widget
    
    def create_stores_tab(self):
        """Create stores management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Store list
        self.stores_table = QTableWidget()
        self.stores_table.setColumnCount(6)
        self.stores_table.setHorizontalHeaderLabels([
            "Store ID", "URL", "Status", "Products", "Last Sync", "Actions"
        ])
        self.stores_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.stores_table)
        
        # Store actions
        actions_layout = QHBoxLayout()
        
        add_store_btn = QPushButton("Add Store")
        add_store_btn.clicked.connect(self.show_add_store_dialog)
        actions_layout.addWidget(add_store_btn)
        
        edit_store_btn = QPushButton("Edit Store")
        edit_store_btn.clicked.connect(self.edit_selected_store)
        actions_layout.addWidget(edit_store_btn)
        
        delete_store_btn = QPushButton("Delete Store")
        delete_store_btn.clicked.connect(self.delete_selected_store)
        actions_layout.addWidget(delete_store_btn)
        
        test_connection_btn = QPushButton("Test Connection")
        test_connection_btn.clicked.connect(self.test_store_connection)
        actions_layout.addWidget(test_connection_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return widget
    
    def create_products_tab(self):
        """Create products management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Store selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select Store:"))
        
        self.store_selector = QComboBox()
        selector_layout.addWidget(self.store_selector)
        
        load_products_btn = QPushButton("Load Products")
        load_products_btn.clicked.connect(self.load_products)
        selector_layout.addWidget(load_products_btn)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "SKU", "Name", "Price", "Stock", "Status", "Categories"
        ])
        
        layout.addWidget(self.products_table)
        
        # Product actions
        actions_layout = QHBoxLayout()
        
        import_csv_btn = QPushButton("Import CSV")
        import_csv_btn.clicked.connect(self.import_csv)
        actions_layout.addWidget(import_csv_btn)
        
        export_excel_btn = QPushButton("Export Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        actions_layout.addWidget(export_excel_btn)
        
        bulk_update_btn = QPushButton("Bulk Update")
        bulk_update_btn.clicked.connect(self.bulk_update_products)
        actions_layout.addWidget(bulk_update_btn)
        
        sync_products_btn = QPushButton("Sync Products")
        sync_products_btn.clicked.connect(self.sync_products)
        actions_layout.addWidget(sync_products_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return widget
    
    def create_operations_tab(self):
        """Create operations tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Operation categories
        operations_group = QGroupBox("Available Operations")
        operations_layout = QGridLayout()
        
        # Store operations
        store_ops_group = QGroupBox("Store Operations")
        store_ops_layout = QVBoxLayout()
        
        clone_store_btn = QPushButton("Clone Store")
        clone_store_btn.clicked.connect(self.clone_store)
        store_ops_layout.addWidget(clone_store_btn)
        
        migrate_products_btn = QPushButton("Migrate Products")
        migrate_products_btn.clicked.connect(self.migrate_products)
        store_ops_layout.addWidget(migrate_products_btn)
        
        compare_stores_btn = QPushButton("Compare Stores")
        compare_stores_btn.clicked.connect(self.compare_stores)
        store_ops_layout.addWidget(compare_stores_btn)
        
        store_ops_group.setLayout(store_ops_layout)
        operations_layout.addWidget(store_ops_group, 0, 0)
        
        # Bulk operations
        bulk_ops_group = QGroupBox("Bulk Operations")
        bulk_ops_layout = QVBoxLayout()
        
        batch_price_btn = QPushButton("Batch Price Update")
        batch_price_btn.clicked.connect(self.batch_price_update)
        bulk_ops_layout.addWidget(batch_price_btn)
        
        batch_category_btn = QPushButton("Batch Category Update")
        batch_category_btn.clicked.connect(self.batch_category_update)
        bulk_ops_layout.addWidget(batch_category_btn)
        
        batch_seo_btn = QPushButton("Batch SEO Update")
        batch_seo_btn.clicked.connect(self.batch_seo_update)
        bulk_ops_layout.addWidget(batch_seo_btn)
        
        bulk_ops_group.setLayout(bulk_ops_layout)
        operations_layout.addWidget(bulk_ops_group, 0, 1)
        
        # Data validation
        validation_group = QGroupBox("Data Validation")
        validation_layout = QVBoxLayout()
        
        validate_data_btn = QPushButton("Validate Product Data")
        validate_data_btn.clicked.connect(self.validate_product_data)
        validation_layout.addWidget(validate_data_btn)
        
        find_duplicates_btn = QPushButton("Find Duplicates")
        find_duplicates_btn.clicked.connect(self.find_duplicates)
        validation_layout.addWidget(find_duplicates_btn)
        
        audit_completeness_btn = QPushButton("Audit Completeness")
        audit_completeness_btn.clicked.connect(self.audit_completeness)
        validation_layout.addWidget(audit_completeness_btn)
        
        validation_group.setLayout(validation_layout)
        operations_layout.addWidget(validation_group, 0, 2)
        
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Operation queue
        queue_group = QGroupBox("Operation Queue")
        queue_layout = QVBoxLayout()
        
        self.operation_queue = QTableWidget()
        self.operation_queue.setColumnCount(5)
        self.operation_queue.setHorizontalHeaderLabels([
            "Operation", "Status", "Progress", "Started", "Actions"
        ])
        
        queue_layout.addWidget(self.operation_queue)
        queue_group.setLayout(queue_layout)
        layout.addWidget(queue_group)
        
        return widget
    
    def create_logs_tab(self):
        """Create logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Log filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Log Level:"))
        
        self.log_level_filter = QComboBox()
        self.log_level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_filter.currentTextChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.log_level_filter)
        
        filter_layout.addWidget(QLabel("Service:"))
        
        self.service_filter = QComboBox()
        self.service_filter.addItems(["All", "MCP Server", "Inspector", "Dashboard", "Tunnel"])
        self.service_filter.currentTextChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.service_filter)
        
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        filter_layout.addWidget(clear_logs_btn)
        
        export_logs_btn = QPushButton("Export Logs")
        export_logs_btn.clicked.connect(self.export_logs)
        filter_layout.addWidget(export_logs_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_viewer)
        
        return widget
    
    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QGridLayout()
        
        general_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark", "Light", "Auto"])
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        general_layout.addWidget(self.theme_selector, 0, 1)
        
        self.start_minimized_cb = QCheckBox("Start Minimized")
        general_layout.addWidget(self.start_minimized_cb, 1, 0, 1, 2)
        
        self.minimize_to_tray_cb = QCheckBox("Minimize to System Tray")
        general_layout.addWidget(self.minimize_to_tray_cb, 2, 0, 1, 2)
        
        self.auto_start_cb = QCheckBox("Start on Windows Boot")
        general_layout.addWidget(self.auto_start_cb, 3, 0, 1, 2)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Tunnel settings
        tunnel_group = QGroupBox("LocalTunnel Settings")
        tunnel_layout = QGridLayout()
        
        tunnel_layout.addWidget(QLabel("Subdomain:"), 0, 0)
        self.tunnel_subdomain = QLineEdit(settings.tunnel.subdomain)
        tunnel_layout.addWidget(self.tunnel_subdomain, 0, 1)
        
        self.tunnel_auto_start = QCheckBox("Auto-start Tunnel")
        self.tunnel_auto_start.setChecked(settings.tunnel.auto_start)
        tunnel_layout.addWidget(self.tunnel_auto_start, 1, 0, 1, 2)
        
        self.tunnel_fallback = QCheckBox("Fallback to ngrok")
        self.tunnel_fallback.setChecked(settings.tunnel.fallback_to_ngrok)
        tunnel_layout.addWidget(self.tunnel_fallback, 2, 0, 1, 2)
        
        tunnel_group.setLayout(tunnel_layout)
        layout.addWidget(tunnel_group)
        
        # Save settings button
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_btn)
        
        layout.addStretch()
        
        return widget
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets
        self.connection_status = QLabel("● Disconnected")
        self.connection_status.setStyleSheet("color: red;")
        self.status_bar.addPermanentWidget(self.connection_status)
        
        self.status_bar.showMessage("Ready")
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("MCP WooCommerce Suite")
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        start_action = tray_menu.addAction("Start Services")
        start_action.triggered.connect(self.start_all_services)
        
        stop_action = tray_menu.addAction("Stop Services")
        stop_action.triggered.connect(self.stop_all_services)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def start_monitoring(self):
        """Start service monitoring thread"""
        self.monitor_thread = ServiceMonitorThread()
        self.monitor_thread.status_updated.connect(self.update_service_status)
        self.monitor_thread.start()
    
    def update_service_status(self, status: Dict[str, Any]):
        """Update service status indicators"""
        # Update service indicators
        for service_id, indicator in self.service_indicators.items():
            if status.get(service_id, False):
                indicator.setStyleSheet("font-size: 24px; color: green;")
            else:
                indicator.setStyleSheet("font-size: 24px; color: red;")
        
        # Update system metrics
        self.cpu_label.setText(f"CPU: {status['cpu_percent']:.1f}%")
        self.memory_label.setText(f"Memory: {status['memory_percent']:.1f}%")
        self.disk_label.setText(f"Disk: {status['disk_percent']:.1f}%")
        
        # Update tunnel URLs
        if status.get('tunnel_urls'):
            urls_text = "Tunnel URLs:\n"
            for service, url in status['tunnel_urls'].items():
                urls_text += f"{service}: {url}\n"
            self.tunnel_info.setText(urls_text)
        else:
            self.tunnel_info.clear()
        
        # Update connection status
        if status.get('tunnel'):
            self.connection_status.setText("● Connected")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("● Disconnected")
            self.connection_status.setStyleSheet("color: red;")
    
    def set_theme(self, theme: str):
        """Set application theme"""
        if theme.lower() == "dark":
            # Dark theme
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            self.setPalette(dark_palette)
    
    # Service control methods
    def start_all_services(self):
        """Start all services"""
        self.status_bar.showMessage("Starting all services...")
        self.process_manager.start_all_services()
        self.add_activity("Started all services")
    
    def stop_all_services(self):
        """Stop all services"""
        self.status_bar.showMessage("Stopping all services...")
        self.process_manager.stop_all_services()
        self.add_activity("Stopped all services")
    
    def restart_services(self):
        """Restart all services"""
        self.stop_all_services()
        QTimer.singleShot(2000, self.start_all_services)
    
    def toggle_tunnel(self):
        """Toggle LocalTunnel connection"""
        if self.process_manager.is_tunnel_active():
            self.tunnel_manager.stop_tunnel()
            self.add_activity("Disconnected LocalTunnel")
        else:
            subdomain = self.tunnel_subdomain.text() or settings.tunnel.subdomain
            self.tunnel_manager.start_tunnel(subdomain)
            self.add_activity(f"Connected LocalTunnel with subdomain: {subdomain}")
    
    # Dialog methods
    def show_add_store_dialog(self):
        """Show add store dialog"""
        # Implementation would open a dialog to add a new store
        pass
    
    def show_settings_dialog(self):
        """Show settings dialog"""
        self.tab_widget.setCurrentIndex(5)  # Switch to settings tab
    
    # Utility methods
    def add_activity(self, message: str):
        """Add activity to recent activity list"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_list.insertItem(0, f"[{timestamp}] {message}")
        if self.activity_list.count() > 100:
            self.activity_list.takeItem(100)
    
    def refresh_status(self):
        """Refresh all status information"""
        self.status_bar.showMessage("Refreshing status...")
        # Trigger immediate status update
        if self.monitor_thread:
            self.monitor_thread.run()
    
    def load_settings(self):
        """Load application settings"""
        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load other settings
        theme = self.settings.value("theme", settings.gui.theme)
        self.set_theme(theme)
    
    def save_settings(self):
        """Save application settings"""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Save other settings
        self.settings.setValue("theme", self.theme_selector.currentText())
        
        self.status_bar.showMessage("Settings saved")
    
    def closeEvent(self, event):
        """Handle close event"""
        if settings.gui.minimize_to_tray and self.tray_icon:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "MCP WooCommerce Suite",
                "Application minimized to tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.quit_application()
    
    def quit_application(self):
        """Quit the application"""
        # Stop monitoring thread
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
        
        # Save settings
        self.save_settings()
        
        # Stop all services
        self.process_manager.stop_all_services()
        
        # Quit
        QApplication.quit()
    
    # Placeholder methods for functionality
    def open_inspector(self):
        """Open MCP Inspector in browser"""
        import webbrowser
        urls = self.process_manager.get_tunnel_urls()
        if 'inspector' in urls:
            webbrowser.open(urls['inspector'])
        else:
            webbrowser.open("http://localhost:8001")
    
    def open_dashboard(self):
        """Open Monitoring Dashboard in browser"""
        import webbrowser
        urls = self.process_manager.get_tunnel_urls()
        if 'dashboard' in urls:
            webbrowser.open(urls['dashboard'])
        else:
            webbrowser.open("http://localhost:8002")
    
    def import_products(self):
        """Import products from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Products", "", 
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.status_bar.showMessage(f"Importing products from {file_path}")
            self.add_activity(f"Imported products from {file_path}")
    
    def export_products(self):
        """Export products to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Products", "", 
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if file_path:
            self.status_bar.showMessage(f"Exporting products to {file_path}")
            self.add_activity(f"Exported products to {file_path}")
    
    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About MCP WooCommerce Suite",
            f"<h2>{settings.app_name}</h2>"
            f"<p>Version: {settings.app_version}</p>"
            f"<p>{settings.app_description}</p>"
            f"<p>© 2024 {settings.author}</p>"
        )


def main():
    """Main entry point for GUI application"""
    app = QApplication(sys.argv)
    app.setApplicationName("MCP WooCommerce Suite")
    app.setOrganizationName("MCPWooCommerce")
    
    # Set application icon
    # app.setWindowIcon(QIcon("resources/icons/app_icon.png"))
    
    window = MCPWooCommerceSuite()
    
    if not settings.gui.start_minimized:
        window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()