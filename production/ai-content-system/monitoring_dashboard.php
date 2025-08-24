<?php
/**
 * Monitoring Dashboard - PHP Implementation
 * Server health monitoring and analytics for conventum.kg
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

// System Monitoring Class
class SystemMonitor {
    private $pdo;
    
    public function __construct($pdo) {
        $this->pdo = $pdo;
    }
    
    public function getDatabaseStats() {
        $stats = [];
        
        // Get total posts
        $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM wp_posts WHERE post_status = 'publish'");
        $stats['published_posts'] = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
        
        // Get draft posts
        $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM wp_posts WHERE post_status = 'draft'");
        $stats['draft_posts'] = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
        
        // Get total users
        $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM wp_users");
        $stats['total_users'] = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
        
        // Get total comments
        $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM wp_comments WHERE comment_approved = '1'");
        $stats['approved_comments'] = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
        
        // Get media files
        $stmt = $this->pdo->query("SELECT COUNT(*) as count FROM wp_posts WHERE post_type = 'attachment'");
        $stats['media_files'] = $stmt->fetch(PDO::FETCH_ASSOC)['count'];
        
        // Get database size (approximate)
        $stmt = $this->pdo->query("
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS size_mb 
            FROM information_schema.tables 
            WHERE table_schema = '" . DB_NAME . "'
        ");
        $stats['database_size_mb'] = $stmt->fetch(PDO::FETCH_ASSOC)['size_mb'];
        
        return $stats;
    }
    
    public function getRecentActivity() {
        $activity = [];
        
        // Recent posts
        $stmt = $this->pdo->query("
            SELECT post_title, post_date, post_status, post_type 
            FROM wp_posts 
            WHERE post_type IN ('post', 'page') 
            ORDER BY post_modified DESC 
            LIMIT 10
        ");
        $activity['recent_posts'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Recent comments
        $stmt = $this->pdo->query("
            SELECT comment_author, comment_content, comment_date, comment_approved
            FROM wp_comments 
            ORDER BY comment_date DESC 
            LIMIT 5
        ");
        $activity['recent_comments'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        return $activity;
    }
    
    public function getContentMetrics() {
        $metrics = [];
        
        // Content by type
        $stmt = $this->pdo->query("
            SELECT post_type, COUNT(*) as count 
            FROM wp_posts 
            WHERE post_status = 'publish' 
            GROUP BY post_type
        ");
        $metrics['content_by_type'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Posts by month (last 6 months)
        $stmt = $this->pdo->query("
            SELECT 
                DATE_FORMAT(post_date, '%Y-%m') as month,
                COUNT(*) as count
            FROM wp_posts 
            WHERE post_status = 'publish' 
                AND post_type = 'post'
                AND post_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(post_date, '%Y-%m')
            ORDER BY month DESC
        ");
        $metrics['posts_by_month'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Average content length
        $stmt = $this->pdo->query("
            SELECT AVG(CHAR_LENGTH(post_content)) as avg_length
            FROM wp_posts 
            WHERE post_status = 'publish' AND post_type = 'post'
        ");
        $metrics['avg_content_length'] = round($stmt->fetch(PDO::FETCH_ASSOC)['avg_length']);
        
        return $metrics;
    }
    
    public function getSystemHealth() {
        $health = [
            'database_connection' => true,
            'last_backup' => 'N/A', // Would need backup plugin data
            'wordpress_version' => $this->getWordPressVersion(),
            'php_version' => phpversion(),
            'memory_usage' => $this->getMemoryUsage(),
            'disk_usage' => 'N/A', // Limited on shared hosting
            'uptime' => $this->estimateUptime()
        ];
        
        return $health;
    }
    
    private function getWordPressVersion() {
        $stmt = $this->pdo->query("SELECT option_value FROM wp_options WHERE option_name = 'db_version'");
        $db_version = $stmt->fetch(PDO::FETCH_ASSOC)['option_value'] ?? 'Unknown';
        return "DB: {$db_version}";
    }
    
    private function getMemoryUsage() {
        $memory = memory_get_usage(true);
        $peak = memory_get_peak_usage(true);
        return [
            'current' => $this->formatBytes($memory),
            'peak' => $this->formatBytes($peak),
            'percentage' => round(($memory / (1024 * 1024 * 128)) * 100, 1) // Assume 128MB limit
        ];
    }
    
    private function formatBytes($bytes, $precision = 2) {
        $units = array('B', 'KB', 'MB', 'GB');
        
        for ($i = 0; $bytes > 1024 && $i < count($units) - 1; $i++) {
            $bytes /= 1024;
        }
        
        return round($bytes, $precision) . ' ' . $units[$i];
    }
    
    private function estimateUptime() {
        // Estimate based on recent activity
        $stmt = $this->pdo->query("SELECT MAX(post_modified) as last_activity FROM wp_posts");
        $last_activity = $stmt->fetch(PDO::FETCH_ASSOC)['last_activity'];
        
        if ($last_activity) {
            $diff = time() - strtotime($last_activity);
            $days = floor($diff / 86400);
            return "{$days} days (estimated)";
        }
        
        return "Unknown";
    }
}

// Handle AJAX requests
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    header('Content-Type: application/json');
    
    $monitor = new SystemMonitor($pdo);
    
    switch ($_POST['action']) {
        case 'get_stats':
            echo json_encode($monitor->getDatabaseStats());
            break;
        case 'get_activity':
            echo json_encode($monitor->getRecentActivity());
            break;
        case 'get_metrics':
            echo json_encode($monitor->getContentMetrics());
            break;
        case 'get_health':
            echo json_encode($monitor->getSystemHealth());
            break;
    }
    exit;
}

$monitor = new SystemMonitor($pdo);
$stats = $monitor->getDatabaseStats();
$health = $monitor->getSystemHealth();
$metrics = $monitor->getContentMetrics();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoring Dashboard - conventum.kg</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            margin-bottom: 20px;
            text-align: center;
            padding: 20px;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .metric-label {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-healthy {
            background-color: #28a745;
        }
        
        .status-warning {
            background-color: #ffc107;
        }
        
        .status-error {
            background-color: #dc3545;
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
        
        .activity-item {
            border-left: 3px solid #007bff;
            padding-left: 15px;
            margin-bottom: 15px;
        }
        
        .chart-container {
            height: 300px;
            margin: 20px 0;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(45deg, #007bff, #0056b3);
            border: none;
            color: white;
            font-size: 1.2rem;
            box-shadow: 0 10px 30px rgba(0,123,255,0.3);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 15px 40px rgba(0,123,255,0.4);
        }
    </style>
</head>
<body>
    <div class="container main-container">
        <!-- Navigation -->
        <div class="text-center nav-links">
            <a href="analyzer.php"><i class="fas fa-chart-line"></i> Content Analyzer</a>
            <a href="mcp_inspector.php"><i class="fas fa-search"></i> MCP Inspector</a>
            <a href="monitoring_dashboard.php" class="active"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
            <a href="auto_improver.php"><i class="fas fa-magic"></i> Auto Improver</a>
        </div>
        
        <!-- Header -->
        <div class="card">
            <div class="card-body text-center">
                <h1 class="display-6 mb-3">
                    <i class="fas fa-tachometer-alt text-primary"></i>
                    System Dashboard
                </h1>
                <p class="text-muted mb-0">Real-time monitoring and analytics for conventum.kg</p>
            </div>
        </div>
        
        <!-- Key Metrics -->
        <div class="row">
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value text-primary"><?= number_format($stats['published_posts']) ?></div>
                    <div class="metric-label">Published Posts</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value text-success"><?= number_format($stats['total_users']) ?></div>
                    <div class="metric-label">Total Users</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value text-info"><?= number_format($stats['media_files']) ?></div>
                    <div class="metric-label">Media Files</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card">
                    <div class="metric-value text-warning"><?= $stats['database_size_mb'] ?>MB</div>
                    <div class="metric-label">Database Size</div>
                </div>
            </div>
        </div>
        
        <!-- Charts Row -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Content Distribution</h5>
                        <div class="chart-container">
                            <canvas id="contentChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Publishing Activity</h5>
                        <div class="chart-container">
                            <canvas id="activityChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Health & Activity -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">System Health</h5>
                        <div class="mb-3">
                            <span class="status-indicator status-healthy"></span>
                            Database Connection: Connected
                        </div>
                        <div class="mb-3">
                            <span class="status-indicator status-healthy"></span>
                            WordPress Version: <?= htmlspecialchars($health['wordpress_version']) ?>
                        </div>
                        <div class="mb-3">
                            <span class="status-indicator status-healthy"></span>
                            PHP Version: <?= htmlspecialchars($health['php_version']) ?>
                        </div>
                        <div class="mb-3">
                            <span class="status-indicator status-<?= $health['memory_usage']['percentage'] > 80 ? 'warning' : 'healthy' ?>"></span>
                            Memory Usage: <?= $health['memory_usage']['current'] ?> (<?= $health['memory_usage']['percentage'] ?>%)
                        </div>
                        <div class="mb-3">
                            <span class="status-indicator status-healthy"></span>
                            Estimated Uptime: <?= htmlspecialchars($health['uptime']) ?>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Recent Activity</h5>
                        <div id="activity-feed">
                            <?php 
                            $activity = $monitor->getRecentActivity();
                            foreach (array_slice($activity['recent_posts'], 0, 5) as $post): 
                            ?>
                                <div class="activity-item">
                                    <strong><?= htmlspecialchars($post['post_title']) ?></strong>
                                    <br>
                                    <small class="text-muted">
                                        <?= ucfirst($post['post_type']) ?> • <?= date('M j, Y', strtotime($post['post_date'])) ?>
                                        <span class="badge badge-sm bg-<?= $post['post_status'] === 'publish' ? 'success' : 'warning' ?> ms-2">
                                            <?= ucfirst($post['post_status']) ?>
                                        </span>
                                    </small>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Quick Stats -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Quick Statistics</h5>
                        <div class="row">
                            <div class="col-md-3 text-center">
                                <h4 class="text-primary"><?= $stats['approved_comments'] ?></h4>
                                <small>Approved Comments</small>
                            </div>
                            <div class="col-md-3 text-center">
                                <h4 class="text-warning"><?= $stats['draft_posts'] ?></h4>
                                <small>Draft Posts</small>
                            </div>
                            <div class="col-md-3 text-center">
                                <h4 class="text-info"><?= number_format($metrics['avg_content_length']) ?></h4>
                                <small>Avg. Content Length</small>
                            </div>
                            <div class="col-md-3 text-center">
                                <h4 class="text-success"><?= count($metrics['posts_by_month']) ?></h4>
                                <small>Active Months</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Refresh Button -->
    <button class="refresh-btn" onclick="refreshDashboard()" title="Refresh Dashboard">
        <i class="fas fa-sync-alt" id="refresh-icon"></i>
    </button>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Content Distribution Chart
        const contentCtx = document.getElementById('contentChart').getContext('2d');
        const contentChart = new Chart(contentCtx, {
            type: 'doughnut',
            data: {
                labels: ['Posts', 'Pages', 'Media', 'Other'],
                datasets: [{
                    data: [<?= $stats['published_posts'] ?>, <?= $stats['draft_posts'] ?>, <?= $stats['media_files'] ?>, 10],
                    backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Activity Chart
        const activityCtx = document.getElementById('activityChart').getContext('2d');
        const activityChart = new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: <?= json_encode(array_column(array_reverse($metrics['posts_by_month']), 'month')) ?>,
                datasets: [{
                    label: 'Posts Published',
                    data: <?= json_encode(array_column(array_reverse($metrics['posts_by_month']), 'count')) ?>,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
        
        function refreshDashboard() {
            const icon = document.getElementById('refresh-icon');
            icon.classList.add('fa-spin');
            
            // Simulate refresh (in real implementation, you'd fetch new data)
            setTimeout(() => {
                icon.classList.remove('fa-spin');
                location.reload();
            }, 1000);
        }
    </script>
</body>
</html>