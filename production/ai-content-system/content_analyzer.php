<?php
/**
 * AI Content Analyzer for conventum.kg
 * Provides intelligent content analysis and recommendations
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

// AI Analysis Functions
function analyzeSEO($title, $content, $excerpt = '') {
    $analysis = [];
    $score = 100;
    
    // Title analysis
    $title_len = strlen($title);
    if ($title_len < 30) {
        $analysis[] = "❌ Title too short ({$title_len} chars) - aim for 30-60 characters";
        $score -= 15;
    } elseif ($title_len > 60) {
        $analysis[] = "⚠️ Title too long ({$title_len} chars) - keep under 60 characters";
        $score -= 10;
    } else {
        $analysis[] = "✅ Title length is optimal ({$title_len} chars)";
    }
    
    // Content analysis
    $content_words = str_word_count(strip_tags($content));
    if ($content_words < 300) {
        $analysis[] = "❌ Content too short ({$content_words} words) - aim for 300+ words";
        $score -= 20;
    } else {
        $analysis[] = "✅ Good content length ({$content_words} words)";
    }
    
    // Meta description
    $excerpt_len = strlen($excerpt);
    if (!$excerpt) {
        $analysis[] = "❌ Missing meta description - add excerpt for better SEO";
        $score -= 15;
    } elseif ($excerpt_len > 160) {
        $analysis[] = "⚠️ Meta description too long ({$excerpt_len} chars) - keep under 160";
        $score -= 5;
    } else {
        $analysis[] = "✅ Meta description length good ({$excerpt_len} chars)";
    }
    
    // Readability check
    $sentences = substr_count($content, '.') + substr_count($content, '!') + substr_count($content, '?');
    if ($sentences > 0) {
        $avg_words_per_sentence = $content_words / $sentences;
        if ($avg_words_per_sentence > 25) {
            $analysis[] = "⚠️ Sentences too long (avg {$avg_words_per_sentence} words) - aim for under 20";
            $score -= 10;
        } else {
            $analysis[] = "✅ Good sentence length (avg {$avg_words_per_sentence} words)";
        }
    }
    
    // Keyword density (simplified)
    $title_words = explode(' ', strtolower($title));
    $content_lower = strtolower($content);
    $keyword_found = false;
    foreach ($title_words as $word) {
        if (strlen($word) > 3 && substr_count($content_lower, $word) > 0) {
            $keyword_found = true;
            break;
        }
    }
    
    if (!$keyword_found) {
        $analysis[] = "⚠️ Title keywords not found in content - consider including them";
        $score -= 10;
    } else {
        $analysis[] = "✅ Title keywords found in content";
    }
    
    return ['score' => max(0, $score), 'analysis' => $analysis];
}

function analyzeContentQuality($title, $content) {
    $recommendations = [];
    
    // Engagement factors
    if (!preg_match('/[?!]/', $content)) {
        $recommendations[] = "💡 Add questions or exclamations to increase engagement";
    }
    
    if (substr_count($content, '<') < 3) {
        $recommendations[] = "💡 Use HTML formatting (headings, bold, lists) to improve readability";
    }
    
    if (!preg_match('/\b(you|your)\b/i', $content)) {
        $recommendations[] = "💡 Use 'you' and 'your' to speak directly to readers";
    }
    
    // Content structure
    if (!preg_match('/<h[2-6]/', $content)) {
        $recommendations[] = "💡 Add subheadings (H2, H3) to structure your content";
    }
    
    if (!preg_match('/<ul|<ol/', $content)) {
        $recommendations[] = "💡 Consider adding bullet points or lists for better readability";
    }
    
    // Call to action
    $cta_words = ['contact', 'call', 'email', 'book', 'schedule', 'order', 'buy', 'learn more'];
    $has_cta = false;
    foreach ($cta_words as $word) {
        if (stripos($content, $word) !== false) {
            $has_cta = true;
            break;
        }
    }
    
    if (!$has_cta) {
        $recommendations[] = "💡 Add a clear call-to-action (contact, book, learn more)";
    }
    
    return $recommendations;
}

function analyzeElementorUsage($post_id, $pdo) {
    $elementor_query = "
        SELECT meta_value 
        FROM wp_postmeta 
        WHERE post_id = ? AND meta_key = '_elementor_data'
    ";
    $stmt = $pdo->prepare($elementor_query);
    $stmt->execute([$post_id]);
    $elementor_data = $stmt->fetch();
    
    if ($elementor_data && $elementor_data['meta_value']) {
        try {
            $data = json_decode($elementor_data['meta_value'], true);
            $element_count = is_array($data) ? count($data) : 0;
            
            return [
                'uses_elementor' => true,
                'element_count' => $element_count,
                'recommendations' => [
                    $element_count > 20 ? "⚠️ High element count ({$element_count}) - consider simplifying for better performance" : "✅ Good element count ({$element_count})",
                    "💡 Elementor detected - ensure mobile responsiveness is tested",
                    "💡 Consider caching plugins to optimize Elementor page loading"
                ]
            ];
        } catch (Exception $e) {
            return ['uses_elementor' => true, 'element_count' => 0, 'recommendations' => []];
        }
    }
    
    return ['uses_elementor' => false, 'recommendations' => ["💡 This page doesn't use Elementor - consider using it for better visual design"]];
}

// Get content for analysis
$analyze_post = null;
if (isset($_GET['analyze'])) {
    $analyze_id = (int)$_GET['analyze'];
    $stmt = $pdo->prepare("
        SELECT ID, post_title, post_content, post_excerpt, post_type, post_status, post_date
        FROM wp_posts 
        WHERE ID = ?
    ");
    $stmt->execute([$analyze_id]);
    $analyze_post = $stmt->fetch();
}

// Get content list
$content_query = "
    SELECT ID, post_title, post_type, post_status, post_date, post_modified,
           CHAR_LENGTH(post_content) as content_length,
           CHAR_LENGTH(post_excerpt) as excerpt_length
    FROM wp_posts 
    WHERE post_type IN ('post', 'page') 
    AND post_status IN ('publish', 'draft')
    ORDER BY post_modified DESC 
    LIMIT 50
";
$content_list = $pdo->query($content_query)->fetchAll();

// Overall content statistics
$stats_query = "
    SELECT 
        COUNT(*) as total_content,
        AVG(CHAR_LENGTH(post_content)) as avg_content_length,
        COUNT(CASE WHEN CHAR_LENGTH(post_excerpt) > 0 THEN 1 END) as has_excerpt_count,
        COUNT(CASE WHEN post_status = 'publish' THEN 1 END) as published_count
    FROM wp_posts 
    WHERE post_type IN ('post', 'page')
";
$stats = $pdo->query($stats_query)->fetch();

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Analyzer - conventum.kg</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
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
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }
        .stat-value { font-size: 28px; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .analysis-result {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .seo-score {
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }
        .score-excellent { color: #28a745; }
        .score-good { color: #ffc107; }
        .score-poor { color: #dc3545; }
        .analysis-item {
            margin: 10px 0;
            padding: 8px;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #667eea;
        }
        .recommendation {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 10px;
            margin: 8px 0;
        }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e3e8ee; }
        th { background: #f8f9fa; font-weight: 600; color: #666; }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
        }
        .btn:hover { background: #5a6fd8; }
        .post-title { font-weight: 600; color: #333; }
        .content-length { color: #666; font-size: 14px; }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #667eea;
            text-decoration: none;
        }
        @media (max-width: 768px) {
            .content-grid { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Content Analyzer</h1>
            <p class="subtitle">Intelligent content analysis and SEO recommendations for conventum.kg</p>
        </div>

        <?php if ($analyze_post): ?>
        <a href="content_analyzer.php" class="back-link">← Back to Content List</a>
        
        <div class="card">
            <div class="card-header">
                🔍 Analysis Results for: "<?php echo htmlspecialchars($analyze_post['post_title']); ?>"
            </div>
            <div class="card-body">
                <?php
                $seo_analysis = analyzeSEO($analyze_post['post_title'], $analyze_post['post_content'], $analyze_post['post_excerpt']);
                $quality_recs = analyzeContentQuality($analyze_post['post_title'], $analyze_post['post_content']);
                $elementor_analysis = analyzeElementorUsage($analyze_post['ID'], $pdo);
                
                $score_class = 'score-poor';
                if ($seo_analysis['score'] >= 80) $score_class = 'score-excellent';
                elseif ($seo_analysis['score'] >= 60) $score_class = 'score-good';
                ?>
                
                <div class="analysis-result">
                    <div class="seo-score <?php echo $score_class; ?>">
                        <?php echo $seo_analysis['score']; ?>/100
                    </div>
                    <h3>🎯 SEO Analysis</h3>
                    <?php foreach ($seo_analysis['analysis'] as $item): ?>
                    <div class="analysis-item"><?php echo $item; ?></div>
                    <?php endforeach; ?>
                </div>
                
                <?php if (!empty($quality_recs)): ?>
                <div class="analysis-result">
                    <h3>💡 Content Quality Recommendations</h3>
                    <?php foreach ($quality_recs as $rec): ?>
                    <div class="recommendation"><?php echo $rec; ?></div>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
                
                <div class="analysis-result">
                    <h3>🎨 Design & Technical Analysis</h3>
                    <?php foreach ($elementor_analysis['recommendations'] as $rec): ?>
                    <div class="recommendation"><?php echo $rec; ?></div>
                    <?php endforeach; ?>
                </div>
                
                <div class="analysis-result">
                    <h3>📊 Content Metrics</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value"><?php echo str_word_count(strip_tags($analyze_post['post_content'])); ?></div>
                            <div class="stat-label">Word Count</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value"><?php echo strlen($analyze_post['post_title']); ?></div>
                            <div class="stat-label">Title Length</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value"><?php echo strlen($analyze_post['post_excerpt']); ?></div>
                            <div class="stat-label">Excerpt Length</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value"><?php echo $elementor_analysis['uses_elementor'] ? 'Yes' : 'No'; ?></div>
                            <div class="stat-label">Uses Elementor</div>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://conventum.kg/wp-admin/post.php?post=<?php echo $analyze_post['ID']; ?>&action=edit" 
                       target="_blank" class="btn">Edit in WordPress</a>
                </div>
            </div>
        </div>
        
        <?php else: ?>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value"><?php echo $stats['total_content']; ?></div>
                <div class="stat-label">Total Content Pieces</div>
            </div>
            <div class="stat-card">
                <div class="stat-value"><?php echo number_format($stats['avg_content_length']); ?></div>
                <div class="stat-label">Avg Content Length</div>
            </div>
            <div class="stat-card">
                <div class="stat-value"><?php echo round(($stats['has_excerpt_count'] / $stats['total_content']) * 100); ?>%</div>
                <div class="stat-label">Have Meta Descriptions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value"><?php echo $stats['published_count']; ?></div>
                <div class="stat-label">Published Content</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">📋 Content Analysis Dashboard</div>
            <div class="card-body">
                <table>
                    <thead>
                        <tr>
                            <th>Content</th>
                            <th>Type</th>
                            <th>Content Length</th>
                            <th>Has Excerpt</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($content_list as $item): ?>
                        <tr>
                            <td>
                                <div class="post-title"><?php echo htmlspecialchars($item['post_title']); ?></div>
                                <div class="content-length">Modified: <?php echo date('M d, Y', strtotime($item['post_modified'])); ?></div>
                            </td>
                            <td><?php echo ucfirst($item['post_type']); ?></td>
                            <td>
                                <?php 
                                $length = $item['content_length'];
                                $color = $length < 300 ? 'color: #dc3545' : ($length > 1000 ? 'color: #28a745' : 'color: #ffc107');
                                echo "<span style='{$color}'>{$length} chars</span>";
                                ?>
                            </td>
                            <td><?php echo $item['excerpt_length'] > 0 ? '✅' : '❌'; ?></td>
                            <td><?php echo ucfirst($item['post_status']); ?></td>
                            <td>
                                <a href="?analyze=<?php echo $item['ID']; ?>" class="btn">Analyze</a>
                                <a href="auto_improver.php?improve=<?php echo $item['ID']; ?>" class="btn" style="background: #28a745;">Auto-Improve</a>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
        
        <?php endif; ?>
    </div>
</body>
</html>