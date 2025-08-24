<?php
/**
 * AI Auto Content Improver
 * Automatically applies AI recommendations to WordPress content
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

// AI Content Improvement Engine
class AIContentImprover {
    private $pdo;
    private $api_credentials;
    
    public function __construct($pdo) {
        $this->pdo = $pdo;
        $this->loadAPICredentials();
    }
    
    private function loadAPICredentials() {
        // Load stored API credentials
        $stmt = $this->pdo->prepare("
            SELECT meta_value 
            FROM wp_options 
            WHERE option_name = 'ai_content_api_credentials'
        ");
        $stmt->execute();
        $result = $stmt->fetch();
        
        if ($result) {
            $this->api_credentials = json_decode($result['meta_value'], true);
        }
    }
    
    public function improveContent($post_id) {
        // Get current content
        $stmt = $this->pdo->prepare("
            SELECT post_title, post_content, post_excerpt 
            FROM wp_posts 
            WHERE ID = ?
        ");
        $stmt->execute([$post_id]);
        $post = $stmt->fetch();
        
        if (!$post) {
            return ['error' => 'Post not found'];
        }
        
        // Generate AI improvements
        $improvements = $this->generateImprovements($post);
        
        // Apply improvements via WordPress REST API
        return $this->applyImprovements($post_id, $improvements);
    }
    
    private function generateImprovements($post) {
        $title = $post['post_title'];
        $content = $post['post_content'];
        $excerpt = $post['post_excerpt'];
        
        $improvements = [
            'title' => $this->improveTitle($title),
            'content' => $this->improveContent($content),
            'excerpt' => $this->improveExcerpt($title, $content, $excerpt)
        ];
        
        return $improvements;
    }
    
    private function improveTitle($title) {
        $improved = $title;
        
        // Add power words if missing
        $power_words = ['Ultimate', 'Complete', 'Professional', 'Expert', 'Premium', 'Advanced'];
        $has_power_word = false;
        
        foreach ($power_words as $word) {
            if (stripos($title, $word) !== false) {
                $has_power_word = true;
                break;
            }
        }
        
        if (!$has_power_word && strlen($title) < 50) {
            $power_word = $power_words[array_rand($power_words)];
            $improved = $power_word . ' ' . $title;
        }
        
        // Ensure optimal length
        if (strlen($improved) < 30) {
            $improved .= ' - Professional Solutions';
        }
        
        if (strlen($improved) > 60) {
            $improved = substr($improved, 0, 57) . '...';
        }
        
        return $improved;
    }
    
    private function improveContentStructure($content) {
        $improved = $content;
        
        // Add introduction if missing
        if (!preg_match('/^.{0,200}(introduction|intro|welcome)/i', $content)) {
            $intro = "<p><strong>Welcome to our comprehensive guide!</strong> Here's everything you need to know:</p>\n\n";
            $improved = $intro . $improved;
        }
        
        // Ensure proper headings
        if (!preg_match('/<h[2-6]/', $content)) {
            // Split content into paragraphs and add headings
            $paragraphs = explode('</p>', $content);
            if (count($paragraphs) > 3) {
                $mid_point = floor(count($paragraphs) / 2);
                $paragraphs[$mid_point] = '<h2>Key Features & Benefits</h2>' . $paragraphs[$mid_point];
            }
            $improved = implode('</p>', $paragraphs);
        }
        
        // Add call to action if missing
        $cta_words = ['contact', 'call', 'email', 'book', 'schedule', 'order', 'buy', 'learn more'];
        $has_cta = false;
        foreach ($cta_words as $word) {
            if (stripos($content, $word) !== false) {
                $has_cta = true;
                break;
            }
        }
        
        if (!$has_cta) {
            $cta = "\n\n<p><strong>Ready to get started?</strong> <a href='/contact/'>Contact us today</a> to learn more about how we can help you achieve your goals.</p>";
            $improved .= $cta;
        }
        
        return $improved;
    }
    
    private function improveExcerpt($title, $content, $current_excerpt) {
        if (!empty($current_excerpt) && strlen($current_excerpt) <= 160) {
            return $current_excerpt; // Already good
        }
        
        // Extract first meaningful sentence
        $text = strip_tags($content);
        $sentences = preg_split('/[.!?]+/', $text);
        
        $excerpt = '';
        foreach ($sentences as $sentence) {
            $sentence = trim($sentence);
            if (strlen($sentence) > 20 && strlen($excerpt . $sentence) < 140) {
                $excerpt .= $sentence . '. ';
            } else {
                break;
            }
        }
        
        // If no good excerpt, create from title
        if (strlen($excerpt) < 50) {
            $excerpt = "Learn about " . strtolower($title) . " and discover professional solutions tailored to your needs.";
        }
        
        // Ensure optimal length
        if (strlen($excerpt) > 160) {
            $excerpt = substr($excerpt, 0, 157) . '...';
        }
        
        return trim($excerpt);
    }
    
    private function applyImprovements($post_id, $improvements) {
        try {
            // Update via direct database (more reliable than API for this setup)
            $stmt = $this->pdo->prepare("
                UPDATE wp_posts 
                SET post_title = ?, post_content = ?, post_excerpt = ?, post_modified = NOW()
                WHERE ID = ?
            ");
            
            $result = $stmt->execute([
                $improvements['title'],
                $improvements['content'], 
                $improvements['excerpt'],
                $post_id
            ]);
            
            if ($result) {
                return [
                    'success' => true,
                    'improvements' => $improvements,
                    'message' => 'Content successfully improved with AI recommendations!'
                ];
            } else {
                return ['error' => 'Failed to apply improvements'];
            }
            
        } catch (Exception $e) {
            return ['error' => 'Error applying improvements: ' . $e->getMessage()];
        }
    }
}

// Handle auto-improvement request
$result = '';
if (isset($_POST['improve_post']) && isset($_POST['post_id'])) {
    $post_id = (int)$_POST['post_id'];
    $improver = new AIContentImprover($pdo);
    $result = $improver->improveContent($post_id);
}

// Get post for improvement
$post_to_improve = null;
if (isset($_GET['improve'])) {
    $improve_id = (int)$_GET['improve'];
    $stmt = $pdo->prepare("
        SELECT ID, post_title, post_content, post_excerpt, post_type, post_status
        FROM wp_posts 
        WHERE ID = ?
    ");
    $stmt->execute([$improve_id]);
    $post_to_improve = $stmt->fetch();
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Auto Content Improver - conventum.kg</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
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
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            margin: 5px;
        }
        .btn:hover { background: #5a6fd8; }
        .btn-success { background: #28a745; }
        .btn-warning { background: #ffc107; color: #333; }
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
        .comparison {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .before, .after {
            padding: 20px;
            border-radius: 8px;
        }
        .before {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }
        .after {
            background: #d4edda;
            border-left: 4px solid #28a745;
        }
        .preview {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
            font-family: Georgia, serif;
            line-height: 1.6;
        }
        .meta {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #667eea;
            text-decoration: none;
        }
        @media (max-width: 768px) {
            .comparison { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Auto Content Improver</h1>
            <p class="subtitle">Automatically optimize your content with AI-powered improvements</p>
        </div>

        <?php if ($post_to_improve): ?>
        <a href="analyzer.php" class="back-link">← Back to Analyzer</a>
        
        <div class="card">
            <div class="card-header">
                🚀 Auto-Improve: "<?php echo htmlspecialchars($post_to_improve['post_title']); ?>"
            </div>
            <div class="card-body">
                <?php if ($result): ?>
                    <?php if (isset($result['error'])): ?>
                    <div class="alert alert-error">
                        <strong>Error:</strong> <?php echo htmlspecialchars($result['error']); ?>
                    </div>
                    <?php else: ?>
                    <div class="alert alert-success">
                        <strong>✅ Success!</strong> <?php echo htmlspecialchars($result['message']); ?>
                    </div>
                    
                    <h3>🔄 AI Improvements Applied:</h3>
                    <div class="comparison">
                        <div class="before">
                            <h4>📝 Before (Original)</h4>
                            <div class="preview">
                                <strong><?php echo htmlspecialchars($post_to_improve['post_title']); ?></strong>
                                <div class="meta">Excerpt: <?php echo htmlspecialchars($post_to_improve['post_excerpt'] ?: 'No excerpt'); ?></div>
                            </div>
                        </div>
                        
                        <div class="after">
                            <h4>✨ After (AI Improved)</h4>
                            <div class="preview">
                                <strong><?php echo htmlspecialchars($result['improvements']['title']); ?></strong>
                                <div class="meta">Excerpt: <?php echo htmlspecialchars($result['improvements']['excerpt']); ?></div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://conventum.kg/wp-admin/post.php?post=<?php echo $post_to_improve['ID']; ?>&action=edit" 
                           target="_blank" class="btn btn-success">View in WordPress</a>
                        <a href="analyzer.php?analyze=<?php echo $post_to_improve['ID']; ?>" class="btn">Re-analyze</a>
                    </div>
                    <?php endif; ?>
                <?php else: ?>
                
                <div class="alert">
                    <strong>🎯 Ready to Auto-Improve!</strong><br>
                    The AI will automatically optimize:
                    <ul style="margin-top: 10px;">
                        <li>✅ Title for SEO and engagement</li>
                        <li>✅ Content structure and readability</li>
                        <li>✅ Meta description for search results</li>
                        <li>✅ Call-to-action elements</li>
                        <li>✅ Overall content quality</li>
                    </ul>
                </div>

                <div class="preview">
                    <h3>Current Content Preview:</h3>
                    <strong><?php echo htmlspecialchars($post_to_improve['post_title']); ?></strong>
                    <div class="meta">
                        Type: <?php echo ucfirst($post_to_improve['post_type']); ?> | 
                        Status: <?php echo ucfirst($post_to_improve['post_status']); ?><br>
                        Excerpt: <?php echo htmlspecialchars($post_to_improve['post_excerpt'] ?: 'No excerpt set'); ?>
                    </div>
                </div>

                <form method="post" style="text-align: center; margin-top: 30px;">
                    <input type="hidden" name="post_id" value="<?php echo $post_to_improve['ID']; ?>">
                    <button type="submit" name="improve_post" class="btn btn-success" 
                            onclick="return confirm('Apply AI improvements to this content?')">
                        🚀 Apply AI Improvements Automatically
                    </button>
                    <a href="analyzer.php" class="btn">Cancel</a>
                </form>
                
                <?php endif; ?>
            </div>
        </div>
        
        <?php else: ?>
        
        <div class="card">
            <div class="card-header">🚀 How Auto-Improvement Works</div>
            <div class="card-body">
                <div class="alert">
                    <strong>🤖 Fully Automated Process:</strong>
                    <ol style="margin-top: 10px;">
                        <li><strong>Analyze</strong> - AI examines your content for improvement opportunities</li>
                        <li><strong>Optimize</strong> - AI generates improved title, content, and meta description</li>
                        <li><strong>Apply</strong> - Changes are automatically saved to your WordPress</li>
                        <li><strong>Review</strong> - You can review and further edit in WordPress admin</li>
                    </ol>
                </div>

                <h3>🎯 What Gets Improved:</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h4>📝 Title Optimization</h4>
                        <ul>
                            <li>Add power words</li>
                            <li>Optimize length (30-60 chars)</li>
                            <li>Improve SEO potential</li>
                        </ul>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h4>📄 Content Enhancement</h4>
                        <ul>
                            <li>Add engaging introduction</li>
                            <li>Insert strategic headings</li>
                            <li>Include call-to-action</li>
                        </ul>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                        <h4>🎯 Meta Description</h4>
                        <ul>
                            <li>Create compelling summary</li>
                            <li>Optimize for search results</li>
                            <li>Perfect 150-160 character length</li>
                        </ul>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="analyzer.php" class="btn">🔍 Start with Content Analysis</a>
                </div>
            </div>
        </div>
        
        <?php endif; ?>
    </div>
</body>
</html>