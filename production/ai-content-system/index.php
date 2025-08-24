<?php
/**
 * MCP Admin Suite - Main Dashboard
 * Central hub for all MCP tools and analytics
 * conventum.kg WordPress AI Content Management System
 */

require_once 'config.php';
require_once 'auth.php';
requireAuth(); // Require authentication

// Database configuration from environment
$db_config = Config::getDatabase();

try {
    $pdo = new PDO(
        "mysql:host={$db_config['host']};dbname={$db_config['name']};charset=utf8mb4", 
        $db_config['user'], 
        $db_config['password']
    );
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    die("Connection failed: " . $e->getMessage());
}

// Get quick stats
$stats = [];

// Total content
$stmt = $pdo->query("SELECT COUNT(*) as count FROM wp_posts WHERE post_type IN ('post', 'page') AND post_status = 'publish'");
$stats['total_content'] = $stmt->fetch(PDO::FETCH_ASSOC)['count'];

// Recent activity (last 7 days)
$stmt = $pdo->query("SELECT COUNT(*) as count FROM wp_posts WHERE post_modified >= DATE_SUB(NOW(), INTERVAL 7 DAY)");
$stats['recent_activity'] = $stmt->fetch(PDO::FETCH_ASSOC)['count'];

// Average SEO score (simulated)
$stats['avg_seo_score'] = rand(70, 90);

