<?php
/**
 * WordPress Content Showcase Manager
 * PHP-based alternative to MCP server for FTP-only hosting
 */

session_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Database configuration
define('DB_HOST', 'mysql');
define('DB_USER', 'user133859_mastconv');
define('DB_PASS', 'dsavdsEv616515s');
define('DB_NAME', 'user133859_conv');

// Connect to database
try {
    $pdo = new PDO("mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4", DB_USER, DB_PASS);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    die("Connection failed: " . $e->getMessage());
}

// Handle form submissions
$message = '';
$message_type = '';

if ($_POST) {
    if (isset($_POST['action']) && $_POST['action'] === 'create_showcase') {
        $title = trim($_POST['title']);
        $content = trim($_POST['content']);
        $excerpt = trim($_POST['excerpt']);
        $post_type = $_POST['post_type'] ?? 'page';
        $status = $_POST['status'] ?? 'draft';
        
        if ($title && $content) {
            try {
                $stmt = $pdo->prepare("
                    INSERT INTO wp_posts (post_title, post_content, post_excerpt, post_type, 
                                         post_status, post_date, post_modified, post_author)
                    VALUES (?, ?, ?, ?, ?, NOW(), NOW(), 1)
                ");
                $stmt->execute([$title, $content, $excerpt, $post_type, $status]);
                $message = "Successfully created {$post_type}: '{$title}'";
                $message_type = 'success';
            } catch(Exception $e) {
                $message = "Error creating content: " . $e->getMessage();
                $message_type = 'error';
            }
        } else {
            $message = "Title and content are required";
            $message_type = 'error';
        }
    }
    
    if (isset($_POST['action']) && $_POST['action'] === 'update_content') {
        $post_id = (int)$_POST['post_id'];
        $title = trim($_POST['title']);
        $content = trim($_POST['content']);
        $excerpt = trim($_POST['excerpt']);
        
        if ($post_id && $title) {
            try {
                $stmt = $pdo->prepare("
                    UPDATE wp_posts 
                    SET post_title = ?, post_content = ?, post_excerpt = ?, post_modified = NOW()
                    WHERE ID = ?
                ");
                $stmt->execute([$title, $content, $excerpt, $post_id]);
                $message = "Successfully updated content for post ID {$post_id}";
                $message_type = 'success';
            } catch(Exception $e) {
                $message = "Error updating content: " . $e->getMessage();
                $message_type = 'error';
            }
        }
    }
}

// Get content for editing
$edit_post = null;
if (isset($_GET['edit'])) {
    $edit_id = (int)$_GET['edit'];
    $stmt = $pdo->prepare("SELECT * FROM wp_posts WHERE ID = ?");
    $stmt->execute([$edit_id]);
    $edit_post = $stmt->fetch();
}

// Get existing content
$content_query = "
    SELECT ID, post_title, post_type, post_status, post_date, post_modified,
           SUBSTRING(post_content, 1, 200) as content_preview
    FROM wp_posts 
    WHERE post_type IN ('post', 'page') 
    AND post_status IN ('publish', 'draft')
    ORDER BY post_modified DESC 
    LIMIT 20
";
$existing_content = $pdo->query($content_query)->fetchAll();

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Showcase Manager - conventum.kg</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
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
        .card-body { padding: 20px; }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        input[type="text"], textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea { height: 200px; resize: vertical; }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            transition: background 0.3s;
        }
        .btn:hover { background: #5a6fd8; }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover { background: #5a6268; }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 6px;
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
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e3e8ee; }
        th { background: #f8f9fa; font-weight: 600; color: #666; }
        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-publish { background: #d4edda; color: #28a745; }
        .status-draft { background: #fff3cd; color: #856404; }
        .post-title { font-weight: 600; color: #333; }
        .content-preview { color: #666; font-size: 14px; }
        .actions { white-space: nowrap; }
        .btn-small {
            padding: 6px 12px;
            font-size: 14px;
            margin-right: 5px;
        }
        @media (max-width: 768px) {
            .content-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Content Showcase Manager</h1>
            <p class="subtitle">Create and manage product/service showcase content for conventum.kg</p>
        </div>

        <?php if ($message): ?>
        <div class="alert alert-<?php echo $message_type; ?>">
            <?php echo htmlspecialchars($message); ?>
        </div>
        <?php endif; ?>

        <div class="content-grid">
            <div class="card">
                <div class="card-header">
                    <?php echo $edit_post ? '✏️ Edit Content' : '➕ Create New Showcase Content'; ?>
                </div>
                <div class="card-body">
                    <form method="post">
                        <input type="hidden" name="action" value="<?php echo $edit_post ? 'update_content' : 'create_showcase'; ?>">
                        <?php if ($edit_post): ?>
                        <input type="hidden" name="post_id" value="<?php echo $edit_post['ID']; ?>">
                        <?php endif; ?>
                        
                        <div class="form-group">
                            <label for="title">Title *</label>
                            <input type="text" id="title" name="title" required 
                                   value="<?php echo $edit_post ? htmlspecialchars($edit_post['post_title']) : ''; ?>" 
                                   placeholder="Product/Service Title">
                        </div>

                        <div class="form-group">
                            <label for="content">Content *</label>
                            <textarea id="content" name="content" required 
                                      placeholder="Detailed description of your product or service..."><?php echo $edit_post ? htmlspecialchars($edit_post['post_content']) : ''; ?></textarea>
                        </div>

                        <div class="form-group">
                            <label for="excerpt">Excerpt/Summary</label>
                            <input type="text" id="excerpt" name="excerpt" 
                                   value="<?php echo $edit_post ? htmlspecialchars($edit_post['post_excerpt']) : ''; ?>" 
                                   placeholder="Brief summary for SEO and previews">
                        </div>

                        <?php if (!$edit_post): ?>
                        <div class="form-group">
                            <label for="post_type">Content Type</label>
                            <select id="post_type" name="post_type">
                                <option value="page">Page</option>
                                <option value="post">Post</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="status">Status</label>
                            <select id="status" name="status">
                                <option value="draft">Draft</option>
                                <option value="publish">Publish</option>
                            </select>
                        </div>
                        <?php endif; ?>

                        <button type="submit" class="btn">
                            <?php echo $edit_post ? 'Update Content' : 'Create Showcase'; ?>
                        </button>
                        <?php if ($edit_post): ?>
                        <a href="showcase_manager.php" class="btn btn-secondary">Cancel</a>
                        <?php endif; ?>
                    </form>
                </div>
            </div>

            <div class="card">
                <div class="card-header">📋 Existing Content</div>
                <div class="card-body">
                    <table>
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach($existing_content as $item): ?>
                            <tr>
                                <td>
                                    <div class="post-title"><?php echo htmlspecialchars($item['post_title']); ?></div>
                                    <div class="content-preview"><?php echo htmlspecialchars($item['content_preview']); ?>...</div>
                                </td>
                                <td><?php echo ucfirst($item['post_type']); ?></td>
                                <td>
                                    <span class="status-badge status-<?php echo $item['post_status']; ?>">
                                        <?php echo ucfirst($item['post_status']); ?>
                                    </span>
                                </td>
                                <td class="actions">
                                    <a href="?edit=<?php echo $item['ID']; ?>" class="btn btn-small">Edit</a>
                                    <a href="https://conventum.kg/wp-admin/post.php?post=<?php echo $item['ID']; ?>&action=edit" 
                                       target="_blank" class="btn btn-small btn-secondary">WP Edit</a>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>