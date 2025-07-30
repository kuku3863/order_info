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
        # 获取文件扩展名
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        # 生成唯一文件名，确保包含扩展名
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # 创建子目录路径
        if subfolder:
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            # 返回相对路径，用于存储在数据库（使用正斜杠以确保Web兼容性）
            return f"uploads/{subfolder}/{unique_filename}"
        else:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            # 返回相对路径，用于存储在数据库（使用正斜杠以确保Web兼容性）
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
    from datetime import date, timedelta
    from sqlalchemy import and_, extract
    
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_type = request.args.get('search_type', 'wechat_name')
    search_value = request.args.get('search_value', '').strip()
    sort_by = request.args.get('sort_by', 'amount')
    sort_by = request.args.get('sort_by', 'amount')  # 排序方式：amount(金额) 或 count(数量)
    
    # 构建查询
    query = Order.query
    
    # 权限控制
    if current_user.can(Permission.VIEW_ALL):
        # 管理员可以查看所有订单，可以按用户筛选
        if user_id:
            query = query.filter(Order.user_id == user_id)
    else:
        # 普通用户只能查看自己的订单
        query = query.filter(Order.user_id == current_user.id)
    
    # 日期筛选，默认当前月份
    if not start_date and not end_date:
        # 默认显示当前月份
        today = date.today()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        # 计算月末
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.completion_time >= start_dt)
        except ValueError:
            flash('开始日期格式错误', 'danger')
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(Order.completion_time <= end_dt)
        except ValueError:
            flash('结束日期格式错误', 'danger')
    
    # 用户搜索筛选
    if search_value:
        if search_type == 'order_code':
            query = query.filter(Order.order_code.contains(search_value))
        elif search_type == 'wechat_name':
            query = query.filter(Order.wechat_name.contains(search_value))
        elif search_type == 'wechat_id':
            query = query.filter(Order.wechat_id.contains(search_value))
        elif search_type == 'phone':
            query = query.filter(Order.phone.isnot(None)).filter(Order.phone.contains(search_value))
    

    
    # 分页
    pagination = query.order_by(Order.create_time.desc()).paginate(
        page=page, per_page=10, error_out=False)
    orders = pagination.items
    
    # 计算总金额
    total_amount = query.filter(Order.amount.isnot(None)).with_entities(db.func.sum(Order.amount)).scalar() or 0
    
    # 计算数量总数
    total_quantity = query.with_entities(db.func.sum(Order.quantity)).scalar() or 0
    
    # 获取微信用户总数
    from ..models import WechatUser
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
                         total_amount=total_amount,
                         total_quantity=total_quantity,
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
    form = OrderForm()
    if form.validate_on_submit():
        # 创建或更新微信用户资料
        wechat_user = WechatUser.query.filter_by(wechat_id=form.wechat_id.data).first()
        if not wechat_user:
            wechat_user = WechatUser(
                wechat_name=form.wechat_name.data,
                wechat_id=form.wechat_id.data
            )
            db.session.add(wechat_user)
        else:
            # 更新微信名（可能会变化）
            wechat_user.wechat_name = form.wechat_name.data
            wechat_user.update_time = datetime.utcnow()
        
        order = Order(
            order_code=form.order_code.data,
            wechat_name=form.wechat_name.data,
            wechat_id=form.wechat_id.data,
            phone=form.phone.data,
            notes=form.notes.data,
            order_info=form.order_info.data,
            completion_time=form.completion_time.data,
            quantity=form.quantity.data,
            amount=form.amount.data,
            order_type_id=form.order_type_id.data,
            user_id=current_user.id
        )
        
        # 处理自定义字段
        custom_fields = OrderField.query.filter_by(is_default=False).all()
        for field in custom_fields:
            if hasattr(form, field.name) and getattr(form, field.name).data is not None:
                order.set_custom_field(field.name, getattr(form, field.name).data)
        
        db.session.add(order)
        db.session.commit()
        
        # 处理图片上传
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                image_path = save_image(file)
                if image_path:
                    image = OrderImage(order_id=order.id, image_path=image_path)
                    db.session.add(image)
        
        db.session.commit()
        flash('订单已创建成功')
        return redirect(url_for('main.order_list'))
    
    return render_template('main/new_order.html', form=form)

