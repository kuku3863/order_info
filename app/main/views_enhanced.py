# 增强版视图文件 - 集成缓存和API优化
import os
import uuid
import shutil
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify, abort, send_from_directory
from flask_login import login_required, current_user
from .. import csrf
from . import main
from .. import db
from ..models import Order, OrderImage, Permission, OrderField, OrderType, WechatUser
from ..forms import OrderForm
from ..decorators import admin_required
from werkzeug.utils import secure_filename

# 导入优化模块
from ..cache_manager import cached, CacheKeys
from ..api_optimizer import paginate_response, success_response, error_response
from ..static_optimizer import optimize_image, serve_optimized_image

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file, subfolder=''):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        if subfolder:
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            return f"uploads/{subfolder}/{unique_filename}"
        else:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            return f"uploads/{unique_filename}"
    return None

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.order_list'))
    return render_template('index.html')

@main.route('/orders')
@login_required
@cached(timeout=60, key_prefix=CacheKeys.ORDER_LIST)  # 缓存1分钟
def order_list():
    """优化的订单列表查询 - 带缓存"""
    from datetime import date, timedelta
    
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_type = request.args.get('search_type', 'wechat_name')
    search_value = request.args.get('search_value', '').strip()
    
    # 权限控制
    if current_user.can(Permission.VIEW_ALL):
        query_user_id = user_id
    else:
        query_user_id = current_user.id
    
    # 日期筛选，默认当前月份
    if not start_date and not end_date:
        today = date.today()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 转换日期格式
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            flash('开始日期格式错误', 'danger')
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        except ValueError:
            flash('结束日期格式错误', 'danger')
    
    # 使用优化的查询方法
    query = Order.get_optimized_query(
        user_id=query_user_id,
        start_date=start_dt,
        end_dt=end_dt,
        search_type=search_type,
        search_value=search_value,
        include_relations=True
    )
    
    # 分页
    pagination = query.order_by(Order.create_time.desc()).paginate(
        page=page, per_page=10, error_out=False)
    orders = pagination.items
    
    # 使用优化的统计查询
    stats = Order.get_statistics(
        user_id=query_user_id,
        start_date=start_dt,
        end_date=end_dt
    )
    
    # 获取微信用户总数（缓存）
    total_wechat_users = get_wechat_users_count()
    
    # 获取自定义字段信息（缓存）
    custom_fields = get_custom_fields()
    
    # 获取所有用户（仅管理员可见，缓存）
    users = []
    if current_user.can(Permission.VIEW_ALL):
        users = get_users_list()
    
    return render_template('main/order_list.html', 
                         orders=orders, 
                         pagination=pagination, 
                         custom_fields=custom_fields,
                         users=users,
                         total_amount=stats['total_amount'],
                         total_quantity=stats['total_quantity'],
                         total_wechat_users=total_wechat_users,
                         current_filters={
                             'user_id': user_id,
                             'start_date': start_date,
                             'end_date': end_date,
                             'search_type': search_type,
                             'search_value': search_value
                         })

@cached(timeout=300, key_prefix=CacheKeys.WECHAT_USERS)
def get_wechat_users_count():
    """获取微信用户总数 - 缓存5分钟"""
    return WechatUser.query.count()

@cached(timeout=600, key_prefix=CacheKeys.CUSTOM_FIELDS)
def get_custom_fields():
    """获取自定义字段 - 缓存10分钟"""
    return OrderField.query.filter_by(is_default=False).order_by(OrderField.order).all()

@cached(timeout=300, key_prefix=CacheKeys.USERS)
def get_users_list():
    """获取用户列表 - 缓存5分钟"""
    from ..models import User
    return User.query.all()

