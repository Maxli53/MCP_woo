<?php
/**
 * MCP Admin Suite Login Page
 * Secure authentication for admin access
 */

require_once 'auth.php';

// If already authenticated, redirect to dashboard
if (isAuthenticated()) {
    $redirect = $_SESSION['redirect_after_login'] ?? 'mcp_dashboard.php';
    unset($_SESSION['redirect_after_login']);
    header("Location: $redirect");
    exit;
}

$error_message = '';
$success_message = '';

// Handle login form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    
    // Check rate limiting
    if (!checkRateLimit()) {
        $error_message = 'Too many login attempts. Please wait 15 minutes before trying again.';
    } else {
        $username = trim($_POST['username'] ?? '');
        $password = $_POST['password'] ?? '';
        
        if (empty($username) || empty($password)) {
            $error_message = 'Please enter both username and password.';
        } else {
            if (authenticateUser($username, $password)) {
                // Successful login - redirect to requested page or dashboard
                $redirect = $_SESSION['redirect_after_login'] ?? 'mcp_dashboard.php';
                unset($_SESSION['redirect_after_login']);
                header("Location: $redirect");
                exit;
            } else {
                recordFailedAttempt();
                $error_message = 'Invalid username or password.';
                
                // Add small delay to prevent brute force
                sleep(2);
            }
        }
    }
}

// Handle messages
if (isset($_GET['message'])) {
    switch ($_GET['message']) {
        case 'logged_out':
            $success_message = 'You have been successfully logged out.';
            break;
        case 'session_expired':
            $error_message = 'Your session has expired. Please log in again.';
            break;
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Admin Login - conventum.kg</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            width: 100%;
            max-width: 400px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .login-header h2 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .login-header p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .form-control {
            border-radius: 10px;
            border: 1px solid #ddd;
            padding: 12px 15px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        
        .btn-login {
            background: linear-gradient(45deg, #667eea, #764ba2);
            border: none;
            border-radius: 10px;
            padding: 12px;
            color: white;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            color: white;
        }
        
        .alert {
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .security-info {
            background: rgba(13, 110, 253, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            font-size: 0.85rem;
            color: #666;
        }
        
        .input-group-text {
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid #ddd;
            border-right: none;
            border-radius: 10px 0 0 10px;
        }
        
        .input-group .form-control {
            border-left: none;
            border-radius: 0 10px 10px 0;
            margin-bottom: 0;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .loading-spinner {
            display: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h2><i class="fas fa-shield-alt text-primary"></i> MCP Admin</h2>
            <p>Secure access to conventum.kg management suite</p>
        </div>
        
        <?php if ($error_message): ?>
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                <?= htmlspecialchars($error_message) ?>
            </div>
        <?php endif; ?>
        
        <?php if ($success_message): ?>
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i>
                <?= htmlspecialchars($success_message) ?>
            </div>
        <?php endif; ?>
        
        <form method="POST" id="loginForm">
            <div class="input-group">
                <span class="input-group-text">
                    <i class="fas fa-user"></i>
                </span>
                <input type="text" 
                       class="form-control" 
                       name="username" 
                       placeholder="Username"
                       required
                       autocomplete="username">
            </div>
            
            <div class="input-group">
                <span class="input-group-text">
                    <i class="fas fa-lock"></i>
                </span>
                <input type="password" 
                       class="form-control" 
                       name="password" 
                       placeholder="Password"
                       required
                       autocomplete="current-password">
            </div>
            
            <button type="submit" name="login" class="btn btn-login" id="loginBtn">
                <span class="login-text">
                    <i class="fas fa-sign-in-alt"></i>
                    Access MCP Suite
                </span>
                <span class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    Authenticating...
                </span>
            </button>
        </form>
        
        <div class="security-info">
            <div class="mb-2">
                <i class="fas fa-info-circle text-primary"></i>
                <strong>Security Information</strong>
            </div>
            <ul class="mb-0" style="font-size: 0.8rem; padding-left: 20px;">
                <li>Sessions expire after 1 hour of inactivity</li>
                <li>5 failed attempts will lock access for 15 minutes</li>
                <li>Admin-only access - no customer data exposure</li>
            </ul>
        </div>
    </div>
    
    <script>
        // Add loading state on form submission
        document.getElementById('loginForm').addEventListener('submit', function() {
            const btn = document.getElementById('loginBtn');
            const loginText = btn.querySelector('.login-text');
            const spinner = btn.querySelector('.loading-spinner');
            
            loginText.style.display = 'none';
            spinner.style.display = 'inline';
            btn.disabled = true;
        });
        
        // Focus on username field
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelector('input[name="username"]').focus();
        });
        
        // Enter key navigation
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const username = document.querySelector('input[name="username"]');
                const password = document.querySelector('input[name="password"]');
                
                if (document.activeElement === username && username.value.trim()) {
                    password.focus();
                    e.preventDefault();
                }
            }
        });
    </script>
</body>
</html>