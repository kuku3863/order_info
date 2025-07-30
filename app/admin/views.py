from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
import json
from . import admin
from .. import db, csrf
from ..models import User, Role, OrderField, Order, Permission, OrderType, WechatUser
from ..forms import UserForm, OrderFieldForm, DateRangeForm, WechatUserForm
from ..decorators import admin_required, permission_required

@admin.route('/collect-wechat-users', methods=['POST'])
@admin_required
def collect_wechat_users():
    """从订单中收集微信用户信息（基于手机号管理）"""
    try:
        # 获取所有有手机号的订单
        orders = Order.query.filter(Order.phone.isnot(None), Order.phone != '').all()
        
        # 按手机号分组
        phone_orders = {}
        for order in orders:
            if order.phone.strip():  # 确保手机号不为空字符串
                if order.phone not in phone_orders:
                    phone_orders[order.phone] = []
                phone_orders[order.phone].append(order)
        
        created_count = 0
        updated_count = 0
        
        for phone, orders_list in phone_orders.items():
            # 检查是否已存在该手机号的微信用户
            existing_user = WechatUser.query.filter_by(phone=phone).first()
            
            # 从订单中获取最佳的微信名和微信号
            best_wechat_name = None
            best_wechat_id = None
            
            for order in orders_list:
                if order.wechat_name and order.wechat_name.strip() and not best_wechat_name:
                    best_wechat_name = order.wechat_name.strip()
                if order.wechat_id and order.wechat_id.strip() and not best_wechat_id:
                    best_wechat_id = order.wechat_id.strip()
            
            if existing_user:
                # 更新现有用户信息
                updated = False
                if best_wechat_name and (not existing_user.wechat_name or not existing_user.wechat_name.strip()):
                    existing_user.wechat_name = best_wechat_name
                    updated = True
                if best_wechat_id and (not existing_user.wechat_id or not existing_user.wechat_id.strip()):
                    existing_user.wechat_id = best_wechat_id
                    updated = True
                
                if updated:
                    existing_user.update_time = datetime.utcnow()
                    updated_count += 1
            else:
                # 只有当至少有微信名或微信号时才创建新用户
                if best_wechat_name or best_wechat_id:
                    new_user = WechatUser(
                        wechat_name=best_wechat_name,
                        wechat_id=best_wechat_id,
                        phone=phone
                    )
                    db.session.add(new_user)
                    created_count += 1
        
        db.session.commit()
        flash(f'成功收集微信用户信息：新增 {created_count} 个，更新 {updated_count} 个', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'收集微信用户信息时出错: {str(e)}', 'error')
    
    return redirect(url_for('admin.wechat_user_list'))

@admin.route('/refresh-wechat-users', methods=['POST'])
@admin_required
def refresh_wechat_users():
    """刷新所有微信用户信息（基于手机号管理）"""
    try:
        # 获取所有微信用户
        wechat_users = WechatUser.query.all()
        updated_count = 0
        cleaned_count = 0
        
        for wechat_user in wechat_users:
            # 检查是否为无效用户（手机号和微信号都为空）
            if (not wechat_user.phone or not wechat_user.phone.strip()) and \
               (not wechat_user.wechat_id or not wechat_user.wechat_id.strip()):
                # 删除无效用户
                db.session.delete(wechat_user)
                cleaned_count += 1
                continue
            
            # 根据手机号查找最新的订单信息
            latest_order = None
            if wechat_user.phone and wechat_user.phone.strip():
                latest_order = Order.query.filter_by(phone=wechat_user.phone).order_by(Order.create_time.desc()).first()
            
            if latest_order:
                updated = False
                # 更新微信名（如果订单中有更新的信息）
                if latest_order.wechat_name and latest_order.wechat_name != wechat_user.wechat_name:
                    wechat_user.wechat_name = latest_order.wechat_name
                    updated = True
                # 更新微信号（如果用户没有微信号但订单中有）
                if latest_order.wechat_id and (not wechat_user.wechat_id or not wechat_user.wechat_id.strip()):
                    wechat_user.wechat_id = latest_order.wechat_id
                    updated = True
                # 更新手机号（如果用户没有手机号但订单中有）
                if latest_order.phone and (not wechat_user.phone or not wechat_user.phone.strip()):
                    wechat_user.phone = latest_order.phone
                    updated = True
                
                if updated:
                    wechat_user.update_time = datetime.utcnow()
                    updated_count += 1
        
        db.session.commit()
        
        if cleaned_count > 0:
            flash(f'成功刷新了 {updated_count} 个微信用户的信息，清理了 {cleaned_count} 个无效用户', 'success')
        else:
            flash(f'成功刷新了 {updated_count} 个微信用户的信息', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'刷新微信用户信息时出错: {str(e)}', 'error')
    
    return redirect(url_for('admin.wechat_user_list'))

