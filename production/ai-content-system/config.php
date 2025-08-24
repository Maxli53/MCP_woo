<?php
/**
 * Configuration Loader for MCP Admin Suite
 * Loads environment variables from .env file
 */

class Config {
    private static $config = [];
    private static $loaded = false;
    
    /**
     * Load configuration from .env file
     */
    public static function load($envFile = '.env') {
        if (self::$loaded) {
            return;
        }
        
        if (!file_exists($envFile)) {
            throw new Exception("Environment file not found: $envFile");
        }
        
        $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        
        foreach ($lines as $line) {
            // Skip comments
            if (strpos(trim($line), '#') === 0) {
                continue;
            }
            
            // Parse key=value pairs
            if (strpos($line, '=') !== false) {
                list($key, $value) = explode('=', $line, 2);
                $key = trim($key);
                $value = trim($value);
                
                // Remove quotes if present
                if ((substr($value, 0, 1) === '"' && substr($value, -1) === '"') ||
                    (substr($value, 0, 1) === "'" && substr($value, -1) === "'")) {
                    $value = substr($value, 1, -1);
                }
                
                self::$config[$key] = $value;
                
                // Also set as environment variable if not already set
                if (!isset($_ENV[$key])) {
                    $_ENV[$key] = $value;
                    putenv("$key=$value");
                }
            }
        }
        
        self::$loaded = true;
    }
    
    /**
     * Get configuration value
     */
    public static function get($key, $default = null) {
        if (!self::$loaded) {
            self::load();
        }
        
        // Try environment variable first
        $value = getenv($key);
        if ($value !== false) {
            return $value;
        }
        
        // Then try loaded config
        return self::$config[$key] ?? $default;
    }
    
    /**
     * Get database configuration
     */
    public static function getDatabase() {
        return [
            'host' => self::get('DB_HOST', 'mysql'),
            'user' => self::get('DB_USER'),
            'password' => self::get('DB_PASSWORD'),
            'name' => self::get('DB_NAME')
        ];
    }
    
    /**
     * Get authentication configuration
     */
    public static function getAuth() {
        return [
            'username' => self::get('ADMIN_USERNAME', 'admin'),
            'password' => self::get('ADMIN_PASSWORD'),
            'session_timeout' => (int)self::get('SESSION_TIMEOUT', 3600),
            'max_attempts' => (int)self::get('MAX_LOGIN_ATTEMPTS', 5),
            'lockout_duration' => (int)self::get('LOCKOUT_DURATION', 900)
        ];
    }
    
    /**
     * Check if in debug mode
     */
    public static function isDebug() {
        return strtolower(self::get('DEBUG', 'false')) === 'true';
    }
    
    /**
     * Get environment (production, development, etc.)
     */
    public static function getEnvironment() {
        return self::get('ENVIRONMENT', 'development');
    }
}

// Auto-load configuration
try {
    Config::load();
} catch (Exception $e) {
    // Fallback to default configuration if .env file not found
    if (Config::isDebug()) {
        error_log("Config warning: " . $e->getMessage());
    }
}
?>