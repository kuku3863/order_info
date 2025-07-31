# 静态资源优化器
import os
import hashlib
from PIL import Image
from io import BytesIO
from flask import current_app, send_file, request
from werkzeug.utils import secure_filename

class StaticOptimizer:
    """静态资源优化器"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化静态资源优化配置"""
        # 配置静态文件路径
        app.config['STATIC_FOLDER'] = 'static'
        # 不覆盖已有的 UPLOAD_FOLDER 配置
        if 'UPLOAD_FOLDER' not in app.config:
            app.config['UPLOAD_FOLDER'] = 'static/uploads'
        
        # 图片优化配置
        app.config['IMAGE_OPTIMIZATION'] = {
            'max_width': 1920,
            'max_height': 1080,
            'quality': 85,
            'formats': ['webp', 'jpg', 'png'],
            'thumbnail_size': (150, 150)
        }
        
        # 确保上传目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    def optimize_image(self, image_file, max_width=None, max_height=None, quality=None):
        """优化图片"""
        try:
            # 打开图片
            img = Image.open(image_file)
            
            # 获取配置
            config = current_app.config.get('IMAGE_OPTIMIZATION', {})
            max_w = max_width or config.get('max_width', 1920)
            max_h = max_height or config.get('max_height', 1080)
            q = quality or config.get('quality', 85)
            
            # 调整大小
            if img.width > max_w or img.height > max_h:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            
            # 转换为RGB模式（如果是RGBA）
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 保存优化后的图片
            output = BytesIO()
            img.save(output, format='JPEG', quality=q, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            current_app.logger.error(f"图片优化失败: {str(e)}")
            return None
    
    def create_thumbnail(self, image_file, size=(150, 150)):
        """创建缩略图"""
        try:
            img = Image.open(image_file)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            current_app.logger.error(f"缩略图创建失败: {str(e)}")
            return None
    
    def get_file_hash(self, file_path):
        """获取文件哈希值（用于缓存）"""
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        return None
    
    def serve_optimized_image(self, filename, width=None, height=None, quality=None):
        """提供优化后的图片"""
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            # 检查是否需要优化
            if width or height or quality:
                with open(file_path, 'rb') as f:
                    optimized = self.optimize_image(f, width, height, quality)
                    if optimized:
                        return send_file(
                            optimized,
                            mimetype='image/jpeg',
                            as_attachment=False,
                            download_name=filename
                        )
            
            # 返回原图
            return send_file(file_path)
            
        except Exception as e:
            current_app.logger.error(f"图片服务失败: {str(e)}")
            return None
    
    def minify_css(self, css_content):
        """压缩CSS"""
        # 简单的CSS压缩
        import re
        
        # 移除注释
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # 移除多余空白
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r';\s*}', '}', css_content)
        css_content = re.sub(r'{\s*', '{', css_content)
        css_content = re.sub(r'}\s*', '}', css_content)
        
        return css_content.strip()
    
    def minify_js(self, js_content):
        """压缩JavaScript"""
        # 简单的JS压缩
        import re
        
        # 移除单行注释
        js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
        
        # 移除多行注释
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # 移除多余空白
        js_content = re.sub(r'\s+', ' ', js_content)
        
        return js_content.strip()
    
    def generate_asset_url(self, filename, version=None):
        """生成带版本号的资源URL"""
        if not version:
            file_path = os.path.join(current_app.static_folder, filename)
            version = self.get_file_hash(file_path) or 'v1'
        
        return f"/static/{filename}?v={version}"

# 全局静态优化器实例
static_optimizer = StaticOptimizer()

# 便捷函数
def optimize_image(image_file, max_width=None, max_height=None, quality=None):
    """优化图片"""
    return static_optimizer.optimize_image(image_file, max_width, max_height, quality)

def create_thumbnail(image_file, size=(150, 150)):
    """创建缩略图"""
    return static_optimizer.create_thumbnail(image_file, size)

def serve_optimized_image(filename, width=None, height=None, quality=None):
    """提供优化后的图片"""
    return static_optimizer.serve_optimized_image(filename, width, height, quality)

def minify_css(css_content):
    """压缩CSS"""
    return static_optimizer.minify_css(css_content)

def minify_js(js_content):
    """压缩JavaScript"""
    return static_optimizer.minify_js(js_content)

def generate_asset_url(filename, version=None):
    """生成资源URL"""
    return static_optimizer.generate_asset_url(filename, version)