@admin.before_request
@login_required
def before_request():
    # 检查是否有管理员权限
    if not current_user.can(Permission.MANAGE_FIELDS) and not current_user.can(Permission.ADMIN):
        abort(403)

@admin.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('admin/user_list.html', users=users)

@admin.route('/user/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            role_id=form.role.data
        )
        if form.password.data:
            user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('用户已创建成功')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/edit_user.html', form=form)

@admin.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.role_id = form.role.data
        if form.password.data:
            user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('用户已更新成功')
        return redirect(url_for('admin.user_list'))
    form.email.data = user.email
    form.username.data = user.username
    form.role.data = user.role_id
    return render_template('admin/edit_user.html', form=form, user=user)

@admin.route('/user/delete/<int:id>', methods=['POST'])
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('不能删除自己的账户')
        return redirect(url_for('admin.user_list'))
    db.session.delete(user)
    db.session.commit()
    flash('用户已删除')
    return redirect(url_for('admin.user_list'))

@admin.route('/fields')
@permission_required(Permission.MANAGE_FIELDS)
def field_list():
    fields = OrderField.query.order_by(OrderField.order).all()
    return render_template('admin/field_list.html', fields=fields)

@admin.route('/field/new', methods=['GET', 'POST'])
@permission_required(Permission.MANAGE_FIELDS)
def new_field():
    form = OrderFieldForm()
    if form.validate_on_submit():
        field = OrderField(
            name=form.name.data,
            field_type=form.field_type.data,
            required=form.required.data,
            order=form.order.data,
            is_default=False
        )
        db.session.add(field)
        db.session.commit()
        flash('字段已创建成功')
        return redirect(url_for('admin.field_list'))
    return render_template('admin/edit_field.html', form=form)

@admin.route('/field/edit/<int:id>', methods=['GET', 'POST'])
@permission_required(Permission.MANAGE_FIELDS)
def edit_field(id):
    field = OrderField.query.get_or_404(id)
    if field.is_default:
        flash('默认字段不能编辑')
        return redirect(url_for('admin.field_list'))
    
    form = OrderFieldForm()
    if form.validate_on_submit():
        field.name = form.name.data
        field.field_type = form.field_type.data
        field.required = form.required.data
        field.order = form.order.data
        db.session.add(field)
        db.session.commit()
        flash('字段已更新成功')
        return redirect(url_for('admin.field_list'))
    
    form.name.data = field.name
    form.field_type.data = field.field_type
    form.required.data = field.required
    form.order.data = field.order
    return render_template('admin/edit_field.html', form=form, field=field)

@admin.route('/field/delete/<int:id>', methods=['POST'])
@permission_required(Permission.MANAGE_FIELDS)
def delete_field(id):
    field = OrderField.query.get_or_404(id)
    if field.is_default:
        flash('默认字段不能删除')
        return redirect(url_for('admin.field_list'))
    
    db.session.delete(field)
    db.session.commit()
    flash('字段已删除')
    return redirect(url_for('admin.field_list'))

@admin.route('/statistics', methods=['GET', 'POST'])
@permission_required(Permission.VIEW_ALL)
def statistics():
    form = DateRangeForm()
    
    # 默认显示最近7天的数据
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
    else:
        form.start_date.data = start_date
        form.end_date.data = end_date
    
    # 查询日期范围内的订单
    orders = Order.query.filter(
        func.date(Order.completion_time) >= start_date,
        func.date(Order.completion_time) <= end_date
    ).all()
    
    # 按日期分组统计
    daily_stats = {}
    for order in orders:
        date_str = order.completion_time.strftime('%Y-%m-%d')
        if date_str not in daily_stats:
            daily_stats[date_str] = {
                'count': 0,
                'total_amount': 0,
                'total_quantity': 0
            }
        daily_stats[date_str]['count'] += 1
        daily_stats[date_str]['total_amount'] += (order.amount or 0)
        daily_stats[date_str]['total_quantity'] += order.quantity
    
    # 计算总计
    total_stats = {
        'total_orders': len(orders),
        'total_amount': sum((order.amount or 0) for order in orders),
        'total_quantity': sum(order.quantity for order in orders),
        'avg_amount': sum((order.amount or 0) for order in orders) / len(orders) if orders else 0
    }
    
    # 按用户分组统计
    user_stats = {}
    for order in orders:
        user_id = order.user_id
        username = order.creator.username if order.creator else f"用户ID: {user_id}"
        if username not in user_stats:
            user_stats[username] = {
                'count': 0,
                'total_amount': 0
            }
        user_stats[username]['count'] += 1
        user_stats[username]['total_amount'] += (order.amount or 0)
    
    # 准备图表数据
    dates = []
    counts = []
    amounts = []
    
    # 确保日期范围内的每一天都有数据
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        dates.append(date_str)
        if date_str in daily_stats:
            counts.append(daily_stats[date_str]['count'])
            amounts.append(daily_stats[date_str]['total_amount'])
        else:
            counts.append(0)
            amounts.append(0)
        current_date += timedelta(days=1)
    
    chart_data = {
        'dates': dates,
        'counts': counts,
        'amounts': amounts
    }
    
    return render_template('admin/statistics.html', 
                           form=form,
                           daily_stats=daily_stats,
                           total_stats=total_stats,
                           user_stats=user_stats,
                           chart_data=json.dumps(chart_data))

