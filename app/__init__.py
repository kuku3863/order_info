from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录才能访问此页面'
bootstrap = Bootstrap()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 初始化数据库
    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # 缓存和API优化功能已移除，保持代码简洁
    
    # 静态资源优化功能已移除
    
    # 注册蓝图
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # 注册上下文处理器
    from .context_processors import inject_permissions
    app.context_processor(inject_permissions)
    
    # 注册自定义过滤器
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """将换行符转换为HTML的<br>标签"""
        if text is None:
            return ''
        from markupsafe import Markup
        return Markup(text.replace('\n', '<br>'))
    
    # 注册moment模板函数
    @app.template_global()
    def moment(timestamp):
        """格式化时间戳"""
        if timestamp is None:
            return ''
        from datetime import datetime
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                return timestamp
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    # 注册全局变量
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}
    
    # 注册性能监控
    @app.before_request
    def before_request():
        """请求前处理"""
        from flask import g
        import time
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """请求后处理"""
        from flask import g
        if hasattr(g, 'start_time'):
            import time
            duration = time.time() - g.start_time
            # 记录慢请求
            if duration > 1.0:  # 超过1秒的请求
                app.logger.warning(f"慢请求: {request.endpoint} 耗时 {duration:.2f}秒")
        return response
    
    return app