@main.route('/order/<int:id>')
@login_required
def view_order(id):
    order = Order.query.get_or_404(id)
    # 检查权限
    if not current_user.can(Permission.VIEW_ALL) and order.user_id != current_user.id:
        abort(403)
    
    # 获取自定义字段信息
    custom_fields = OrderField.query.filter_by(is_default=False).order_by(OrderField.order).all()
    
    return render_template('main/view_order.html', order=order, custom_fields=custom_fields)

@main.route('/order/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    order = Order.query.get_or_404(id)
    
    # 权限检查：普通用户只能编辑自己的订单，超级管理员可以编辑所有订单
    if not current_user.can(Permission.VIEW_ALL) and order.user_id != current_user.id:
        abort(403)
    
    form = OrderForm(order=order)
    if form.validate_on_submit():
        # 创建或更新微信用户资料
        wechat_user = WechatUser.query.filter_by(wechat_id=form.wechat_id.data).first()
        if not wechat_user:
            wechat_user = WechatUser(
                wechat_name=form.wechat_name.data,
                wechat_id=form.wechat_id.data
            )
            db.session.add(wechat_user)
        else:
            # 更新微信名（可能会变化）
            wechat_user.wechat_name = form.wechat_name.data
            wechat_user.update_time = datetime.utcnow()
        
        order.order_code = form.order_code.data
        order.wechat_name = form.wechat_name.data
        order.wechat_id = form.wechat_id.data
        order.phone = form.phone.data
        order.notes = form.notes.data
        order.order_info = form.order_info.data
        order.completion_time = form.completion_time.data
        order.quantity = form.quantity.data
        order.amount = form.amount.data
        order.order_type_id = form.order_type_id.data
        
        # 处理自定义字段
        custom_fields = OrderField.query.filter_by(is_default=False).all()
        for field in custom_fields:
            if hasattr(form, field.name) and getattr(form, field.name).data is not None:
                order.set_custom_field(field.name, getattr(form, field.name).data)
        
        db.session.add(order)
        
        # 处理图片上传
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                image_path = save_image(file)
                if image_path:
                    image = OrderImage(order_id=order.id, image_path=image_path)
                    db.session.add(image)
        
        db.session.commit()
        flash('订单已更新成功')
        return redirect(url_for('main.view_order', id=order.id))
    
    # 填充表单数据
    form.order_code.data = order.order_code
    form.wechat_name.data = order.wechat_name
    form.wechat_id.data = order.wechat_id
    form.phone.data = order.phone
    form.notes.data = order.notes
    form.order_info.data = order.order_info
    form.completion_time.data = order.completion_time
    form.quantity.data = order.quantity
    form.amount.data = order.amount
    form.order_type_id.data = order.order_type_id
    
    # 填充自定义字段数据
    if order.custom_fields:
        import json
        custom_data = json.loads(order.custom_fields)
        for field_name, value in custom_data.items():
            if hasattr(form, field_name):
                getattr(form, field_name).data = value
    
    return render_template('main/edit_order.html', form=form, order=order)

@main.route('/order/delete/<int:id>', methods=['POST'])
@login_required
def delete_order(id):
    order = Order.query.get_or_404(id)
    # 检查权限
    if not current_user.can(Permission.VIEW_ALL) and order.user_id != current_user.id:
        abort(403)
        
    # 删除关联的图片文件
    for image in order.images:
        try:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path.replace('uploads/', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"删除图片文件失败: {e}")
    
    db.session.delete(order)
    db.session.commit()
    
    # 检查是否是AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    else:
        flash('订单已删除')
        return redirect(url_for('main.order_list'))



@main.route('/orders/statistics')
@login_required
def order_statistics():
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
    sort_by = request.args.get('sort_by', 'amount')  # 排序方式：amount(金额) 或 count(数量)
    
    # 构建查询
    query = Order.query
    
    # 用户筛选
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    # 日期筛选
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.completion_time >= start_dt)
        except ValueError:
            flash('开始日期格式错误', 'danger')
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(Order.completion_time <= end_dt)
        except ValueError:
            flash('结束日期格式错误', 'danger')
    
    # 用户搜索筛选
    if search_value:
        if search_type == 'wechat_name':
            query = query.filter(Order.wechat_name.contains(search_value))
        elif search_type == 'wechat_id':
            query = query.filter(Order.wechat_id.contains(search_value))
        elif search_type == 'phone':
            query = query.filter(Order.phone.isnot(None)).filter(Order.phone.contains(search_value))
    
    # 统计数据
    total_orders = query.count()
    total_amount = query.filter(Order.amount.isnot(None)).with_entities(func.sum(Order.amount)).scalar() or 0
    avg_amount = query.filter(Order.amount.isnot(None)).with_entities(func.avg(Order.amount)).scalar() or 0
    
    # 按用户统计
    user_stats = db.session.query(
        User.username,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount')
    ).join(Order, User.id == Order.user_id)
    
    if user_id:
        user_stats = user_stats.filter(Order.user_id == user_id)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            user_stats = user_stats.filter(Order.create_time >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            user_stats = user_stats.filter(Order.create_time <= end_dt)
        except ValueError:
            pass
    if search_value:
        if search_type == 'wechat_name':
            user_stats = user_stats.filter(Order.wechat_name.contains(search_value))
        elif search_type == 'wechat_id':
            user_stats = user_stats.filter(Order.wechat_id.contains(search_value))
        elif search_type == 'phone':
            user_stats = user_stats.filter(Order.phone.isnot(None)).filter(Order.phone.contains(search_value))
    
    user_stats = user_stats.group_by(User.id, User.username).all()
    
    # 按微信用户统计
    wechat_stats_query = query.with_entities(
        Order.wechat_name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount')
    ).group_by(Order.wechat_name)
    
    # 根据排序参数决定排序方式
    if sort_by == 'count':
        wechat_stats = wechat_stats_query.order_by(func.count(Order.id).desc()).limit(10).all()
    else:  # 默认按金额排序
        wechat_stats = wechat_stats_query.order_by(func.sum(Order.amount).desc()).limit(10).all()
    
    # 按订单类型统计
    type_stats = db.session.query(
        OrderType.name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount')
    ).join(Order, OrderType.id == Order.order_type_id, isouter=True)
    
    if user_id:
        type_stats = type_stats.filter(Order.user_id == user_id)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            type_stats = type_stats.filter(Order.create_time >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            type_stats = type_stats.filter(Order.create_time <= end_dt)
        except ValueError:
            pass
    if search_value:
        if search_type == 'wechat_name':
            type_stats = type_stats.filter(Order.wechat_name.contains(search_value))
        elif search_type == 'wechat_id':
            type_stats = type_stats.filter(Order.wechat_id.contains(search_value))
        elif search_type == 'phone':
            type_stats = type_stats.filter(Order.phone.isnot(None)).filter(Order.phone.contains(search_value))
    
    type_stats = type_stats.group_by(OrderType.id, OrderType.name).all()
    
    # 获取所有用户
    users = User.query.all()
    
    return render_template('main/order_statistics.html',
                         total_orders=total_orders,
                         total_amount=total_amount,
                         avg_amount=avg_amount,
                         user_stats=user_stats,
                         wechat_stats=wechat_stats,
                         type_stats=type_stats,
                         users=users,
                         current_filters={
                             'user_id': user_id,
                             'start_date': start_date,
                             'end_date': end_date,
                             'search_type': search_type,
                             'search_value': search_value,
                             'sort_by': sort_by
                         })

@main.route('/debug/user-info')
@login_required
def debug_user_info():
    """调试用户信息和权限"""
    user_info = {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role_name': current_user.role.name if current_user.role else None,
        'role_id': current_user.role_id,
        'permissions': {
            'VIEW_OWN': current_user.can(Permission.VIEW_OWN),
            'SUBMIT': current_user.can(Permission.SUBMIT),
            'VIEW_ALL': current_user.can(Permission.VIEW_ALL),
            'MANAGE_FIELDS': current_user.can(Permission.MANAGE_FIELDS),
            'ADMIN': current_user.can(Permission.ADMIN)
        }
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(user_info)
    else:
        return f"<pre>{user_info}</pre>"

@main.route('/orders/export-template')
@login_required
def export_template():
    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    # 获取所有字段（包括默认字段和自定义字段）
    default_fields = OrderField.query.filter_by(is_default=True).order_by(OrderField.order).all()
    custom_fields = OrderField.query.filter_by(is_default=False).order_by(OrderField.order).all()
    
    # 创建Excel工作簿和工作表
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "订单导入模板"
    
    # 定义样式
    header_font = Font(name='微软雅黑', size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")  # 更改为更美观的红色
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    data_font = Font(name='微软雅黑', size=10)
    data_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 写入表头
    headers = ['订单编码*', '订单类型', '微信名*', '微信号', '手机号', '订单信息*', '完成时间*', '数量*', '金额', '备注']
    required_fields = [True, False, True, False, False, True, True, True, False, False]  # 标记必填字段
    
    for field in custom_fields:
        headers.append(field.name + ('*' if field.required else ''))
        required_fields.append(field.required)
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # 写入一行示例数据
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    example = ['ORD20230101', '普通订单', '张三', 'zhangsan123', '13800138000', '产品A x 2', current_date, '2', '100', '订单备注信息']
    for field in custom_fields:
        if field.field_type == 'text':
            example.append('文本示例')
        elif field.field_type == 'number':
            example.append('10')
        elif field.field_type == 'date':
            example.append('2023-01-01')
    
    for col_idx, value in enumerate(example, 1):
        cell = ws.cell(row=2, column=col_idx, value=value)
        cell.font = data_font
        cell.alignment = data_alignment
        cell.border = thin_border
    
    # 设置列宽
    column_widths = [15, 12, 12, 15, 15, 20, 12, 8, 10, 20]
    for field in custom_fields:
        if field.field_type == 'text':
            column_widths.append(20)
        elif field.field_type == 'number':
            column_widths.append(10)
        elif field.field_type == 'date':
            column_widths.append(12)
        else:
            column_widths.append(15)
    
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    
    # 创建响应
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = current_app.response_class(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment;filename=order_template.xlsx'}
    )
    
    return response

@main.route('/orders/export')
@login_required
def export_orders():
    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    # 获取筛选参数
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    wechat_name = request.args.get('wechat_name', '').strip()
    phone = request.args.get('phone', '').strip()
    
    # 构建查询（复用订单列表的筛选逻辑）
    query = Order.query
    
    # 权限控制
    if current_user.can(Permission.VIEW_ALL):
        # 管理员可以查看所有订单，可以按用户筛选
        if user_id:
            query = query.filter(Order.user_id == user_id)
    else:
        # 普通用户只能查看自己的订单
        query = query.filter(Order.user_id == current_user.id)
    
    # 日期筛选
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.create_time >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(Order.create_time <= end_dt)
        except ValueError:
            pass
    
    # 微信用户筛选
    if wechat_name:
        query = query.filter(Order.wechat_name.contains(wechat_name))
    
    # 手机号筛选（支持模糊搜索）
    if phone:
        query = query.filter(Order.phone.contains(phone))
    
    # 获取筛选后的订单
    orders = query.order_by(Order.create_time.desc()).all()
    
    # 获取所有字段（包括默认字段和自定义字段）
    custom_fields = OrderField.query.filter_by(is_default=False).order_by(OrderField.order).all()
    
    # 创建Excel工作簿和工作表
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "订单数据"
    
    # 定义样式
    header_font = Font(name='微软雅黑', size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    data_font = Font(name='微软雅黑', size=10)
    data_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 写入表头
    headers = ['订单编码', '订单类型', '微信名', '微信号', '手机号', '订单信息', '完成时间', '数量', '金额', '备注', '创建时间']
    # 如果是管理员，添加提交用户列
    if current_user.can(Permission.VIEW_ALL):
        headers.append('提交用户')
    for field in custom_fields:
        headers.append(field.name)
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # 写入订单数据
    for row_idx, order in enumerate(orders, 2):
        data = [
            order.order_code,
            order.order_type.name if order.order_type else '未分类',
            order.wechat_name,
            order.wechat_id or '',
            order.phone or '',
            order.order_info,
            order.completion_time.strftime('%Y-%m-%d') if order.completion_time else '',
            order.quantity,
            order.amount if order.amount else '',
            order.notes or '',
            order.create_time.strftime('%Y-%m-%d %H:%M')
        ]
        
        # 如果是管理员，添加提交用户信息
        if current_user.can(Permission.VIEW_ALL):
            data.append(order.creator.username if order.creator else '')
        
        # 添加自定义字段值
        for field in custom_fields:
            value = order.get_custom_field(field.name)
            if value is not None:
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d')
                data.append(value)
            else:
                data.append('')
        
        for col_idx, value in enumerate(data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = data_alignment
            cell.border = thin_border
    
    # 设置列宽
    column_widths = [15, 12, 12, 15, 12, 25, 12, 8, 10, 20, 18]  # 添加手机号和备注的列宽
    # 如果是管理员，添加提交用户列宽
    if current_user.can(Permission.VIEW_ALL):
        column_widths.append(12)
    for field in custom_fields:
        if field.field_type == 'text':
            column_widths.append(20)
        elif field.field_type == 'number':
            column_widths.append(10)
        elif field.field_type == 'date':
            column_widths.append(12)
        else:
            column_widths.append(15)
    
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    
    # 创建响应
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = current_app.response_class(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment;filename=orders.xlsx'}
    )
    
    return response

@main.route('/orders/import', methods=['GET', 'POST'])
@login_required
def import_orders():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(request.url)
        
        filename = file.filename.lower()
        if file and (filename.endswith('.csv') or filename.endswith('.xlsx')):
            # 准备导入数据
            success_count = 0
            error_count = 0
            error_messages = []
            
            # 获取自定义字段
            custom_fields = OrderField.query.filter_by(is_default=False).all()
            custom_field_names = [field.name for field in custom_fields]
            
            # 根据文件类型处理数据
            if filename.endswith('.xlsx'):
                # 处理Excel文件
                import openpyxl
                from io import BytesIO
                
                # 读取Excel文件内容
                wb = openpyxl.load_workbook(BytesIO(file.read()))
                ws = wb.active
                
                # 读取表头
                headers = [cell.value for cell in ws[1]]
                
                # 处理每一行数据
                for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
                    row_data = [cell.value for cell in row]
                    
                    if not any(row_data):  # 跳过空行
                        continue
                    
                    # 确保行数据与表头数量一致
                    while len(row_data) < len(headers):
                        row_data.append('')
                    
                    try:
                        if len(row_data) < 10:  # 至少需要10个默认字段（包含手机号和备注）
                            error_count += 1
                            error_messages.append(f'第{i}行: 字段数量不足')
                            continue
                        
                        # 查找订单类型
                        order_type = None
                        if row_data[1]:  # 订单类型字段
                            order_type = OrderType.query.filter_by(name=row_data[1]).first()
                        
                        # 创建新订单
                        order = Order(
                            order_code=row_data[0],
                            order_type_id=order_type.id if order_type else None,
                            wechat_name=row_data[2],
                            wechat_id=row_data[3] if row_data[3] else None,
                            phone=row_data[4] if row_data[4] else None,
                            order_info=row_data[5],
                            completion_time=datetime.strptime(row_data[6], '%Y-%m-%d') if row_data[6] else None,
                            quantity=int(row_data[7]) if row_data[7] else 0,
                            amount=float(row_data[8]) if row_data[8] else None,
                            notes=row_data[9] if row_data[9] else None,
                            user_id=current_user.id
                        )
                        
                        # 处理自定义字段
                        for j, field_name in enumerate(headers[10:], start=10):
                            if j < len(row_data) and field_name in custom_field_names and row_data[j]:
                                field = next((f for f in custom_fields if f.name == field_name), None)
                                if field:
                                    if field.field_type == 'number':
                                        order.set_custom_field(field_name, float(row_data[j]))
                                    elif field.field_type == 'date':
                                        order.set_custom_field(field_name, datetime.strptime(row_data[j], '%Y-%m-%d'))
                                    else:
                                        order.set_custom_field(field_name, row_data[j])
                        
                        db.session.add(order)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f'第{i}行: {str(e)}')
            else:
                # 处理CSV文件
                import csv
                from io import StringIO
                import codecs
                
                # 读取CSV文件，尝试多种编码
                encodings = ['utf-8-sig', 'gbk', 'gb2312', 'latin-1']
                for encoding in encodings:
                    try:
                        # 重置文件指针到开始位置
                        file.stream.seek(0)
                        stream = codecs.iterdecode(file.stream, encoding)
                        # 尝试读取第一行来验证编码
                        test_reader = csv.reader(stream)
                        next(test_reader)
                        
                        # 如果没有抛出异常，说明编码正确
                        file.stream.seek(0)
                        stream = codecs.iterdecode(file.stream, encoding)
                        reader = csv.reader(stream)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # 如果所有编码都失败
                    flash('无法识别文件编码，请确保文件使用UTF-8、GBK或GB2312编码，或尝试使用Excel格式', 'danger')
                    return redirect(request.url)
                
                # 获取表头
                headers = next(reader)
                
                # 处理每一行数据
                for i, row in enumerate(reader, start=2):
                    if not any(row):  # 跳过空行
                        continue
                    
                    # 确保行数据与表头数量一致
                    while len(row) < len(headers):
                        row.append('')
                    
                    try:
                        if len(row) < 10:  # 至少需要10个默认字段（包含手机号和备注）
                            error_count += 1
                            error_messages.append(f'第{i}行: 字段数量不足')
                            continue
                        
                        # 查找订单类型
                        order_type = None
                        if row[1]:  # 订单类型字段
                            order_type = OrderType.query.filter_by(name=row[1]).first()
                        
                        # 创建新订单
                        order = Order(
                            order_code=row[0],
                            order_type_id=order_type.id if order_type else None,
                            wechat_name=row[2],
                            wechat_id=row[3] if row[3] else None,
                            phone=row[4] if row[4] else None,
                            order_info=row[5],
                            completion_time=datetime.strptime(row[6], '%Y-%m-%d') if row[6] else None,
                            quantity=int(row[7]) if row[7] else 0,
                            amount=float(row[8]) if row[8] else None,
                            notes=row[9] if row[9] else None,
                            user_id=current_user.id
                        )
                        
                        # 处理自定义字段
                        for j, field_name in enumerate(headers[10:], start=10):
                            if j < len(row) and field_name in custom_field_names and row[j]:
                                field = next((f for f in custom_fields if f.name == field_name), None)
                                if field:
                                    if field.field_type == 'number':
                                        order.set_custom_field(field_name, float(row[j]))
                                    elif field.field_type == 'date':
                                        order.set_custom_field(field_name, datetime.strptime(row[j], '%Y-%m-%d'))
                                    else:
                                        order.set_custom_field(field_name, row[j])
                        
                        db.session.add(order)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f'第{i}行: {str(e)}')
            
            if success_count > 0:
                db.session.commit()
                flash(f'成功导入{success_count}条订单记录', 'success')
            
            if error_count > 0:
                flash(f'导入过程中有{error_count}条记录出错', 'warning')
                for msg in error_messages[:10]:  # 只显示前10条错误信息
                    flash(msg, 'danger')
                if len(error_messages) > 10:
                    flash(f'... 还有 {len(error_messages) - 10} 条错误信息未显示', 'info')
            
            return redirect(url_for('main.order_list'))
        else:
            flash('请上传CSV或Excel(XLSX)格式的文件', 'danger')
    
    return render_template('main/import_orders.html')
    
    # 删除关联的图片文件
    for image in order.images:
        try:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path.replace('uploads/', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"删除图片文件失败: {e}")
    
    db.session.delete(order)
    db.session.commit()
    flash('订单已删除')
    return redirect(url_for('main.order_list'))

@main.route('/order/image/delete/<int:id>', methods=['POST'])
@login_required
def delete_image(id):
    image = OrderImage.query.get_or_404(id)
    order = Order.query.get(image.order_id)
    
    # 检查权限
    if not current_user.can(Permission.VIEW_ALL) and order.user_id != current_user.id:
        abort(403)
    
    # 删除图片文件
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path.replace('uploads/', ''))
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        current_app.logger.error(f"删除图片文件失败: {e}")
    
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'success': True})

@main.route('/quick_add', methods=['POST'])
@login_required
def quick_add_order():
    # 快速添加订单的API
    if not request.is_json:
        return jsonify({'error': '请求必须是JSON格式'}), 400
    
    data = request.json
    required_fields = ['order_code', 'wechat_name', 'wechat_id', 'order_info', 'quantity', 'amount']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    try:
        order = Order(
            order_code=data['order_code'],
            wechat_name=data['wechat_name'],
            wechat_id=data['wechat_id'],
            order_info=data['order_info'],
            completion_time=datetime.strptime(data.get('completion_time', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d'),
            quantity=int(data['quantity']),
            amount=float(data['amount']),
            user_id=current_user.id
        )
        
        # 处理自定义字段
        custom_fields = OrderField.query.filter_by(is_default=False).all()
        for field in custom_fields:
            if field.name in data:
                order.set_custom_field(field.name, data[field.name])
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': '订单已成功添加'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加订单失败: {str(e)}'}), 500

@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """提供上传图片的访问服务"""
    # 如果filename以'uploads/'开头，去掉这个前缀
    if filename.startswith('uploads/'):
        filename = filename[8:]  # 去掉'uploads/'前缀
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/order/update_status/<int:order_id>', methods=['POST'])
@csrf.exempt
@login_required
def update_order_status(order_id):
    """修改订单状态（管理员可用）"""
    # 调试信息
    print(f"\n=== 调试信息 - 修改订单状态 ===")
    print(f"订单ID: {order_id}")
    print(f"请求方法: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"is_json: {request.is_json}")
    print(f"request.json: {request.json}")
    print(f"request.form: {dict(request.form)}")
    print(f"request.data: {request.data}")
    print(f"当前用户: {current_user.username if current_user.is_authenticated else 'None'}")
    print(f"用户权限: {current_user.can(Permission.ADMIN) if current_user.is_authenticated else 'None'}")
    
    # 检查权限：只有管理员才能修改状态
    if not current_user.can(Permission.ADMIN):
        print("错误: 权限不足")
        return jsonify({'error': '权限不足'}), 403
    
    order = Order.query.get_or_404(order_id)
    print(f"找到订单: {order.order_code}，当前状态: {getattr(order, 'status', '无状态字段')}")
    
    # 支持JSON和表单数据
    new_status = None
    if request.is_json and request.json:
        new_status = request.json.get('status')
        print(f"使用JSON数据: {request.json}")
    elif request.form:
        new_status = request.form.get('status')
        print(f"使用表单数据: {dict(request.form)}")
    
    print(f"获取到的状态: {new_status}")
    
    if not new_status:
        print("错误: 状态为空")
        return jsonify({'error': '缺少状态参数'}), 400
    
    # 验证状态值
    valid_statuses = ['已结算', '未结算', '未完成']
    if new_status not in valid_statuses:
        print(f"错误: 无效状态值 {new_status}，有效值: {valid_statuses}")
        return jsonify({'error': '无效的订单状态'}), 400
    
    try:
        old_status = getattr(order, 'status', '无状态字段')
        order.status = new_status
        
        # 如果状态改为已结算，设置结算时间
        if new_status == '已结算':
            if hasattr(order, 'settle_time'):
                order.settle_time = datetime.utcnow()
        elif new_status in ['未完成', '未结算']:
            if hasattr(order, 'settle_time'):
                order.settle_time = None
        
        db.session.commit()
        print(f"状态更新成功: {old_status} -> {new_status}")
        print("=== 调试信息结束 ===\n")
        
        return jsonify({
            'success': True,
            'message': f'订单状态已更新为：{new_status}'
        })
    except Exception as e:
        db.session.rollback()
        print(f"异常错误: {str(e)}")
        print(f"异常类型: {type(e)}")
        import traceback
        print(f"异常堆栈: {traceback.format_exc()}")
        print("=== 调试信息结束 ===\n")
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@main.route('/batch_update_status', methods=['POST'])
@csrf.exempt
@login_required
def batch_update_status():
    """批量修改订单状态（管理员可用）"""
    # 调试信息
    print(f"\n=== 调试信息 - 批量修改订单状态 ===")
    print(f"请求方法: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"is_json: {request.is_json}")
    print(f"request.json: {request.json}")
    print(f"request.form: {dict(request.form)}")
    print(f"request.data: {request.data}")
    print(f"当前用户: {current_user.username if current_user.is_authenticated else 'None'}")
    print(f"用户权限: {current_user.can(Permission.ADMIN) if current_user.is_authenticated else 'None'}")
    
    # 检查权限：只有管理员才能修改状态
    if not current_user.can(Permission.ADMIN):
        print("错误: 权限不足")
        return jsonify({'error': '权限不足'}), 403
    
    if not request.is_json:
        print("错误: 请求不是JSON格式")
        return jsonify({'error': '请求必须是JSON格式'}), 400
    
    data = request.json
    print(f"解析的JSON数据: {data}")
    order_ids = data.get('order_ids', [])
    new_status = data.get('status')
    print(f"订单ID列表: {order_ids}")
    print(f"新状态: {new_status}")
    
    if not order_ids:
        print("错误: 缺少订单ID列表")
        return jsonify({'error': '缺少订单ID列表'}), 400
    
    if not new_status:
        print("错误: 缺少状态参数")
        return jsonify({'error': '缺少状态参数'}), 400
    
    # 验证状态值
    valid_statuses = ['已结算', '未结算', '未完成']
    if new_status not in valid_statuses:
        print(f"错误: 无效状态值 {new_status}，有效值: {valid_statuses}")
        return jsonify({'error': '无效的订单状态'}), 400
    
    try:
        # 批量更新订单状态
        updated_count = 0
        print(f"开始批量更新，订单数量: {len(order_ids)}")
        for order_id in order_ids:
            order = Order.query.get(order_id)
            if order:
                old_status = getattr(order, 'status', '无状态字段')
                order.status = new_status
                print(f"订单 {order_id} ({order.order_code}): {old_status} -> {new_status}")
                updated_count += 1
            else:
                print(f"订单 {order_id} 不存在")
        
        db.session.commit()
        print(f"批量更新成功，共更新 {updated_count} 个订单")
        print("=== 调试信息结束 ===\n")
        return jsonify({
            'success': True,
            'message': f'成功修改了 {updated_count} 个订单的状态为：{new_status}'
        })
    except Exception as e:
        db.session.rollback()
        print(f"异常错误: {str(e)}")
        print(f"异常类型: {type(e)}")
        import traceback
        print(f"异常堆栈: {traceback.format_exc()}")
        print("=== 调试信息结束 ===\n")
        return jsonify({'error': f'批量更新失败: {str(e)}'}), 500

@main.route('/batch_delete_orders', methods=['POST'])
@csrf.exempt
@login_required
def batch_delete_orders():
    """批量删除订单（管理员可用）"""
    # 检查权限：只有管理员才能批量删除
    if not current_user.can(Permission.ADMIN):
        return jsonify({'error': '权限不足'}), 403
    
    if not request.is_json:
        return jsonify({'error': '请求必须是JSON格式'}), 400
    
    data = request.json
    order_ids = data.get('order_ids', [])
    
    if not order_ids:
        return jsonify({'error': '缺少订单ID列表'}), 400
    
    try:
        deleted_count = 0
        for order_id in order_ids:
            order = Order.query.get(order_id)
            if order:
                # 删除关联的图片文件
                for image in order.images:
                    try:
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_path.replace('uploads/', ''))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        current_app.logger.error(f"删除图片文件失败: {e}")
                
                db.session.delete(order)
                deleted_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'成功删除了 {deleted_count} 个订单'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'批量删除失败: {str(e)}'}), 500


@main.route('/backup/database', methods=['POST'])
@login_required
@admin_required
def backup_database():
    """备份数据库"""
    try:
        # 获取当前时间戳
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # 获取当前数据库文件路径
        database_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if database_uri.startswith('sqlite:///'):
            db_path = database_uri.replace('sqlite:///', '')
        else:
            return jsonify({'error': '只支持SQLite数据库备份'}), 400
        
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            return jsonify({'error': '数据库文件不存在'}), 404
        
        # 创建备份文件名
        db_dir = os.path.dirname(db_path)
        db_name = os.path.splitext(os.path.basename(db_path))[0]
        backup_filename = f"{db_name}_{timestamp}.sqlite"
        backup_path = os.path.join(db_dir, backup_filename)
        
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        
        # 检查备份文件是否创建成功
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            return jsonify({
                'success': True,
                'message': f'数据库备份成功',
                'backup_file': backup_filename,
                'backup_size': f'{backup_size / 1024:.2f} KB',
                'timestamp': timestamp
            })
        else:
            return jsonify({'error': '备份文件创建失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'备份失败: {str(e)}'}), 500