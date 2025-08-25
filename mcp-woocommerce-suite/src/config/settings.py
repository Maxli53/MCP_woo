"""
MCP WooCommerce Suite Configuration
Production-ready settings with security and monitoring
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field, SecretStr, validator
from cryptography.fernet import Fernet
import json

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backups"
STORES_DIR = DATA_DIR / "stores"
TEMP_DIR = DATA_DIR / "temp"

# Create directories if they don't exist
for dir_path in [DATA_DIR, LOGS_DIR, BACKUP_DIR, STORES_DIR, TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: SecretStr = Field(default=None, env="MCP_SECRET_KEY")
    encryption_key: Optional[str] = Field(default=None, env="MCP_ENCRYPTION_KEY")
    jwt_secret: SecretStr = Field(default=None, env="MCP_JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    api_key_header: str = "X-API-Key"
    enable_cors: bool = True
    cors_origins: List[str] = ["http://localhost:*", "https://*.loca.lt"]
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    enable_2fa: bool = False
    
    @validator('secret_key', pre=True, always=True)
    def generate_secret_key(cls, v):
        if not v:
            return Fernet.generate_key().decode()
        return v
    
    @validator('encryption_key', pre=True, always=True)
    def generate_encryption_key(cls, v):
        if not v:
            return Fernet.generate_key().decode()
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


class LocalTunnelSettings(BaseSettings):
    """LocalTunnel configuration"""
    enabled: bool = Field(default=True, env="TUNNEL_ENABLED")
    subdomain: str = Field(default="mcp-woocommerce", env="TUNNEL_SUBDOMAIN")
    port_mapping: Dict[str, int] = {
        "mcp_server": 8083,
        "inspector": 8001,
        "dashboard": 8002,
        "gui_backend": 8000
    }
    auto_start: bool = True
    retry_attempts: int = 5
    retry_delay: int = 5
    health_check_interval: int = 30
    fallback_to_ngrok: bool = True
    ngrok_auth_token: Optional[str] = Field(default=None, env="NGROK_AUTH_TOKEN")
    custom_domain: Optional[str] = Field(default=None, env="TUNNEL_CUSTOM_DOMAIN")
    
    class Config:
        env_file = ".env"


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    db_type: str = Field(default="sqlite", env="DB_TYPE")  # sqlite, postgresql, mysql
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="mcp_woocommerce", env="DB_NAME")
    db_user: str = Field(default="", env="DB_USER")
    db_password: SecretStr = Field(default="", env="DB_PASSWORD")
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_timeout: int = 30
    sqlite_path: str = str(DATA_DIR / "mcp_woocommerce.db")
    enable_migrations: bool = True
    
    @property
    def database_url(self) -> str:
        if self.db_type == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        elif self.db_type == "postgresql":
            return f"postgresql+asyncpg://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_type == "mysql":
            return f"mysql+aiomysql://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    class Config:
        env_file = ".env"


class MonitoringSettings(BaseSettings):
    """Monitoring and logging configuration"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "json"  # json, plain
    log_rotation: str = "100 MB"
    log_retention: str = "30 days"
    enable_sentry: bool = Field(default=False, env="ENABLE_SENTRY")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_tracing: bool = False
    tracing_endpoint: Optional[str] = None
    health_check_path: str = "/health"
    readiness_check_path: str = "/ready"
    enable_performance_monitoring: bool = True
    slow_query_threshold_ms: int = 1000
    enable_audit_log: bool = True
    audit_log_path: str = str(LOGS_DIR / "audit.log")
    
    class Config:
        env_file = ".env"


class WooCommerceSettings(BaseSettings):
    """WooCommerce API configuration"""
    api_timeout: int = 30
    api_retry_count: int = 3
    api_retry_delay: int = 2
    batch_size: int = 100
    concurrent_requests: int = 5
    rate_limit_per_minute: int = 60
    cache_ttl_seconds: int = 300
    enable_webhook_verification: bool = True
    webhook_secret: Optional[SecretStr] = Field(default=None, env="WEBHOOK_SECRET")
    supported_versions: List[str] = ["wc/v3", "wc/v2", "wc/v1"]
    default_api_version: str = "wc/v3"
    
    class Config:
        env_file = ".env"


class BackupSettings(BaseSettings):
    """Backup configuration"""
    enable_auto_backup: bool = True
    backup_interval_hours: int = 24
    max_backups: int = 30
    backup_on_major_operations: bool = True
    compress_backups: bool = True
    encrypt_backups: bool = True
    cloud_backup_enabled: bool = False
    cloud_provider: Optional[str] = None  # aws, gcp, azure, dropbox
    cloud_bucket: Optional[str] = None
    cloud_credentials: Optional[Dict] = None
    
    class Config:
        env_file = ".env"


