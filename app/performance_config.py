# 性能优化配置文件

class PerformanceConfig:
    """前端性能优化配置"""
    
    # 资源压缩设置
    COMPRESS_ENABLED = True
    COMPRESS_LEVEL = 6  # 压缩级别 1-9
    
    # 缓存设置
    CACHE_ENABLED = True
    CACHE_DEFAULT_TIMEOUT = 300  # 5分钟
    CACHE_KEY_PREFIX = 'order_system'
    
    # 静态文件设置
    STATIC_FOLDER = 'static'
    STATIC_URL_PATH = '/static'
    
    # 图片优化设置
    IMAGE_OPTIMIZATION = {
        'max_width': 1920,
        'max_height': 1080,
        'quality': 85,
        'formats': ['webp', 'jpg', 'png'],
        'lazy_loading': True
    }
    
    # JavaScript优化设置
    JS_OPTIMIZATION = {
        'minify': True,
        'bundle': True,
        'source_maps': False,
        'tree_shaking': True
    }
    
    # CSS优化设置
    CSS_OPTIMIZATION = {
        'minify': True,
        'purge_unused': True,
        'critical_css': True
    }
    
    # 预加载设置
    PRELOAD_RESOURCES = [
        '/static/css/performance.css',
        '/static/js/performance.js',
        '/static/js/main_optimized.js'
    ]
    
    # 关键资源
    CRITICAL_RESOURCES = [
        '/static/styles.css',
        '/static/js/main.js'
    ]
    
    # 性能监控设置
    PERFORMANCE_MONITORING = {
        'enabled': True,
        'metrics_endpoint': '/api/performance/metrics',
        'error_reporting': True,
        'real_user_monitoring': True
    }
    
    # 网络优化设置
    NETWORK_OPTIMIZATION = {
        'http2_push': True,
        'dns_prefetch': True,
        'preconnect': True,
        'resource_hints': True
    }
    
    # 移动端优化
    MOBILE_OPTIMIZATION = {
        'touch_optimized': True,
        'viewport_optimization': True,
        'reduced_motion': True
    }
    
    # 无障碍优化
    ACCESSIBILITY_OPTIMIZATION = {
        'aria_labels': True,
        'keyboard_navigation': True,
        'screen_reader_support': True,
        'high_contrast_support': True
    }
    
    # 安全设置
    SECURITY_OPTIMIZATION = {
        'csp_enabled': True,
        'hsts_enabled': True,
        'xss_protection': True,
        'content_type_options': True
    }
    
    @classmethod
    def get_csp_policy(cls):
        """获取内容安全策略"""
        return {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:"
            ],
            'font-src': [
                "'self'",
                "https://cdnjs.cloudflare.com"
            ],
            'connect-src': [
                "'self'"
            ]
        }
    
    @classmethod
    def get_resource_hints(cls):
        """获取资源提示"""
        return {
            'dns-prefetch': [
                '//cdn.jsdelivr.net',
                '//cdnjs.cloudflare.com'
            ],
            'preconnect': [
                'https://cdn.jsdelivr.net',
                'https://cdnjs.cloudflare.com'
            ],
            'preload': cls.CRITICAL_RESOURCES,
            'prefetch': [
                '/auth/login',
                '/auth/register',
                '/main/order_list'
            ]
        }
    
    @classmethod
    def get_cache_headers(cls):
        """获取缓存头设置"""
        return {
            'static_files': {
                'Cache-Control': 'public, max-age=31536000, immutable',
                'ETag': True
            },
            'html_pages': {
                'Cache-Control': 'public, max-age=3600',
                'ETag': True
            },
            'api_responses': {
                'Cache-Control': 'private, max-age=300',
                'ETag': True
            }
        }
    
    @classmethod
    def get_compression_settings(cls):
        """获取压缩设置"""
        return {
            'gzip': {
                'enabled': True,
                'level': 6,
                'min_size': 1024
            },
            'brotli': {
                'enabled': True,
                'level': 4,
                'min_size': 1024
            }
        }
    
    @classmethod
    def get_performance_budget(cls):
        """获取性能预算"""
        return {
            'first_contentful_paint': 1500,  # 1.5秒
            'largest_contentful_paint': 2500,  # 2.5秒
            'first_input_delay': 100,  # 100毫秒
            'cumulative_layout_shift': 0.1,  # 0.1
            'total_blocking_time': 300,  # 300毫秒
            'speed_index': 2000,  # 2秒
            'max_bundle_size': 250000,  # 250KB
            'max_image_size': 1000000  # 1MB
        }
    
    @classmethod
    def get_optimization_rules(cls):
        """获取优化规则"""
        return {
            'images': {
                'webp_support': True,
                'responsive_images': True,
                'lazy_loading': True,
                'compression': True
            },
            'javascript': {
                'async_loading': True,
                'defer_non_critical': True,
                'code_splitting': True,
                'tree_shaking': True
            },
            'css': {
                'critical_css_inline': True,
                'unused_css_removal': True,
                'css_minification': True
            },
            'fonts': {
                'font_display_swap': True,
                'font_preloading': True,
                'font_subsetting': True
            }
        }
    
    @classmethod
    def get_monitoring_endpoints(cls):
        """获取监控端点"""
        return {
            'performance_metrics': '/api/performance/metrics',
            'error_reporting': '/api/errors/report',
            'user_interactions': '/api/analytics/interactions',
            'resource_timing': '/api/performance/resources'
        }
    
    @classmethod
    def is_development(cls):
        """是否为开发环境"""
        import os
        return os.environ.get('FLASK_ENV') == 'development'
    
    @classmethod
    def is_production(cls):
        """是否为生产环境"""
        import os
        return os.environ.get('FLASK_ENV') == 'production'
    
    @classmethod
    def get_environment_specific_config(cls):
        """获取环境特定配置"""
        if cls.is_development():
            return {
                'debug': True,
                'minify': False,
                'source_maps': True,
                'cache': False
            }
        else:
            return {
                'debug': False,
                'minify': True,
                'source_maps': False,
                'cache': True
            } 