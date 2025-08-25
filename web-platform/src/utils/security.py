"""
Security Module - Handles encryption, authentication, and secure credential storage
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import logging

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from passlib.context import CryptContext
from jose import JWTError, jwt
import pyotp

from ..config.settings import settings

logger = logging.getLogger(__name__)


class SecureCredentialStore:
    """Secure storage for API credentials and sensitive data"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        self.credentials_file = settings.data_dir / "credentials.enc"
        self.credentials_cache = {}
        self._load_credentials()
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = settings.data_dir / ".key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (Windows)
            if os.name == 'nt':
                import win32api
                import win32security
                import ntsecuritycon as con
                
                # Get current user SID
                user_sid = win32security.GetTokenInformation(
                    win32security.GetCurrentProcessToken(),
                    win32security.TokenUser
                )[0]
                
                # Create DACL with only current user having access
                dacl = win32security.ACL()
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_ALL_ACCESS,
                    user_sid
                )
                
                # Set security descriptor
                sd = win32security.SECURITY_DESCRIPTOR()
                sd.SetSecurityDescriptorDacl(1, dacl, 0)
                win32security.SetFileSecurity(
                    str(key_file),
                    win32security.DACL_SECURITY_INFORMATION,
                    sd
                )
            
            return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def _load_credentials(self):
        """Load encrypted credentials from file"""
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                self.credentials_cache = json.loads(decrypted_data)
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
                self.credentials_cache = {}
    
    def save_credential(self, key: str, value: str, metadata: Dict[str, Any] = None):
        """Save encrypted credential"""
        self.credentials_cache[key] = {
            'value': value,
            'metadata': metadata or {},
            'created': datetime.now().isoformat(),
            'last_accessed': None
        }
        self._save_credentials()
    
    def get_credential(self, key: str) -> Optional[str]:
        """Get decrypted credential"""
        if key in self.credentials_cache:
            self.credentials_cache[key]['last_accessed'] = datetime.now().isoformat()
            self._save_credentials()
            return self.credentials_cache[key]['value']
        return None
    
    def delete_credential(self, key: str) -> bool:
        """Delete credential"""
        if key in self.credentials_cache:
            del self.credentials_cache[key]
            self._save_credentials()
            return True
        return False
    
    def _save_credentials(self):
        """Save encrypted credentials to file"""
        try:
            data = json.dumps(self.credentials_cache)
            encrypted_data = self.cipher.encrypt(data.encode())
            
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")


