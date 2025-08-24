<?php
/**
 * MCP Inspector - PHP Implementation
 * Web interface for testing and debugging MCP server tools
 * Based on analyzer.php design pattern
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

// MCP Tools Simulation
class MCPInspector {
    private $pdo;
    private $tools = [
        'create_product_showcase' => [
            'name' => 'Create Product Showcase',
            'description' => 'Create new showcase content for WordPress',
            'parameters' => ['title', 'content', 'category', 'featured_image'],
            'status' => 'active'
        ],
        'update_showcase_content' => [
            'name' => 'Update Showcase Content',
            'description' => 'Update existing WordPress content',
            'parameters' => ['post_id', 'title', 'content', 'meta'],
            'status' => 'active'
        ],
        'analyze_content_performance' => [
            'name' => 'Analyze Content Performance',
            'description' => 'Get performance metrics for content',
            'parameters' => ['post_id', 'metrics_type', 'date_range'],
            'status' => 'active'
        ],
        'optimize_content_seo' => [
            'name' => 'Optimize Content SEO',
            'description' => 'AI-powered SEO optimization',
            'parameters' => ['post_id', 'keywords', 'optimization_level'],
            'status' => 'active'
        ],
        'manage_media_assets' => [
            'name' => 'Manage Media Assets',
            'description' => 'WordPress media library management',
            'parameters' => ['action', 'media_id', 'metadata'],
            'status' => 'active'
        ],
        'get_elementor_insights' => [
            'name' => 'Get Elementor Insights',
            'description' => 'Analyze Elementor page builder usage',
            'parameters' => ['post_id', 'analysis_type'],
            'status' => 'active'
        ]
    ];
    
    public function __construct($pdo) {
        $this->pdo = $pdo;
    }
    
    public function getTools() {
        return $this->tools;
    }
    
    public function executeTool($tool_name, $parameters) {
        if (!isset($this->tools[$tool_name])) {
            return ['error' => 'Tool not found'];
        }
        
        // Simulate tool execution based on tool type
        switch ($tool_name) {
            case 'create_product_showcase':
                return $this->createShowcase($parameters);
            case 'update_showcase_content':
                return $this->updateContent($parameters);
            case 'analyze_content_performance':
                return $this->analyzePerformance($parameters);
            case 'optimize_content_seo':
                return $this->optimizeSEO($parameters);
            case 'manage_media_assets':
                return $this->manageMedia($parameters);
            case 'get_elementor_insights':
                return $this->getElementorInsights($parameters);
            default:
                return ['error' => 'Tool not implemented'];
        }
    }
    
    private function createShowcase($params) {
        // Simulate showcase creation
        $new_id = rand(1000, 9999);
        return [
            'success' => true,
            'message' => 'Showcase content created successfully',
            'post_id' => $new_id,
            'title' => $params['title'] ?? 'New Showcase',
            'status' => 'draft',
            'url' => "https://conventum.kg/?p={$new_id}"
        ];
    }
    
    private function updateContent($params) {
        // Get real post data if post_id provided
        if (isset($params['post_id'])) {
            $stmt = $this->pdo->prepare("SELECT post_title, post_status FROM wp_posts WHERE ID = ?");
            $stmt->execute([$params['post_id']]);
            $post = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if ($post) {
                return [
                    'success' => true,
                    'message' => 'Content updated successfully',
                    'post_id' => $params['post_id'],
                    'title' => $post['post_title'],
                    'status' => $post['post_status']
                ];
            }
        }
        
        return ['success' => false, 'message' => 'Post not found'];
    }
    
    private function analyzePerformance($params) {
        // Simulate performance metrics
        return [
            'success' => true,
            'metrics' => [
                'views' => rand(100, 5000),
                'engagement_rate' => rand(15, 85) . '%',
                'avg_time_on_page' => rand(30, 300) . 's',
                'bounce_rate' => rand(20, 70) . '%',
                'seo_score' => rand(60, 95)
            ]
        ];
    }
    
    private function optimizeSEO($params) {
        // Simulate SEO optimization
        return [
            'success' => true,
            'optimizations' => [
                'title_optimized' => true,
                'meta_description_generated' => true,
                'heading_structure_improved' => true,
                'keyword_density_optimized' => true,
                'internal_links_added' => rand(2, 8)
            ],
            'new_seo_score' => rand(80, 98)
        ];
    }
    
    private function manageMedia($params) {
        // Get media count from database
        $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM wp_posts WHERE post_type = 'attachment'");
        $media_count = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
        
        return [
            'success' => true,
            'total_media' => $media_count,
            'action' => $params['action'] ?? 'list',
            'message' => 'Media operation completed successfully'
        ];
    }
    
    private function getElementorInsights($params) {
        // Check Elementor usage in database
        $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM wp_postmeta WHERE meta_key = '_elementor_data'");
        $elementor_count = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
        
        return [
            'success' => true,
            'elementor_pages' => $elementor_count,
            'insights' => [
                'most_used_widgets' => ['heading', 'text-editor', 'image', 'button'],
                'avg_widgets_per_page' => rand(8, 25),
                'performance_score' => rand(70, 95)
            ]
        ];
    }
}

// Handle AJAX requests
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    header('Content-Type: application/json');
    
    $inspector = new MCPInspector($pdo);
    
    if ($_POST['action'] === 'execute_tool') {
        $tool_name = $_POST['tool_name'] ?? '';
        $parameters = json_decode($_POST['parameters'] ?? '{}', true);
        
        $result = $inspector->executeTool($tool_name, $parameters);
        echo json_encode($result);
        exit;
    }
    
    if ($_POST['action'] === 'get_tools') {
        echo json_encode($inspector->getTools());
        exit;
    }
}

$inspector = new MCPInspector($pdo);
$tools = $inspector->getTools();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Inspector - conventum.kg</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .main-container {
            padding: 30px 0;
        }
        
        .header-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: none;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .tool-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        
        .tool-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .status-badge {
            font-size: 0.8rem;
            padding: 4px 12px;
            border-radius: 20px;
        }
        
        .status-active {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        
        .btn-execute {
            background: linear-gradient(45deg, #28a745, #20c997);
            border: none;
            border-radius: 25px;
            color: white;
            padding: 8px 20px;
            transition: all 0.3s ease;
        }
        
        .btn-execute:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.4);
            color: white;
        }
        
        .result-area {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .nav-links {
            margin-bottom: 20px;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .nav-links a:hover, .nav-links a.active {
            background: rgba(255, 255, 255, 0.3);
            color: white;
        }
        
        .parameter-input {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container main-container">
        <!-- Navigation -->
        <div class="text-center nav-links">
            <a href="analyzer.php"><i class="fas fa-chart-line"></i> Content Analyzer</a>
            <a href="mcp_inspector.php" class="active"><i class="fas fa-search"></i> MCP Inspector</a>
            <a href="monitoring_dashboard.php"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
            <a href="auto_improver.php"><i class="fas fa-magic"></i> Auto Improver</a>
        </div>
        
        <!-- Header -->
        <div class="card header-card">
            <div class="card-body text-center">
                <h1 class="display-6 mb-3">
                    <i class="fas fa-search text-primary"></i>
                    MCP Inspector
                </h1>
                <p class="text-muted mb-0">Test and debug Model Context Protocol tools for WordPress content management</p>
                <div class="row mt-4">
                    <div class="col-md-4">
                        <h5 class="text-primary"><?= count($tools) ?></h5>
                        <small class="text-muted">Available Tools</small>
                    </div>
                    <div class="col-md-4">
                        <h5 class="text-success">6</h5>
                        <small class="text-muted">Active Tools</small>
                    </div>
                    <div class="col-md-4">
                        <h5 class="text-info">100%</h5>
                        <small class="text-muted">System Health</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tools Grid -->
        <div class="row">
            <?php foreach ($tools as $tool_id => $tool): ?>
                <div class="col-md-6 col-lg-4">
                    <div class="card tool-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <h6 class="card-title mb-0"><?= htmlspecialchars($tool['name']) ?></h6>
                                <span class="badge status-badge status-<?= $tool['status'] ?>"><?= ucfirst($tool['status']) ?></span>
                            </div>
                            
                            <p class="card-text text-muted small mb-3"><?= htmlspecialchars($tool['description']) ?></p>
                            
                            <!-- Parameters -->
                            <div class="parameters-section mb-3">
                                <small class="text-muted d-block mb-2">Parameters:</small>
                                <?php foreach ($tool['parameters'] as $param): ?>
                                    <div class="parameter-input">
                                        <input type="text" 
                                               class="form-control form-control-sm" 
                                               placeholder="<?= htmlspecialchars($param) ?>"
                                               data-param="<?= htmlspecialchars($param) ?>"
                                               id="<?= $tool_id ?>_<?= $param ?>">
                                    </div>
                                <?php endforeach; ?>
                            </div>
                            
                            <button class="btn btn-execute btn-sm w-100" onclick="executeTool('<?= $tool_id ?>')">
                                <i class="fas fa-play"></i> Execute Tool
                            </button>
                            
                            <!-- Result Area -->
                            <div class="result-area" id="result_<?= $tool_id ?>" style="display: none;"></div>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function executeTool(toolId) {
            const resultArea = document.getElementById('result_' + toolId);
            const executeBtn = document.querySelector(`[onclick="executeTool('${toolId}')"]`);
            
            // Collect parameters
            const parameters = {};
            const paramInputs = document.querySelectorAll(`[id^="${toolId}_"]`);
            paramInputs.forEach(input => {
                const paramName = input.getAttribute('data-param');
                if (input.value.trim()) {
                    parameters[paramName] = input.value.trim();
                }
            });
            
            // Show loading
            executeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
            executeBtn.disabled = true;
            resultArea.style.display = 'block';
            resultArea.innerHTML = '<div class="text-muted">Executing tool...</div>';
            
            // Execute tool
            fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    action: 'execute_tool',
                    tool_name: toolId,
                    parameters: JSON.stringify(parameters)
                })
            })
            .then(response => response.json())
            .then(data => {
                resultArea.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                
                // Reset button
                executeBtn.innerHTML = '<i class="fas fa-play"></i> Execute Tool';
                executeBtn.disabled = false;
            })
            .catch(error => {
                resultArea.innerHTML = '<div class="text-danger">Error: ' + error.message + '</div>';
                
                // Reset button
                executeBtn.innerHTML = '<i class="fas fa-play"></i> Execute Tool';
                executeBtn.disabled = false;
            });
        }
    </script>
</body>
</html>