@admin.route('/api/statistics/daily')
@permission_required(Permission.VIEW_ALL)
def api_daily_statistics():
    # 获取查询参数
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # 默认最近30天
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=29)
        
        # 查询日期范围内的订单
        orders = Order.query.filter(
            func.date(Order.completion_time) >= start_date,
            func.date(Order.completion_time) <= end_date
        ).all()
        
        # 按日期分组统计
        daily_stats = {}
        for order in orders:
            date_str = order.completion_time.strftime('%Y-%m-%d')
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    'count': 0,
                    'total_amount': 0
                }
            daily_stats[date_str]['count'] += 1
            daily_stats[date_str]['total_amount'] += (order.amount or 0)
        
        # 确保日期范围内的每一天都有数据
        result = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in daily_stats:
                result.append({
                    'date': date_str,
                    'count': daily_stats[date_str]['count'],
                    'amount': daily_stats[date_str]['total_amount']
                })
            else:
                result.append({
                    'date': date_str,
                    'count': 0,
                    'amount': 0
                })
            current_date += timedelta(days=1)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@admin.route('/order-types')
@admin_required
def order_type_list():
    order_types = OrderType.query.order_by(OrderType.create_time.desc()).all()
    return render_template('admin/order_type_list.html', order_types=order_types)

@admin.route('/order-type/new', methods=['GET', 'POST'])
@csrf.exempt
@admin_required
def new_order_type():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('订单类型名称不能为空')
            return render_template('admin/edit_order_type.html', order_type=None)
        
        # 检查是否已存在
        existing = OrderType.query.filter_by(name=name).first()
        if existing:
            flash('该订单类型已存在')
            return render_template('admin/edit_order_type.html', order_type=None)
        
        order_type = OrderType(
            name=name,
            description=description
        )
        db.session.add(order_type)
        db.session.commit()
        flash('订单类型已创建成功')
        return redirect(url_for('admin.order_type_list'))
    
    return render_template('admin/edit_order_type.html', order_type=None)

@admin.route('/order-type/edit/<int:id>', methods=['GET', 'POST'])
@csrf.exempt
@admin_required
def edit_order_type(id):
    order_type = OrderType.query.get_or_404(id)
    
    if request.method == 'POST':
        print(f"POST request received for order_type {id}")
        print(f"Form data: {request.form}")
        
        name = request.form.get('name')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        print(f"Parsed data - name: {name}, description: {description}, is_active: {is_active}")
        
        if not name:
            flash('订单类型名称不能为空')
            return render_template('admin/edit_order_type.html', order_type=order_type)
        
        # 检查是否已存在（排除当前记录）
        existing = OrderType.query.filter_by(name=name).filter(OrderType.id != id).first()
        if existing:
            flash('该订单类型已存在')
            return render_template('admin/edit_order_type.html', order_type=order_type)
        
        try:
            order_type.name = name
            order_type.description = description
            order_type.is_active = is_active
            db.session.commit()
            flash('订单类型已更新成功')
            return redirect(url_for('admin.order_type_list'))
        except Exception as e:
            print(f"Database error: {e}")
            db.session.rollback()
            flash('更新失败，请重试')
            return render_template('admin/edit_order_type.html', order_type=order_type)
    
    return render_template('admin/edit_order_type.html', order_type=order_type)

@admin.route('/order-type/delete/<int:id>', methods=['POST'])
@admin_required
def delete_order_type(id):
    order_type = OrderType.query.get_or_404(id)
    
    # 检查是否有关联的订单
    if order_type.orders.count() > 0:
        flash('该订单类型下还有订单，不能删除')
        return redirect(url_for('admin.order_type_list'))
    
    db.session.delete(order_type)
    db.session.commit()
    flash('订单类型已删除')
    return redirect(url_for('admin.order_type_list'))

