"""
Performance Monitoring Service - Phase 4 Enhancement
Comprehensive system monitoring and benchmarking capabilities

Tracks performance metrics, system health, and provides
insights for optimization and troubleshooting.
"""

import os
import json
import time
import sqlite3
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import uuid

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance measurement"""
    metric_type: str    # 'analysis_time', 'memory_usage', 'api_latency', etc.
    metric_name: str    # Specific metric name
    value: float        # Measured value
    unit: str          # Unit of measurement
    component: str     # Component that generated this metric
    context: Dict = None  # Additional context data
    session_id: str = None
    recorded_at: datetime = None

    def __post_init__(self):
        if self.recorded_at is None:
            self.recorded_at = datetime.now()
        if self.context is None:
            self.context = {}

@dataclass
class SystemHealth:
    """Overall system health snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    redis_available: bool
    database_responsive: bool
    ai_service_available: bool
    url_service_available: bool
    active_processes: int
    uptime_seconds: float

class PerformanceMonitor:
    """
    Comprehensive performance monitoring service
    Tracks metrics, system health, and provides benchmarking capabilities
    """
    
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'data/phishing_analyzer.db')
        self.session_id = str(uuid.uuid4())[:8]  # Short session identifier
        self.start_time = time.time()
        
        # Metric collection settings
        self.auto_collect_interval = int(os.getenv('MONITORING_INTERVAL_SECONDS', '60'))
        self.max_metrics_age_days = int(os.getenv('METRICS_RETENTION_DAYS', '30'))
        
        # Performance thresholds
        self.thresholds = {
            'rule_analysis_ms': 1000,      # Rule analysis should be < 1s
            'ai_analysis_ms': 5000,        # AI analysis should be < 5s
            'memory_percent': 80,          # Memory usage warning at 80%
            'cpu_percent': 70,             # CPU usage warning at 70%
            'disk_percent': 90,            # Disk usage warning at 90%
            'cache_hit_rate': 0.7,         # Cache hit rate should be > 70%
            'api_error_rate': 0.05         # API error rate should be < 5%
        }
        
        # Background monitoring thread
        self._monitoring_thread = None
        self._monitoring_active = False
        
        logger.info(f"PerformanceMonitor initialized with session: {self.session_id}")

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def record_metric(self, 
                     metric_type: str, 
                     metric_name: str, 
                     value: float, 
                     unit: str,
                     component: str,
                     context: Optional[Dict] = None) -> bool:
        """
        Record a performance metric
        
        Args:
            metric_type: Category of metric (e.g., 'analysis_time', 'memory_usage')
            metric_name: Specific metric name
            value: Measured value
            unit: Unit of measurement
            component: Component that generated this metric
            context: Additional context data
            
        Returns:
            True if recorded successfully
        """
        try:
            metric = PerformanceMetric(
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                unit=unit,
                component=component,
                context=context or {},
                session_id=self.session_id
            )
            
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO performance_metrics 
                    (metric_type, metric_name, value, unit, component, context, 
                     recorded_at, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.metric_type, metric.metric_name, metric.value,
                    metric.unit, metric.component, json.dumps(metric.context),
                    metric.recorded_at.isoformat(), metric.session_id
                ))
                conn.commit()
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {e}")
            return False

    @contextmanager
    def measure_time(self, metric_name: str, component: str, context: Optional[Dict] = None):
        """
        Context manager to measure execution time
        
        Usage:
            with monitor.measure_time('email_parsing', 'parser'):
                parse_email(content)
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_metric(
                'execution_time', 
                metric_name, 
                duration_ms, 
                'milliseconds',
                component,
                context
            )

    def measure_function(self, metric_name: str, component: str):
        """
        Decorator to measure function execution time
        
        Usage:
            @monitor.measure_function('email_analysis', 'analyzer')
            def analyze_email(email):
                # function code
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                with self.measure_time(metric_name, component, {'function': func.__name__}):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def collect_system_metrics(self) -> SystemHealth:
        """
        Collect current system performance metrics
        """
        try:
            # Basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check service availability
            redis_available = self._check_redis_health()
            database_responsive = self._check_database_health()
            ai_service_available = self._check_ai_service_health()
            url_service_available = self._check_url_service_health()
            
            # Process information
            active_processes = len(psutil.pids())
            uptime_seconds = time.time() - self.start_time
            
            health = SystemHealth(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                redis_available=redis_available,
                database_responsive=database_responsive,
                ai_service_available=ai_service_available,
                url_service_available=url_service_available,
                active_processes=active_processes,
                uptime_seconds=uptime_seconds
            )
            
            # Record individual metrics
            self.record_metric('system', 'cpu_percent', cpu_percent, 'percent', 'monitor')
            self.record_metric('system', 'memory_percent', memory.percent, 'percent', 'monitor')
            self.record_metric('system', 'disk_percent', disk.percent, 'percent', 'monitor')
            self.record_metric('system', 'uptime_seconds', uptime_seconds, 'seconds', 'monitor')
            
            return health
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return minimal health data
            return SystemHealth(
                timestamp=datetime.now(),
                cpu_percent=0,
                memory_percent=0,
                disk_percent=0,
                redis_available=False,
                database_responsive=False,
                ai_service_available=False,
                url_service_available=False,
                active_processes=0,
                uptime_seconds=time.time() - self.start_time
            )

    def _check_redis_health(self) -> bool:
        """Check if Redis is available and responsive"""
        try:
            from services.cache_manager import get_cache_manager
            cache = get_cache_manager()
            health = cache.health_check()
            return health.get('status') in ['healthy', 'degraded']
        except Exception:
            return False

    def _check_database_health(self) -> bool:
        """Check if database is responsive"""
        try:
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
            finally:
                conn.close()
        except Exception:
            return False

    def _check_ai_service_health(self) -> bool:
        """Check if AI service is available"""
        try:
            from services.ai import get_ai_analyzer
            analyzer = get_ai_analyzer()
            # Simple test - just check if we can create the analyzer
            return analyzer is not None
        except Exception:
            return False

    def _check_url_service_health(self) -> bool:
        """Check if URL reputation service is available"""
        try:
            from services.url_reputation import get_url_reputation_service
            service = get_url_reputation_service()
            return service is not None
        except Exception:
            return False

    def get_performance_summary(self, hours: int = 24) -> Dict:
        """
        Get performance summary for the last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict with performance statistics
        """
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                
                # Get metrics from the specified time period
                cursor.execute("""
                    SELECT metric_type, metric_name, value, unit, component, recorded_at
                    FROM performance_metrics
                    WHERE recorded_at >= ?
                    ORDER BY recorded_at DESC
                """, (since_time.isoformat(),))
                
                metrics = cursor.fetchall()
                
                if not metrics:
                    return {'message': f'No metrics found for the last {hours} hours'}
                
                # Group metrics by type and calculate statistics
                grouped_metrics = {}
                for metric in metrics:
                    key = f"{metric['metric_type']}.{metric['metric_name']}"
                    if key not in grouped_metrics:
                        grouped_metrics[key] = []
                    grouped_metrics[key].append(metric['value'])
                
                summary = {
                    'time_period_hours': hours,
                    'total_measurements': len(metrics),
                    'metrics_summary': {}
                }
                
                for key, values in grouped_metrics.items():
                    if values:
                        summary['metrics_summary'][key] = {
                            'count': len(values),
                            'average': round(sum(values) / len(values), 3),
                            'min': min(values),
                            'max': max(values),
                            'latest': values[0] if values else None
                        }
                
                # Check against thresholds
                alerts = []
                latest_metrics = self.get_latest_metrics()
                
                for threshold_key, threshold_value in self.thresholds.items():
                    for metric_key, stats in summary['metrics_summary'].items():
                        if threshold_key in metric_key:
                            latest_value = stats['latest']
                            if latest_value is not None:
                                if 'percent' in threshold_key or 'rate' in threshold_key:
                                    if latest_value > threshold_value:
                                        alerts.append(f"{metric_key}: {latest_value} exceeds threshold {threshold_value}")
                                else:
                                    if latest_value > threshold_value:
                                        alerts.append(f"{metric_key}: {latest_value} exceeds threshold {threshold_value}")
                
                summary['alerts'] = alerts
                summary['health_status'] = 'healthy' if not alerts else 'warning'
                
                return summary
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}

    def get_latest_metrics(self) -> Dict:
        """Get the most recent metrics for each type"""
        try:
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                
                # Get latest metric for each type/name combination
                cursor.execute("""
                    SELECT metric_type, metric_name, value, unit, component, 
                           recorded_at, context
                    FROM performance_metrics pm1
                    WHERE recorded_at = (
                        SELECT MAX(recorded_at)
                        FROM performance_metrics pm2
                        WHERE pm2.metric_type = pm1.metric_type 
                        AND pm2.metric_name = pm1.metric_name
                    )
                    ORDER BY recorded_at DESC
                """)
                
                metrics = cursor.fetchall()
                
                result = {}
                for metric in metrics:
                    key = f"{metric['metric_type']}.{metric['metric_name']}"
                    result[key] = {
                        'value': metric['value'],
                        'unit': metric['unit'],
                        'component': metric['component'],
                        'recorded_at': metric['recorded_at'],
                        'context': json.loads(metric['context']) if metric['context'] else {}
                    }
                
                return result
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to get latest metrics: {e}")
            return {}

    def start_background_monitoring(self):
        """Start background thread for automatic metric collection"""
        if self._monitoring_active:
            logger.warning("Background monitoring already active")
            return
            
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._background_monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Started background monitoring")

    def stop_background_monitoring(self):
        """Stop background monitoring"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Stopped background monitoring")

    def _background_monitoring_loop(self):
        """Background thread loop for collecting metrics"""
        while self._monitoring_active:
            try:
                self.collect_system_metrics()
                time.sleep(self.auto_collect_interval)
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(self.auto_collect_interval)

    def cleanup_old_metrics(self) -> int:
        """
        Clean up old performance metrics to prevent database bloat
        
        Returns:
            Number of metrics deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_metrics_age_days)
            
            conn = self._get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM performance_metrics
                    WHERE recorded_at < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old performance metrics")
                return deleted_count
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0

    def generate_benchmark_report(self) -> Dict:
        """
        Generate comprehensive benchmark report
        Useful for performance analysis and optimization
        """
        try:
            system_health = self.collect_system_metrics()
            performance_summary = self.get_performance_summary(hours=24)
            latest_metrics = self.get_latest_metrics()
            
            # Calculate some derived metrics
            analysis_metrics = {
                k: v for k, v in latest_metrics.items() 
                if 'analysis' in k or 'processing' in k
            }
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'system_health': asdict(system_health),
                'performance_summary_24h': performance_summary,
                'latest_metrics': latest_metrics,
                'analysis_performance': analysis_metrics,
                'recommendations': self._generate_performance_recommendations(
                    system_health, performance_summary
                )
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate benchmark report: {e}")
            return {'error': str(e)}

    def _generate_performance_recommendations(self, 
                                           health: SystemHealth, 
                                           summary: Dict) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Memory recommendations
        if health.memory_percent > 80:
            recommendations.append(
                "High memory usage detected. Consider implementing more aggressive caching cleanup."
            )
        
        # CPU recommendations
        if health.cpu_percent > 70:
            recommendations.append(
                "High CPU usage. Consider scaling workers or optimizing analysis algorithms."
            )
        
        # Service availability
        if not health.redis_available:
            recommendations.append(
                "Redis unavailable. Performance will be degraded without caching."
            )
        
        # Analysis performance
        analysis_metrics = summary.get('metrics_summary', {})
        for metric_key, stats in analysis_metrics.items():
            if 'analysis' in metric_key and stats.get('average', 0) > 2000:  # > 2s average
                recommendations.append(
                    f"Slow {metric_key} detected (avg: {stats['average']}ms). Consider optimization."
                )
        
        if not recommendations:
            recommendations.append("System performance looks good!")
        
        return recommendations


# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def reset_performance_monitor():
    """Reset global performance monitor (mainly for testing)"""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.stop_background_monitoring()
    _performance_monitor = None