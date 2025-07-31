# 缓存管理器
import time
import json
import hashlib
from functools import wraps
from flask import current_app, request
from flask_caching import Cache

# 初始化缓存
cache = Cache()

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化缓存配置"""
        cache_config = {
            'CACHE_TYPE': 'simple',  # 使用内存缓存，生产环境可改为redis
            'CACHE_DEFAULT_TIMEOUT': 300,  # 5分钟默认超时
            'CACHE_KEY_PREFIX': 'order_system_',
            'CACHE_THRESHOLD': 1000,  # 最大缓存条目数
        }
        
        app.config.update(cache_config)
        cache.init_app(app)
    
    def generate_cache_key(self, prefix, *args, **kwargs):
        """生成缓存键"""
        # 将参数转换为字符串
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            key_parts.append(str(arg))
        
        # 添加关键字参数
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        # 添加用户ID（如果已登录）
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            key_parts.append(f"user:{request.user.id}")
        
        # 生成MD5哈希
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cache_result(self, timeout=300, key_prefix=''):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self.generate_cache_key(key_prefix or func.__name__, *args, **kwargs)
                
                # 尝试从缓存获取
                result = cache.get(cache_key)
                if result is not None:
                    return result
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 存入缓存
                cache.set(cache_key, result, timeout=timeout)
                
                return result
            return wrapper
        return decorator
    
    def invalidate_cache(self, pattern=''):
        """清除缓存"""
        if pattern:
            # 清除特定模式的缓存
            cache.delete_pattern(pattern)
        else:
            # 清除所有缓存
            cache.clear()
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        try:
            # 这里可以添加缓存统计逻辑
            return {
                'cache_type': current_app.config.get('CACHE_TYPE', 'unknown'),
                'cache_timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
                'cache_prefix': current_app.config.get('CACHE_KEY_PREFIX', ''),
            }
        except Exception as e:
            return {'error': str(e)}

# 全局缓存管理器实例
cache_manager = CacheManager()

# 缓存装饰器
def cached(timeout=300, key_prefix=''):
    """缓存装饰器"""
    return cache_manager.cache_result(timeout, key_prefix)

def invalidate_cache(pattern=''):
    """清除缓存"""
    return cache_manager.invalidate_cache(pattern)

def get_cache_stats():
    """获取缓存统计"""
    return cache_manager.get_cache_stats()

# 预定义的缓存键
class CacheKeys:
    """缓存键常量"""
    ORDER_LIST = 'order_list'
    ORDER_STATS = 'order_stats'
    USER_STATS = 'user_stats'
    WECHAT_USER_STATS = 'wechat_user_stats'
    ORDER_TYPE_STATS = 'order_type_stats'
    CUSTOM_FIELDS = 'custom_fields'
    ORDER_TYPES = 'order_types'
    USERS = 'users'
    WECHAT_USERS = 'wechat_users' 