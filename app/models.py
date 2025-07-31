from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import json

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.VIEW_OWN, Permission.SUBMIT],
            'Admin': [Permission.VIEW_ALL, Permission.SUBMIT, Permission.MANAGE_FIELDS],
            'SuperAdmin': [Permission.VIEW_ALL, Permission.SUBMIT, Permission.MANAGE_FIELDS, Permission.ADMIN]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()
    
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permissions(self):
        self.permissions = 0
    
    def has_permission(self, perm):
        return self.permissions & perm == perm
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Permission:
    VIEW_OWN = 1       # 查看自己的订单
    SUBMIT = 2         # 提交订单
    VIEW_ALL = 4       # 查看所有订单
    MANAGE_FIELDS = 8  # 管理订单字段
    ADMIN = 16         # 管理用户和角色

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    orders = db.relationship('Order', backref='creator', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == 'admin@example.com':
                self.role = Role.query.filter_by(name='SuperAdmin').first()
            else:
                self.role = Role.query.filter_by(default=True).first()
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)
    
    def is_administrator(self):
        return self.can(Permission.ADMIN)
    
    def __repr__(self):
        return f'<User {self.username}>'

class OrderField(db.Model):
    __tablename__ = 'order_fields'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    field_type = db.Column(db.String(32))  # text, number, date, image, select
    required = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer)  # 显示顺序
    is_default = db.Column(db.Boolean, default=False)  # 是否为默认字段
    
    @staticmethod
    def insert_default_fields():
        default_fields = [
            {'name': 'wechat_name', 'field_type': 'text', 'required': True, 'order': 1, 'is_default': True},
            {'name': 'wechat_id', 'field_type': 'text', 'required': False, 'order': 2, 'is_default': True},
            {'name': 'phone', 'field_type': 'text', 'required': True, 'order': 3, 'is_default': True},
            {'name': 'order_info', 'field_type': 'text', 'required': False, 'order': 4, 'is_default': True},
            {'name': 'completion_time', 'field_type': 'date', 'required': False, 'order': 5, 'is_default': True},
            {'name': 'quantity', 'field_type': 'number', 'required': False, 'order': 6, 'is_default': True},
            {'name': 'amount', 'field_type': 'number', 'required': False, 'order': 7, 'is_default': True},
            {'name': 'notes', 'field_type': 'text', 'required': False, 'order': 8, 'is_default': True}
        ]
        
        for field_data in default_fields:
            field = OrderField.query.filter_by(name=field_data['name']).first()
            if field is None:
                field = OrderField(**field_data)
                db.session.add(field)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<OrderField {self.name}>'

class OrderType(db.Model):
    __tablename__ = 'order_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='order_type', lazy='dynamic')
    
    @staticmethod
    def insert_default_types():
        default_types = [
            {'name': '标准订单', 'description': '标准订单类型'},
            {'name': '优惠订单', 'description': '享受优惠的订单类型'},
            {'name': '加急订单', 'description': '需要加急处理的订单类型'},
            {'name': '特殊订单', 'description': '特殊要求的订单类型'},
            {'name': '测试订单', 'description': '用于测试的订单类型'}
        ]
        
        for type_data in default_types:
            order_type = OrderType.query.filter_by(name=type_data['name']).first()
            if order_type is None:
                order_type = OrderType(**type_data)
                db.session.add(order_type)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<OrderType {self.name}>'

class OrderImage(db.Model):
    __tablename__ = 'order_images'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    image_path = db.Column(db.String(256))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(64), unique=True, index=True)
    wechat_name = db.Column(db.String(64))
    wechat_id = db.Column(db.String(64))
    phone = db.Column(db.String(20), nullable=False)  # 手机号，必填
    order_info = db.Column(db.Text())
    completion_time = db.Column(db.DateTime)
    quantity = db.Column(db.Integer)
    amount = db.Column(db.Float)
    notes = db.Column(db.Text())  # 备注字段
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    order_type_id = db.Column(db.Integer, db.ForeignKey('order_types.id'))
    # 订单状态字段
    status = db.Column(db.String(20), default='未完成')  # 订单状态：未完成、已结算、未结算
    images = db.relationship('OrderImage', backref='order', lazy='dynamic')
    # 存储自定义字段的值
    custom_fields = db.Column(db.Text())
    
    def set_custom_field(self, field_name, value):
        if self.custom_fields is None:
            self.custom_fields = '{}'
        try:
            fields = json.loads(self.custom_fields)
        except (json.JSONDecodeError, TypeError):
            fields = {}
        
        # 验证字段名和值
        if not isinstance(field_name, str) or len(field_name) > 64:
            raise ValueError("Invalid field name")
        
        # 限制值的长度和类型
        if isinstance(value, str) and len(value) > 1000:
            raise ValueError("Field value too long")
        
        fields[field_name] = value
        self.custom_fields = json.dumps(fields, ensure_ascii=False)
    
    def get_custom_field(self, field_name):
        if self.custom_fields is None:
            return None
        try:
            fields = json.loads(self.custom_fields)
            return fields.get(field_name)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_code': self.order_code,
            'wechat_name': self.wechat_name,
            'wechat_id': self.wechat_id,
            'phone': self.phone,
            'order_info': self.order_info,
            'completion_time': self.completion_time.isoformat() if self.completion_time else None,
            'quantity': self.quantity,
            'amount': self.amount,
            'notes': self.notes,
            'create_time': self.create_time.isoformat(),
            'user_id': self.user_id,
            'order_type_id': self.order_type_id,
            'status': self.status,
            'creator': self.creator.username if self.creator else None,
            'order_type': self.order_type.name if self.order_type else None
        }
    
    def __repr__(self):
        return f'<Order {self.order_code}>'

class WechatUser(db.Model):
    __tablename__ = 'wechat_users'
    id = db.Column(db.Integer, primary_key=True)
    wechat_name = db.Column(db.String(64), nullable=False)
    wechat_id = db.Column(db.String(64), nullable=True, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(64))
    address = db.Column(db.String(256))
    avatar = db.Column(db.String(200))
    payment_qr_code = db.Column(db.String(200))
    notes = db.Column(db.Text())
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WechatUser {self.wechat_name}>'
    
    def get_orders(self, start_date=None, end_date=None, order_type_id=None):
        """获取用户的订单"""
        from sqlalchemy import and_
        
        query = Order.query.filter(Order.wechat_name == self.wechat_name)
        
        if start_date:
            query = query.filter(Order.create_time >= start_date)
        if end_date:
            query = query.filter(Order.create_time <= end_date)
        if order_type_id:
            query = query.filter(Order.order_type_id == order_type_id)
        
        return query.order_by(Order.create_time.desc()).all()
    
    def get_order_stats(self, start_date=None, end_date=None):
        """获取用户订单统计"""
        from sqlalchemy import func
        
        query = Order.query.filter(Order.wechat_name == self.wechat_name)
        
        if start_date:
            query = query.filter(Order.create_time >= start_date)
        if end_date:
            query = query.filter(Order.create_time <= end_date)
        
        stats = query.with_entities(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.amount).label('total_amount'),
            func.avg(Order.amount).label('avg_amount'),
            func.sum(Order.quantity).label('total_quantity')
        ).first()
        
        return {
            'total_orders': stats.total_orders or 0,
            'total_amount': float(stats.total_amount or 0),
            'avg_amount': float(stats.avg_amount or 0),
            'total_quantity': stats.total_quantity or 0
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))