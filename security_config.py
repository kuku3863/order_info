#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全配置文件
提供应用程序的安全配置和最佳实践
"""

import os
from datetime import timedelta

class SecurityConfig:
    """安全配置类"""
    
    # 密码策略
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL_CHARS = False
    
    # 会话安全
    SESSION_COOKIE_SECURE = True  # 仅HTTPS
    SESSION_COOKIE_HTTPONLY = True  # 防止XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF保护
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # 会话超时
    
    # 文件上传安全
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    UPLOAD_FOLDER_PERMISSIONS = 0o755
    
    # 请求限制
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100 per hour'
    RATELIMIT_LOGIN = '5 per minute'
    
    # 安全头
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # 数据库安全
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'check_same_thread': False,  # SQLite特定
            'timeout': 20
        }
    }
    
    # 日志安全
    LOG_SENSITIVE_DATA = False
    LOG_LEVEL = 'INFO'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    @staticmethod
    def validate_password(password):
        """验证密码强度"""
        if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
            return False, f"密码长度至少{SecurityConfig.PASSWORD_MIN_LENGTH}位"
        
        if len(password) > SecurityConfig.PASSWORD_MAX_LENGTH:
            return False, f"密码长度不能超过{SecurityConfig.PASSWORD_MAX_LENGTH}位"
        
        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "密码必须包含大写字母"
        
        if SecurityConfig.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "密码必须包含小写字母"
        
        if SecurityConfig.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"
        
        if SecurityConfig.PASSWORD_REQUIRE_SPECIAL_CHARS:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                return False, "密码必须包含特殊字符"
        
        return True, "密码强度符合要求"
    
    @staticmethod
    def sanitize_filename(filename):
        """清理文件名，防止路径遍历攻击"""
        import re
        from werkzeug.utils import secure_filename
        
        # 使用werkzeug的secure_filename
        filename = secure_filename(filename)
        
        # 额外的清理
        filename = re.sub(r'[^\w\-_\.]', '', filename)
        
        # 限制文件名长度
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    @staticmethod
    def validate_file_type(file_content, allowed_types=None):
        """验证文件类型（基于文件头）"""
        if allowed_types is None:
            allowed_types = SecurityConfig.ALLOWED_EXTENSIONS
        
        # 文件签名检查
        signatures = {
            b'\xff\xd8\xff': 'jpg',
            b'\x89PNG\r\n\x1a\n': 'png',
            b'GIF87a': 'gif',
            b'GIF89a': 'gif',
            b'RIFF': 'webp'
        }
        
        for signature, file_type in signatures.items():
            if file_content.startswith(signature) and file_type in allowed_types:
                return True, file_type
        
        return False, None
    
    @staticmethod
    def get_safe_redirect_url(url, fallback_url='/'):
        """获取安全的重定向URL，防止开放重定向攻击"""
        from urllib.parse import urlparse, urljoin
        from flask import request
        
        if not url:
            return fallback_url
        
        # 解析URL
        parsed = urlparse(url)
        
        # 只允许相对URL或同域URL
        if parsed.netloc and parsed.netloc != request.host:
            return fallback_url
        
        # 防止javascript:等危险协议
        if parsed.scheme and parsed.scheme not in ['http', 'https', '']:
            return fallback_url
        
        return url