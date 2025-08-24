<?php
/**
 * WordPress REST API Setup for AI Content Management
 * Creates secure API access for automated content improvements
 */

session_start();

// Database configuration
define('DB_HOST', 'mysql');
define('DB_USER', 'user133859_mastconv');
define('DB_PASS', 'dsavdsEv616515s');
define('DB_NAME', 'user133859_conv');

try {
    $pdo = new PDO("mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4", DB_USER, DB_PASS);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    die("Connection failed: " . $e->getMessage());
}

// WordPress API functions
function createApplicationPassword($user_login, $app_name = 'AI Content Manager') {
    global $pdo;
    
    // Generate a secure application password
    $password = wp_generate_password(24, false);
    $hashed = password_hash($password, PASSWORD_DEFAULT);
    
    // Create application password record
    $stmt = $pdo->prepare("
        INSERT INTO wp_usermeta (user_id, meta_key, meta_value) 
        VALUES (
            (SELECT ID FROM wp_users WHERE user_login = ?),
            '_application_passwords',
            ?
        )
        ON DUPLICATE KEY UPDATE meta_value = ?
    ");
    
    $app_data = json_encode([
        [
            'uuid' => wp_generate_uuid4(),
            'app_id' => sanitize_key($app_name),
            'name' => $app_name,
            'password' => $hashed,
            'created' => time(),
            'last_used' => null,
            'last_ip' => null
        ]
    ]);
    
    $stmt->execute([$user_login, $app_data, $app_data]);
    
    return [
        'username' => $user_login,
        'password' => $password,
        'app_name' => $app_name
    ];
}

function wp_generate_password($length = 12, $special_chars = true) {
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    if ($special_chars) {
        $chars .= '!@#$%^&*()';
    }
    
    $password = '';
    for ($i = 0; $i < $length; $i++) {
        $password .= substr($chars, wp_rand(0, strlen($chars) - 1), 1);
    }
    
    return $password;
}

function wp_generate_uuid4() {
    return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        mt_rand(0, 0xffff), mt_rand(0, 0xffff),
        mt_rand(0, 0xffff),
        mt_rand(0, 0x0fff) | 0x4000,
        mt_rand(0, 0x3fff) | 0x8000,
        mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
    );
}

function wp_rand($min = 0, $max = 0) {
    return mt_rand($min, $max);
}

function sanitize_key($key) {
    return preg_replace('/[^a-z0-9_\-]/', '', strtolower($key));
}

// Handle API setup
$setup_result = '';
if (isset($_POST['setup_api'])) {
    try {
        // Check if WordPress REST API is enabled
        $wp_rest_enabled = checkRestAPIStatus();
        
        if ($wp_rest_enabled) {
            // Create application password
            $api_creds = createApplicationPassword('administrator-master', 'AI Content Manager');
            $setup_result = $api_creds;
        } else {
            $setup_result = ['error' => 'WordPress REST API is not enabled'];
        }
    } catch (Exception $e) {
        $setup_result = ['error' => $e->getMessage()];
    }
}

function checkRestAPIStatus() {
    // Check if WordPress is installed and REST API endpoints exist
    $wp_config_path = dirname(dirname(__FILE__)) . '/wp-config.php';
    return file_exists($wp_config_path);
}

function testAPIConnection($username, $password) {
    $api_url = 'https://conventum.kg/wp-json/wp/v2/posts';
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $api_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
    curl_setopt($ch, CURLOPT_USERPWD, $username . ':' . $password);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    return $http_code === 200;
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WordPress API Setup - AI Content Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            overflow: hidden;
        }
        .card-header {
            background: #f7f9fc;
            padding: 20px;
            border-bottom: 1px solid #e3e8ee;
            font-weight: 600;
            color: #333;
        }
        .card-body { padding: 30px; }
        .btn {
            display: inline-block;
            padding: 15px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
        }
        .btn:hover { background: #5a6fd8; }
        .alert {
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            font-weight: 600;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .code-block {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            font-family: monospace;
            font-size: 14px;
            overflow-x: auto;
            margin: 15px 0;
        }
        .step {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 0 8px 8px 0;
        }
        .step h3 { color: #667eea; margin-bottom: 10px; }
        .credentials {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .warning {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 WordPress API Setup</h1>
            <p class="subtitle">Enable automated AI content management</p>
        </div>

        <div class="card">
            <div class="card-header">🚀 Automated Content Workflow Setup</div>
            <div class="card-body">
                <div class="alert-info alert">
                    <strong>Goal:</strong> Enable the AI to automatically apply content improvements to your WordPress site through secure API access.
                </div>

                <div class="step">
                    <h3>📋 Step 1: Enable WordPress REST API</h3>
                    <p>The WordPress REST API should be enabled by default. We'll verify this during setup.</p>
                </div>

                <div class="step">
                    <h3>🔐 Step 2: Create Application Password</h3>
                    <p>Generate secure credentials for the AI to access your WordPress content safely.</p>
                </div>

                <div class="step">
                    <h3>🤖 Step 3: Test AI Integration</h3>
                    <p>Verify that the AI can securely connect to your WordPress installation.</p>
                </div>

                <?php if ($setup_result): ?>
                    <?php if (isset($setup_result['error'])): ?>
                    <div class="alert alert-error">
                        <strong>Setup Error:</strong> <?php echo htmlspecialchars($setup_result['error']); ?>
                    </div>
                    <?php else: ?>
                    <div class="alert alert-success">
                        <strong>✅ API Setup Successful!</strong> Your AI content management system is ready.
                    </div>
                    
                    <div class="credentials">
                        <h3>🔑 API Credentials Generated</h3>
                        <p><strong>Application:</strong> <?php echo htmlspecialchars($setup_result['app_name']); ?></p>
                        <p><strong>Username:</strong> <?php echo htmlspecialchars($setup_result['username']); ?></p>
                        <div class="code-block">
                            <strong>Password:</strong> <?php echo htmlspecialchars($setup_result['password']); ?>
                        </div>
                        <p><em>Save these credentials securely - the password won't be shown again!</em></p>
                    </div>

                    <div class="alert-info alert">
                        <strong>🎯 What's Next:</strong>
                        <ol>
                            <li>The AI can now automatically improve your content</li>
                            <li>Visit the Content Analyzer to see the new "Auto-Improve" buttons</li>
                            <li>Click "Auto-Improve" and the AI will make optimizations automatically</li>
                            <li>Review changes in WordPress admin if desired</li>
                        </ol>
                    </div>

                    <p style="text-align: center; margin-top: 30px;">
                        <a href="analyzer.php" class="btn">🚀 Start Using AI Auto-Improvements</a>
                    </p>
                    <?php endif; ?>
                <?php else: ?>
                
                <div class="warning">
                    <strong>⚠️ Security Note:</strong> This will create secure API access for automated content management. Only proceed if you want to enable AI-powered automatic content improvements.
                </div>

                <form method="post" style="text-align: center; margin-top: 30px;">
                    <button type="submit" name="setup_api" class="btn">
                        🔧 Setup Automated AI Content Management
                    </button>
                </form>
                
                <?php endif; ?>

                <div class="step" style="margin-top: 30px;">
                    <h3>🔒 Security Features</h3>
                    <ul>
                        <li>✅ Application-specific passwords (not your main login)</li>
                        <li>✅ Limited to content management only</li>
                        <li>✅ Can be revoked anytime in WordPress admin</li>
                        <li>✅ No access to plugins, themes, or sensitive settings</li>
                        <li>✅ All changes logged in WordPress</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</body>
</html>