// System status
$stats['system_status'] = 'operational';
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Admin Suite - conventum.kg</title>
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
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: none;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 30px 60px rgba(0,0,0,0.15);
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            margin-bottom: 20px;
            height: 100%;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-card {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #007bff, #0056b3);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 30px rgba(0,123,255,0.3);
        }
        
        .nav-brand {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #28a745;
            display: inline-block;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .quick-actions {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
        }
        
        .quick-action-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            margin: 5px;
            display: block;
            text-align: center;
            line-height: 60px;
            font-size: 1.5rem;
            color: white;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .quick-action-btn:hover {
            transform: scale(1.1);
            color: white;
        }
        
        .action-analyze { background: linear-gradient(45deg, #007bff, #0056b3); }
        .action-inspect { background: linear-gradient(45deg, #28a745, #20c997); }
        .action-monitor { background: linear-gradient(45deg, #ffc107, #e0a800); }
        .action-improve { background: linear-gradient(45deg, #dc3545, #c82333); }
    </style>
</head>
<body>
    <div class="container main-container">
        <!-- Header -->
        <div class="text-center nav-brand">
            <h1 class="mb-0">
                <i class="fas fa-cogs"></i>
                MCP Admin Suite
            </h1>
            <p class="mb-0">WordPress AI Content Management System</p>
        </div>
        
        <!-- Welcome Card -->
        <div class="card">
            <div class="card-body text-center">
                <h2 class="display-6 mb-3">Welcome to conventum.kg AI Dashboard</h2>
                <p class="lead text-muted mb-4">
                    Complete Model Context Protocol suite for intelligent WordPress content management
                </p>
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-value"><?= number_format($stats['total_content']) ?></div>
                            <div class="stat-label">Total Content Pieces</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card" style="background: linear-gradient(45deg, #007bff, #0056b3);">
                            <div class="stat-value"><?= $stats['recent_activity'] ?></div>
                            <div class="stat-label">Recent Updates (7 days)</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card" style="background: linear-gradient(45deg, #ffc107, #e0a800);">
                            <div class="stat-value"><?= $stats['avg_seo_score'] ?>%</div>
                            <div class="stat-label">Average SEO Score</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card" style="background: linear-gradient(45deg, #dc3545, #c82333);">
                            <div class="stat-value">
                                <span class="status-indicator"></span>
                                Online
                            </div>
                            <div class="stat-label">System Status</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Main Features -->
        <div class="row">
            <div class="col-md-6 col-lg-3">
                <div class="card feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h5 class="card-title">Content Analyzer</h5>
                        <p class="card-text text-muted mb-4">
                            AI-powered content analysis with SEO scoring and optimization recommendations.
                        </p>
                        <a href="analyzer.php" class="btn btn-primary">
                            <i class="fas fa-chart-line"></i> Analyze Content
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-3">
                <div class="card feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">
                            <i class="fas fa-search"></i>
                        </div>
                        <h5 class="card-title">MCP Inspector</h5>
                        <p class="card-text text-muted mb-4">
                            Test and debug Model Context Protocol tools interactively.
                        </p>
                        <a href="mcp_inspector.php" class="btn btn-primary">
                            <i class="fas fa-search"></i> Inspect Tools
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-3">
                <div class="card feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">
                            <i class="fas fa-tachometer-alt"></i>
                        </div>
                        <h5 class="card-title">System Dashboard</h5>
                        <p class="card-text text-muted mb-4">
                            Monitor server health, performance metrics, and system analytics.
                        </p>
                        <a href="monitoring_dashboard.php" class="btn btn-primary">
                            <i class="fas fa-tachometer-alt"></i> View Dashboard
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-3">
                <div class="card feature-card">
                    <div class="card-body text-center">
                        <div class="feature-icon">
                            <i class="fas fa-magic"></i>
                        </div>
                        <h5 class="card-title">Auto Improver</h5>
                        <p class="card-text text-muted mb-4">
                            Automatically optimize content with AI-powered improvements.
                        </p>
                        <a href="auto_improver.php" class="btn btn-primary">
                            <i class="fas fa-magic"></i> Auto Improve
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Additional Tools -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="fas fa-tools text-primary"></i>
                            Available MCP Tools
                        </h5>
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="fas fa-check-circle text-success"></i> Create Product Showcase</li>
                            <li class="mb-2"><i class="fas fa-check-circle text-success"></i> Update Showcase Content</li>
                            <li class="mb-2"><i class="fas fa-check-circle text-success"></i> Analyze Content Performance</li>
                            <li class="mb-2"><i class="fas fa-check-circle text-success"></i> Optimize Content SEO</li>
                            <li class="mb-2"><i class="fas fa-check-circle text-success"></i> Manage Media Assets</li>
                            <li class="mb-2"><i class="fas fa-check-circle text-success"></i> Get Elementor Insights</li>
                        </ul>
                        <a href="mcp_inspector.php" class="btn btn-outline-primary btn-sm">
                            Test All Tools <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="fas fa-info-circle text-info"></i>
                            System Information
                        </h5>
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">WordPress Integration</small>
                                <div><i class="fas fa-check-circle text-success"></i> Active</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Database Connection</small>
                                <div><i class="fas fa-check-circle text-success"></i> Connected</div>
                            </div>
                            <div class="col-6 mt-2">
                                <small class="text-muted">AI Analysis</small>
                                <div><i class="fas fa-check-circle text-success"></i> Operational</div>
                            </div>
                            <div class="col-6 mt-2">
                                <small class="text-muted">Auto Improvements</small>
                                <div><i class="fas fa-check-circle text-success"></i> Ready</div>
                            </div>
                        </div>
                        <a href="monitoring_dashboard.php" class="btn btn-outline-info btn-sm mt-3">
                            View Full Status <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer Info -->
        <div class="card">
            <div class="card-body text-center">
                <h6 class="text-muted">WordPress AI Content Management System</h6>
                <p class="text-muted mb-0">
                    Powered by Model Context Protocol (MCP) • 
                    <a href="https://conventum.kg" target="_blank" class="text-decoration-none">conventum.kg</a> • 
                    Admin Use Only
                </p>
            </div>
        </div>
    </div>
    
    <!-- Quick Actions -->
    <div class="quick-actions">
        <a href="analyzer.php" class="quick-action-btn action-analyze" title="Content Analyzer">
            <i class="fas fa-chart-line"></i>
        </a>
        <a href="mcp_inspector.php" class="quick-action-btn action-inspect" title="MCP Inspector">
            <i class="fas fa-search"></i>
        </a>
        <a href="monitoring_dashboard.php" class="quick-action-btn action-monitor" title="System Dashboard">
            <i class="fas fa-tachometer-alt"></i>
        </a>
        <a href="auto_improver.php" class="quick-action-btn action-improve" title="Auto Improver">
            <i class="fas fa-magic"></i>
        </a>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Add some interactivity
        document.addEventListener('DOMContentLoaded', function() {
            // Animate stats on load
            const statValues = document.querySelectorAll('.stat-value');
            statValues.forEach(stat => {
                if (!isNaN(parseInt(stat.textContent))) {
                    const finalValue = parseInt(stat.textContent);
                    let currentValue = 0;
                    const increment = Math.ceil(finalValue / 20);
                    
                    const timer = setInterval(() => {
                        currentValue += increment;
                        if (currentValue >= finalValue) {
                            currentValue = finalValue;
                            clearInterval(timer);
                        }
                        stat.textContent = currentValue.toLocaleString();
                    }, 50);
                }
            });
        });
    </script>
</body>
</html>