class AuthenticationManager:
    """Manages user authentication and authorization"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
        self.secret_key = settings.security.secret_key.get_secret_value()
        self.algorithm = settings.security.jwt_algorithm
        self.token_expire_hours = settings.security.jwt_expiration_hours
        self.users_file = settings.data_dir / "users.json"
        self.sessions_file = settings.data_dir / "sessions.json"
        self.failed_attempts = {}
        self._load_users()
    
    def _load_users(self):
        """Load user data"""
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            # Create default admin user
            self.users = {
                "admin": {
                    "username": "admin",
                    "hashed_password": self.hash_password("changeme"),
                    "role": "admin",
                    "created": datetime.now().isoformat(),
                    "two_factor_enabled": False,
                    "two_factor_secret": None
                }
            }
            self._save_users()
    
    def _save_users(self):
        """Save user data"""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    async def authenticate_user(self, username: str, password: str, 
                               otp_code: str = None) -> Dict[str, Any]:
        """Authenticate user with optional 2FA"""
        # Check failed attempts
        if username in self.failed_attempts:
            attempts = self.failed_attempts[username]
            if attempts['count'] >= settings.security.max_login_attempts:
                lockout_time = datetime.fromisoformat(attempts['last_attempt']) + \
                             timedelta(minutes=settings.security.lockout_duration_minutes)
                if datetime.now() < lockout_time:
                    return {
                        'success': False,
                        'error': 'Account locked due to too many failed attempts'
                    }
                else:
                    # Reset failed attempts after lockout period
                    del self.failed_attempts[username]
        
        # Check user exists
        if username not in self.users:
            self._record_failed_attempt(username)
            return {'success': False, 'error': 'Invalid credentials'}
        
        user = self.users[username]
        
        # Verify password
        if not self.verify_password(password, user['hashed_password']):
            self._record_failed_attempt(username)
            return {'success': False, 'error': 'Invalid credentials'}
        
        # Check 2FA if enabled
        if user.get('two_factor_enabled') and settings.security.enable_2fa:
            if not otp_code:
                return {'success': False, 'error': '2FA code required', 'requires_2fa': True}
            
            if not self._verify_otp(user['two_factor_secret'], otp_code):
                self._record_failed_attempt(username)
                return {'success': False, 'error': 'Invalid 2FA code'}
        
        # Clear failed attempts on successful login
        if username in self.failed_attempts:
            del self.failed_attempts[username]
        
        # Generate token
        token = self.create_access_token({'sub': username, 'role': user['role']})
        
        # Update last login
        user['last_login'] = datetime.now().isoformat()
        self._save_users()
        
        return {
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'role': user['role']
            }
        }
    
    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 0,
                'last_attempt': datetime.now().isoformat()
            }
        
        self.failed_attempts[username]['count'] += 1
        self.failed_attempts[username]['last_attempt'] = datetime.now().isoformat()
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=self.token_expire_hours)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """Create new user"""
        if username in self.users:
            return False
        
        self.users[username] = {
            "username": username,
            "hashed_password": self.hash_password(password),
            "role": role,
            "created": datetime.now().isoformat(),
            "two_factor_enabled": False,
            "two_factor_secret": None
        }
        
        self._save_users()
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete user"""
        if username in self.users and username != "admin":
            del self.users[username]
            self._save_users()
            return True
        return False
    
    def change_password(self, username: str, old_password: str, 
                       new_password: str) -> bool:
        """Change user password"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        if not self.verify_password(old_password, user['hashed_password']):
            return False
        
        user['hashed_password'] = self.hash_password(new_password)
        user['password_changed'] = datetime.now().isoformat()
        self._save_users()
        return True
    
    def enable_two_factor(self, username: str) -> str:
        """Enable 2FA for user and return secret"""
        if username not in self.users:
            return None
        
        secret = pyotp.random_base32()
        self.users[username]['two_factor_enabled'] = True
        self.users[username]['two_factor_secret'] = secret
        self._save_users()
        
        # Generate provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name='MCP WooCommerce Suite'
        )
        
        return provisioning_uri
    
    def _verify_otp(self, secret: str, otp_code: str) -> bool:
        """Verify OTP code"""
        if not secret:
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(otp_code, valid_window=1)


class APIKeyManager:
    """Manages API keys for external access"""
    
    def __init__(self):
        self.keys_file = settings.data_dir / "api_keys.json"
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys"""
        if self.keys_file.exists():
            with open(self.keys_file, 'r') as f:
                self.keys = json.load(f)
        else:
            self.keys = {}
    
    def _save_keys(self):
        """Save API keys"""
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys, f, indent=2)
    
    def generate_api_key(self, name: str, permissions: List[str]) -> str:
        """Generate new API key"""
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        self.keys[key_hash] = {
            "name": name,
            "permissions": permissions,
            "created": datetime.now().isoformat(),
            "last_used": None,
            "active": True
        }
        
        self._save_keys()
        return key
    
    def verify_api_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return permissions"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self.keys and self.keys[key_hash]['active']:
            self.keys[key_hash]['last_used'] = datetime.now().isoformat()
            self._save_keys()
            return self.keys[key_hash]
        
        return None
    
    def revoke_api_key(self, key: str) -> bool:
        """Revoke API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self.keys:
            self.keys[key_hash]['active'] = False
            self.keys[key_hash]['revoked'] = datetime.now().isoformat()
            self._save_keys()
            return True
        
        return False