@main.route('/api/orders')
@login_required
def api_orders():
    """API接口 - 订单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        
        # 权限控制
        if current_user.can(Permission.VIEW_ALL):
            query_user_id = user_id
        else:
            query_user_id = current_user.id
        
        # 构建查询
        query = Order.get_optimized_query(
            user_id=query_user_id,
            include_relations=True
        )
        
        # 返回分页响应
        return paginate_response(query, page, per_page)
        
    except Exception as e:
        current_app.logger.error(f"API订单列表错误: {str(e)}")
        return error_response("获取订单列表失败", 500)

@main.route('/api/orders/<int:order_id>')
@login_required
def api_order_detail(order_id):
    """API接口 - 订单详情"""
    try:
        order = Order.get_optimized_query(include_relations=True).filter(Order.id == order_id).first()
        
        if not order:
            return error_response("订单不存在", 404)
        
        # 权限检查
        if not current_user.can(Permission.VIEW_ALL) and order.user_id != current_user.id:
            return error_response("无权限访问", 403)
        
        return success_response(order.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"API订单详情错误: {str(e)}")
        return error_response("获取订单详情失败", 500)

@main.route('/api/statistics')
@login_required
@cached(timeout=300, key_prefix=CacheKeys.ORDER_STATS)
def api_statistics():
    """API接口 - 统计数据"""
    try:
        user_id = request.args.get('user_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 转换日期
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        
        # 获取统计数据
        stats = Order.get_statistics(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return success_response(stats)
        
    except Exception as e:
        current_app.logger.error(f"API统计错误: {str(e)}")
        return error_response("获取统计数据失败", 500)

@main.route('/optimized-image/<path:filename>')
def optimized_image(filename):
    """提供优化后的图片"""
    width = request.args.get('width', type=int)
    height = request.args.get('height', type=int)
    quality = request.args.get('quality', type=int)
    
    return serve_optimized_image(filename, width, height, quality)

@main.route('/order/new', methods=['GET', 'POST'])
@login_required
def new_order():
    """优化的新订单创建"""
    form = OrderForm()
    
    # 预加载订单类型和字段（缓存）
    form.order_type_id.choices = get_order_types_choices()
    
    if form.validate_on_submit():
        # 生成订单编号
        order_code = f"{datetime.now().strftime('%y%m%d')}-{int(datetime.now().timestamp() * 1000)}"
        
        order = Order(
            order_code=order_code,
            wechat_name=form.wechat_name.data,
            wechat_id=form.wechat_id.data,
            phone=form.phone.data,
            order_info=form.order_info.data,
            completion_time=form.completion_time.data,
            quantity=form.quantity.data,
            amount=form.amount.data,
            notes=form.notes.data,
            user_id=current_user.id,
            order_type_id=form.order_type_id.data
        )
        
        # 处理自定义字段
        custom_fields = get_custom_fields()
        for field in custom_fields:
            if hasattr(form, field.name):
                value = getattr(form, field.name).data
                if value:
                    order.set_custom_field(field.name, value)
        
        # 处理图片上传（优化）
        if form.images.data:
            for image_file in form.images.data:
                if image_file.filename:
                    # 优化图片
                    optimized_image = optimize_image(image_file)
                    if optimized_image:
                        image_path = save_image(optimized_image)
                        if image_path:
                            order_image = OrderImage(image_path=image_path)
                            order.images.append(order_image)
        
        db.session.add(order)
        db.session.commit()
        
        # 清除相关缓存
        from ..cache_manager import invalidate_cache
        invalidate_cache(CacheKeys.ORDER_LIST)
        invalidate_cache(CacheKeys.ORDER_STATS)
        
        flash('订单创建成功！', 'success')
        return redirect(url_for('main.order_list'))
    
    return render_template('main/new_order.html', form=form)

@cached(timeout=600, key_prefix=CacheKeys.ORDER_TYPES)
def get_order_types_choices():
    """获取订单类型选择 - 缓存10分钟"""
    return [(t.id, t.name) for t in OrderType.query.filter_by(is_active=True).all()]

# 其他视图函数保持不变... 