class TaskQueueSettings(BaseSettings):
    """Task queue configuration"""
    broker_type: str = "redis"  # redis, rabbitmq, memory
    broker_url: str = Field(default="redis://localhost:6379/0", env="BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/1", env="RESULT_BACKEND")
    task_time_limit: int = 3600  # 1 hour
    task_soft_time_limit: int = 3300
    worker_concurrency: int = 4
    worker_prefetch_multiplier: int = 4
    enable_task_events: bool = True
    task_track_started: bool = True
    task_reject_on_worker_lost: bool = True
    enable_scheduled_tasks: bool = True
    
    class Config:
        env_file = ".env"


class GUISettings(BaseSettings):
    """GUI application settings"""
    theme: str = "dark"  # dark, light, auto
    window_width: int = 1400
    window_height: int = 900
    start_minimized: bool = False
    minimize_to_tray: bool = True
    show_notifications: bool = True
    auto_start_on_boot: bool = False
    check_updates: bool = True
    update_channel: str = "stable"  # stable, beta, dev
    language: str = "en"
    font_size: int = 10
    enable_animations: bool = True
    
    class Config:
        env_file = ".env"


class DataValidationSettings(BaseSettings):
    """Data validation and processing settings"""
    max_csv_size_mb: int = 100
    max_excel_size_mb: int = 50
    allowed_file_extensions: List[str] = [".csv", ".xlsx", ".xls", ".json", ".xml"]
    enable_virus_scan: bool = True
    enable_data_sanitization: bool = True
    detect_encoding: bool = True
    default_encoding: str = "utf-8"
    encoding_fallbacks: List[str] = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    validate_images: bool = True
    max_image_size_mb: int = 10
    allowed_image_formats: List[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    enable_duplicate_detection: bool = True
    duplicate_threshold: float = 0.95
    
    class Config:
        env_file = ".env"


class NotificationSettings(BaseSettings):
    """Notification settings"""
    enable_email_notifications: bool = False
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[SecretStr] = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = True
    notification_email: Optional[str] = Field(default=None, env="NOTIFICATION_EMAIL")
    enable_desktop_notifications: bool = True
    enable_sound_alerts: bool = True
    enable_slack_notifications: bool = False
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    class Config:
        env_file = ".env"


class Settings:
    """Main settings aggregator"""
    def __init__(self):
        self.security = SecuritySettings()
        self.tunnel = LocalTunnelSettings()
        self.database = DatabaseSettings()
        self.monitoring = MonitoringSettings()
        self.woocommerce = WooCommerceSettings()
        self.backup = BackupSettings()
        self.task_queue = TaskQueueSettings()
        self.gui = GUISettings()
        self.validation = DataValidationSettings()
        self.notifications = NotificationSettings()
        
        # Application metadata
        self.app_name = "MCP WooCommerce Suite"
        self.app_version = "1.0.0"
        self.app_description = "Professional WooCommerce Store Management via MCP"
        self.author = "MCP WooCommerce Team"
        
        # Paths
        self.base_dir = BASE_DIR
        self.data_dir = DATA_DIR
        self.logs_dir = LOGS_DIR
        self.backup_dir = BACKUP_DIR
        self.stores_dir = STORES_DIR
        self.temp_dir = TEMP_DIR
        
        # Runtime settings
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.testing = os.getenv("TESTING", "False").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "production")
    
    def to_dict(self) -> dict:
        """Export settings as dictionary"""
        return {
            "app": {
                "name": self.app_name,
                "version": self.app_version,
                "environment": self.environment,
                "debug": self.debug
            },
            "security": self.security.dict(exclude={"secret_key", "encryption_key", "jwt_secret"}),
            "tunnel": self.tunnel.dict(),
            "database": self.database.dict(exclude={"db_password"}),
            "monitoring": self.monitoring.dict(),
            "woocommerce": self.woocommerce.dict(exclude={"webhook_secret"}),
            "backup": self.backup.dict(),
            "task_queue": self.task_queue.dict(),
            "gui": self.gui.dict(),
            "validation": self.validation.dict(),
            "notifications": self.notifications.dict(exclude={"smtp_password"})
        }
    
    def save_to_file(self, filepath: str = None):
        """Save settings to JSON file"""
        if not filepath:
            filepath = self.data_dir / "settings.json"
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def load_from_file(self, filepath: str = None):
        """Load settings from JSON file"""
        if not filepath:
            filepath = self.data_dir / "settings.json"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Update settings from loaded data
                # Implementation depends on specific needs


# Global settings instance
settings = Settings()

# Export commonly used settings
SECRET_KEY = settings.security.secret_key
DATABASE_URL = settings.database.database_url
DEBUG = settings.debug
ENVIRONMENT = settings.environment