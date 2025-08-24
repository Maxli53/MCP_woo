<?php
/**
 * Password Hash Generator for MCP Admin
 * Run this once to generate secure password hash for .env file
 */

// CHANGE THIS TO YOUR DESIRED PASSWORD
$your_password = 'your_secure_admin_password_here';
$your_username = 'admin'; // Change this if desired

if ($your_password === 'your_secure_admin_password_here') {
    echo "<h3>⚠️ Please set your password first!</h3>";
    echo "<p>Edit this file and change the \$your_password variable to your desired password.</p>";
    echo "<p>Optionally change \$your_username if you want a different username.</p>";
    exit;
}

$hash = password_hash($your_password, PASSWORD_DEFAULT);

echo "<h2>🔐 MCP Admin Password Setup</h2>";
echo "<p><strong>Username:</strong> " . htmlspecialchars($your_username) . "</p>";
echo "<p><strong>Password:</strong> " . htmlspecialchars($your_password) . "</p>";
echo "<p><strong>Generated hash:</strong></p>";
echo "<code style='background: #f0f0f0; padding: 10px; display: block; word-break: break-all;'>" . $hash . "</code>";

echo "<h3>📝 Setup Instructions:</h3>";
echo "<ol>";
echo "<li>Copy the values above</li>";
echo "<li>Edit your <code>.env</code> file</li>";
echo "<li>Update ADMIN_USERNAME and ADMIN_PASSWORD</li>";
echo "<li>Delete this file for security</li>";
echo "</ol>";

echo "<h3>🔧 Edit .env file:</h3>";
echo "<pre style='background: #f8f8f8; padding: 15px; border-left: 4px solid #007bff;'>";
echo "# Admin Authentication\n";
echo "ADMIN_USERNAME=" . htmlspecialchars($your_username) . "\n";
echo "ADMIN_PASSWORD=" . $hash . "\n";
echo "</pre>";

echo "<h3>🎯 Benefits of .env configuration:</h3>";
echo "<ul>";
echo "<li>✅ All credentials in one secure file</li>";
echo "<li>✅ Easy to update without editing code</li>";
echo "<li>✅ Better security practices</li>";
echo "<li>✅ Environment-specific settings</li>";
echo "</ul>";

echo "<p><strong>⚠️ Security Note:</strong> Delete this file after updating your .env!</p>";
?>