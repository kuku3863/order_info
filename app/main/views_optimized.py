# 优化版本的视图文件
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
def order_list():
    """优化的订单列表查询"""
    from datetime import date, timedelta
    
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_type = request.args.get('search_type', 'wechat_name')
    search_value = request.args.get('search_value', '').strip()
    
    # 权限控制
    if current_user.can(Permission.VIEW_ALL):
        # 管理员可以查看所有订单，可以按用户筛选
        query_user_id = user_id
    else:
        # 普通用户只能查看自己的订单
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
        end_date=end_dt,
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
    
    # 获取微信用户总数（使用缓存或优化查询）
    total_wechat_users = WechatUser.query.count()
    
    # 获取自定义字段信息
    custom_fields = OrderField.query.filter_by(is_default=False).order_by(OrderField.order).all()
    
    # 获取所有用户（仅管理员可见）
    users = []
    if current_user.can(Permission.VIEW_ALL):
        from ..models import User
        users = User.query.all()
    
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

@main.route('/order/new', methods=['GET', 'POST'])
@login_required
def new_order():
    """优化的新订单创建"""
    form = OrderForm()
    
    # 预加载订单类型和字段
    form.order_type_id.choices = [(t.id, t.name) for t in OrderType.query.filter_by(is_active=True).all()]
    
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
        custom_fields = OrderField.query.filter_by(is_default=False).all()
        for field in custom_fields:
            if hasattr(form, field.name):
                value = getattr(form, field.name).data
                if value:
                    order.set_custom_field(field.name, value)
        
        # 处理图片上传
        if form.images.data:
            for image_file in form.images.data:
                if image_file.filename:
                    image_path = save_image(image_file)
                    if image_path:
                        order_image = OrderImage(image_path=image_path)
                        order.images.append(order_image)
        
        db.session.add(order)
        db.session.commit()
        
        flash('订单创建成功！', 'success')
        return redirect(url_for('main.order_list'))
    
    return render_template('main/new_order.html', form=form)

@main.route('/order/<int:id>')
@login_required
def view_order(id):
    """优化的订单查看"""
    # 使用优化的查询，预加载关联数据
    order = Order.get_optimized_query(include_relations=True).filter(Order.id == id).first()
    
    if not order:
        abort(404)
    
    # 权限检查
    if not current_user.can(Permission.VIEW_ALL) and order.user_id != current_user.id:
        abort(403)
    
    return render_template('main/view_order.html', order=order)

@main.route('/order/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    """优化的订单编辑"""
    order = Order.query.get_or_404(id)
    
    # 权限检查
    if not current_user.can(Permission.VIEW_ALL) and order.user_id != current_user.id:
        abort(403)
    
    form = OrderForm(obj=order)
    form.order_type_id.choices = [(t.id, t.name) for t in OrderType.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # 更新订单信息
        order.wechat_name = form.wechat_name.data
        order.wechat_id = form.wechat_id.data
        order.phone = form.phone.data
        order.order_info = form.order_info.data
        order.completion_time = form.completion_time.data
        order.quantity = form.quantity.data
        order.amount = form.amount.data
        order.notes = form.notes.data
        order.order_type_id = form.order_type_id.data
        
        # 处理自定义字段
        custom_fields = OrderField.query.filter_by(is_default=False).all()
        for field in custom_fields:
            if hasattr(form, field.name):
                value = getattr(form, field.name).data
                order.set_custom_field(field.name, value)
        
        # 处理新图片上传
        if form.images.data:
            for image_file in form.images.data:
                if image_file.filename:
                    image_path = save_image(image_file)
                    if image_path:
                        order_image = OrderImage(image_path=image_path)
                        order.images.append(order_image)
        
        db.session.commit()
        flash('订单更新成功！', 'success')
        return redirect(url_for('main.view_order', id=order.id))
    
    return render_template('main/edit_order.html', form=form, order=order)

@main.route('/orders/statistics')
@login_required
def order_statistics():
    """优化的订单统计"""
    # 仅超级管理员可访问
    if not current_user.can(Permission.VIEW_ALL):
        abort(403)
    
    from datetime import date, timedelta
    from sqlalchemy import func
    from ..models import User
    
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_type = request.args.get('search_type', 'wechat_name')
    search_value = request.args.get('search_value', '').strip()
    sort_by = request.args.get('sort_by', 'amount')
    
    # 转换日期
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
        user_id=user_id,
        start_date=start_dt,
        end_date=end_dt,
        search_type=search_type,
        search_value=search_value,
        include_relations=False  # 统计查询不需要关联数据
    )
    
    # 获取统计数据
    stats = Order.get_statistics(
        user_id=user_id,
        start_date=start_dt,
        end_date=end_dt
    )
    
    # 按用户统计（优化版本）
    user_stats_query = db.session.query(
        User.username,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount')
    ).join(Order, User.id == Order.user_id)
    
    # 应用筛选条件
    if user_id:
        user_stats_query = user_stats_query.filter(Order.user_id == user_id)
    if start_dt:
        user_stats_query = user_stats_query.filter(Order.create_time >= start_dt)
    if end_dt:
        user_stats_query = user_stats_query.filter(Order.create_time <= end_dt)
    if search_value:
        if search_type == 'wechat_name':
            user_stats_query = user_stats_query.filter(Order.wechat_name.contains(search_value))
        elif search_type == 'wechat_id':
            user_stats_query = user_stats_query.filter(Order.wechat_id.contains(search_value))
        elif search_type == 'phone':
            user_stats_query = user_stats_query.filter(Order.phone.contains(search_value))
    
    user_stats = user_stats_query.group_by(User.id, User.username).all()
    
    # 按微信用户统计（优化版本）
    wechat_stats_query = query.with_entities(
        Order.wechat_name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount')
    ).group_by(Order.wechat_name)
    
    if sort_by == 'count':
        wechat_stats = wechat_stats_query.order_by(func.count(Order.id).desc()).limit(10).all()
    else:
        wechat_stats = wechat_stats_query.order_by(func.sum(Order.amount).desc()).limit(10).all()
    
    # 按订单类型统计（优化版本）
    type_stats_query = db.session.query(
        OrderType.name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount')
    ).join(Order, OrderType.id == Order.order_type_id, isouter=True)
    
    # 应用筛选条件
    if user_id:
        type_stats_query = type_stats_query.filter(Order.user_id == user_id)
    if start_dt:
        type_stats_query = type_stats_query.filter(Order.create_time >= start_dt)
    if end_dt:
        type_stats_query = type_stats_query.filter(Order.create_time <= end_dt)
    if search_value:
        if search_type == 'wechat_name':
            type_stats_query = type_stats_query.filter(Order.wechat_name.contains(search_value))
        elif search_type == 'wechat_id':
            type_stats_query = type_stats_query.filter(Order.wechat_id.contains(search_value))
        elif search_type == 'phone':
            type_stats_query = type_stats_query.filter(Order.phone.contains(search_value))
    
    type_stats = type_stats_query.group_by(OrderType.id, OrderType.name).all()
    
    return render_template('main/order_statistics.html',
                         total_orders=stats['total_orders'],
                         total_amount=stats['total_amount'],
                         avg_amount=stats['avg_amount'],
                         user_stats=user_stats,
                         wechat_stats=wechat_stats,
                         type_stats=type_stats,
                         current_filters={
                             'user_id': user_id,
                             'start_date': start_date,
                             'end_date': end_date,
                             'search_type': search_type,
                             'search_value': search_value,
                             'sort_by': sort_by
                         })

# 其他视图函数保持不变... 