@admin.route('/wechat-users')
@admin_required
def wechat_user_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = WechatUser.query
    if search:
        query = query.filter(
            db.or_(
                WechatUser.wechat_name.contains(search),
                WechatUser.wechat_id.contains(search),
                WechatUser.phone.contains(search)
            )
        )
    
    wechat_users = query.order_by(WechatUser.create_time.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 检查是否有可收集的微信用户（基于手机号）
    uncollected_count = Order.query.filter(
        Order.phone.isnot(None),
        Order.phone != '',
        ~Order.phone.in_(
            db.session.query(WechatUser.phone).filter(WechatUser.phone.isnot(None))
        )
    ).count()
    
    return render_template('admin/wechat_user_list.html', 
                         wechat_users=wechat_users, 
                         search=search,
                         uncollected_count=uncollected_count)

@admin.route('/wechat-user/<int:id>')
@admin_required
def wechat_user_detail(id):
    wechat_user = WechatUser.query.get_or_404(id)
    
    # 获取筛选参数
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    order_type_id = request.args.get('order_type_id', type=int)
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    
    # 获取订单
    orders = wechat_user.get_orders(start_date, end_date, order_type_id)
    
    # 获取统计信息
    stats = wechat_user.get_order_stats(start_date, end_date)
    
    # 获取所有订单类型
    order_types = OrderType.query.filter_by(is_active=True).all()
    
    return render_template('admin/wechat_user_detail.html',
                         wechat_user=wechat_user,
                         orders=orders,
                         stats=stats,
                         order_types=order_types,
                         current_filters={
                             'start_date': start_date_str,
                             'end_date': end_date_str,
                             'order_type_id': order_type_id
                         })

@admin.route('/wechat-user/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_wechat_user(id):
    """编辑微信用户"""
    wechat_user = WechatUser.query.get_or_404(id)
    form = WechatUserForm(wechat_user=wechat_user)
    
    if form.validate_on_submit():
        try:
            # 更新基本信息
            wechat_user.wechat_name = form.wechat_name.data
            wechat_user.wechat_id = form.wechat_id.data
            wechat_user.phone = form.phone.data if form.phone.data else None
            wechat_user.email = form.email.data if form.email.data else None
            wechat_user.address = form.address.data if form.address.data else None
            wechat_user.notes = form.notes.data if form.notes.data else None
            
            # 处理头像上传
            if form.avatar.data:
                from ..main.views import save_image
                avatar_path = save_image(form.avatar.data, 'avatars')
                if avatar_path:
                    wechat_user.avatar = avatar_path
            
            # 处理付款码上传
            if form.payment_qr_code.data:
                from ..main.views import save_image
                qr_path = save_image(form.payment_qr_code.data, 'qr_codes')
                if qr_path:
                    wechat_user.payment_qr_code = qr_path
            
            wechat_user.update_time = datetime.utcnow()
            db.session.commit()
            flash('微信用户信息更新成功', 'success')
            return redirect(url_for('admin.wechat_user_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'error')
    
    # 预填充表单数据
    if request.method == 'GET':
        form.wechat_name.data = wechat_user.wechat_name
        form.wechat_id.data = wechat_user.wechat_id
        form.phone.data = wechat_user.phone
        form.email.data = wechat_user.email
        form.address.data = wechat_user.address
        form.notes.data = wechat_user.notes
    
    return render_template('admin/edit_wechat_user.html', wechat_user=wechat_user, form=form)

@admin.route('/wechat-user/delete/<int:id>', methods=['POST'])
@csrf.exempt
@admin_required
def delete_wechat_user(id):
    wechat_user = WechatUser.query.get_or_404(id)
    
    # 获取关联的订单（优先根据手机号，其次根据微信号）
    related_orders = []
    if wechat_user.phone and wechat_user.phone.strip():
        related_orders.extend(Order.query.filter_by(phone=wechat_user.phone).all())
    if wechat_user.wechat_id and wechat_user.wechat_id.strip():
        # 避免重复添加同一订单
        wechat_orders = Order.query.filter_by(wechat_id=wechat_user.wechat_id).all()
        for order in wechat_orders:
            if order not in related_orders:
                related_orders.append(order)
    orders_count = len(related_orders)
    
    # 检查是否确认删除关联订单
    force_delete = request.form.get('force_delete') == 'true'
    
    if orders_count > 0 and not force_delete:
        # 返回JSON响应，包含订单信息
        return jsonify({
            'success': False,
            'has_orders': True,
            'orders_count': orders_count,
            'message': f'该微信用户下还有 {orders_count} 个订单'
        })
    
    try:
        # 删除关联的订单图片
        for order in related_orders:
            for image in order.images:
                db.session.delete(image)
        
        # 删除关联的订单
        for order in related_orders:
            db.session.delete(order)
        
        # 删除微信用户
        db.session.delete(wechat_user)
        db.session.commit()
        
        if orders_count > 0:
            flash(f'微信用户及其 {orders_count} 个关联订单已删除', 'success')
        else:
            flash('微信用户已删除', 'success')
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        })