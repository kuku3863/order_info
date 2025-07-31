# API响应优化器
import json
import gzip
from functools import wraps
from flask import request, jsonify, Response, current_app
from flask_compress import Compress

# 初始化压缩
compress = Compress()

class APIOptimizer:
    """API响应优化器"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化API优化配置"""
        # 启用Gzip压缩
        compress.init_app(app)
        
        # 配置JSON响应
        app.config['JSON_AS_ASCII'] = False
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # 生产环境禁用美化
        
        # 注册响应处理器
        @app.after_request
        def add_response_headers(response):
            # 添加缓存头
            if request.endpoint and 'static' in request.endpoint:
                response.cache_control.max_age = 31536000  # 1年
                response.cache_control.public = True
            else:
                response.cache_control.no_cache = True
            
            # 添加安全头
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            return response
    
    def paginate_response(self, query, page=1, per_page=20, schema=None):
        """分页响应优化"""
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # 构建响应数据
        data = {
            'items': [schema.dump(item) if schema else item.to_dict() for item in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_num': pagination.next_num,
                'prev_num': pagination.prev_num
            }
        }
        
        return self.optimize_response(data)
    
    def optimize_response(self, data, status_code=200):
        """优化响应数据"""
        # 检查是否请求压缩
        if 'gzip' in request.headers.get('Accept-Encoding', ''):
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            compressed = gzip.compress(json_str.encode('utf-8'))
            response = Response(compressed, status=status_code)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Length'] = len(compressed)
            return response
        
        return jsonify(data), status_code
    
    def error_response(self, message, status_code=400, error_code=None):
        """错误响应优化"""
        data = {
            'error': True,
            'message': message,
            'status_code': status_code
        }
        
        if error_code:
            data['error_code'] = error_code
        
        return self.optimize_response(data, status_code)
    
    def success_response(self, data=None, message="Success", status_code=200):
        """成功响应优化"""
        response_data = {
            'success': True,
            'message': message,
            'data': data
        }
        
        return self.optimize_response(response_data, status_code)

# 全局API优化器实例
api_optimizer = APIOptimizer()

# 便捷函数
def paginate_response(query, page=1, per_page=20, schema=None):
    """分页响应"""
    return api_optimizer.paginate_response(query, page, per_page, schema)

def optimize_response(data, status_code=200):
    """优化响应"""
    return api_optimizer.optimize_response(data, status_code)

def error_response(message, status_code=400, error_code=None):
    """错误响应"""
    return api_optimizer.error_response(message, status_code, error_code)

def success_response(data=None, message="Success", status_code=200):
    """成功响应"""
    return api_optimizer.success_response(data, message, status_code)

# API装饰器
def api_response(success_message="Success", error_message="Error"):
    """API响应装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if isinstance(result, tuple):
                    data, status_code = result
                else:
                    data, status_code = result, 200
                
                return success_response(data, success_message, status_code)
            except Exception as e:
                current_app.logger.error(f"API Error: {str(e)}")
                return error_response(error_message, 500)
        return wrapper
    return decorator 