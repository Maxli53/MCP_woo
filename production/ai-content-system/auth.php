<?php
/**
 * MCP Admin Authentication System
 * Secure login protection for MCP Admin Suite
 */

require_once 'config.php';
session_start();

// Load authentication configuration from environment
$auth_config = Config::getAuth();

/**
 * Generate password hash for setup
 * Run this once to generate hash for your password
 */
function generatePasswordHash($password) {
    return password_hash($password, PASSWORD_DEFAULT);
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    if (!isset($_SESSION['mcp_authenticated']) || !isset($_SESSION['mcp_login_time'])) {
        return false;
    }
    
    // Check session timeout
    global $auth_config;
    if (time() - $_SESSION['mcp_login_time'] > $auth_config['session_timeout']) {
        destroySession();
        return false;
    }
    
    // Update last activity time
    $_SESSION['mcp_login_time'] = time();
    
    return $_SESSION['mcp_authenticated'] === true;
}

/**
 * Authenticate user credentials
 */
function authenticateUser($username, $password) {
    global $auth_config;
    if ($username === $auth_config['username'] && password_verify($password, $auth_config['password'])) {
        $_SESSION['mcp_authenticated'] = true;
        $_SESSION['mcp_login_time'] = time();
        $_SESSION['mcp_username'] = $username;
        return true;
    }
    return false;
}

/**
 * Destroy authentication session
 */
function destroySession() {
    unset($_SESSION['mcp_authenticated']);
    unset($_SESSION['mcp_login_time']);
    unset($_SESSION['mcp_username']);
}

/**
 * Require authentication - call this at the top of protected pages
 */
function requireAuth() {
    if (!isAuthenticated()) {
        // Store the requested page for redirect after login
        $_SESSION['redirect_after_login'] = $_SERVER['REQUEST_URI'];
        
        // Redirect to login page
        header('Location: login.php');
        exit;
    }
}

/**
 * Get current authenticated user
 */
function getCurrentUser() {
    return $_SESSION['mcp_username'] ?? null;
}

/**
 * Rate limiting for login attempts
 */
function checkRateLimit() {
    $ip = $_SERVER['REMOTE_ADDR'];
    $current_time = time();
    
    // Initialize or get attempts data
    if (!isset($_SESSION['login_attempts'])) {
        $_SESSION['login_attempts'] = [];
    }
    
    // Clean old attempts (older than 15 minutes)
    $_SESSION['login_attempts'] = array_filter($_SESSION['login_attempts'], function($attempt) use ($current_time) {
        return ($current_time - $attempt) < 900; // 15 minutes
    });
    
    // Check if too many attempts
    global $auth_config;
    if (count($_SESSION['login_attempts']) >= $auth_config['max_attempts']) {
        return false;
    }
    
    return true;
}

/**
 * Record failed login attempt
 */
function recordFailedAttempt() {
    if (!isset($_SESSION['login_attempts'])) {
        $_SESSION['login_attempts'] = [];
    }
    $_SESSION['login_attempts'][] = time();
}

// Handle logout
if (isset($_GET['logout'])) {
    destroySession();
    header('Location: login.php?message=logged_out');
    exit;
}

// Uncomment the line below and run this file once to generate a new password hash
// echo generatePasswordHash('your_secure_password_here'); exit;
?>