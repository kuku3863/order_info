# 优化版本的数据库模型
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

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
            'Moderator': [Permission.VIEW_OWN, Permission.SUBMIT, Permission.VIEW_ALL],
            'Administrator': [Permission.VIEW_OWN, Permission.SUBMIT, Permission.VIEW_ALL, Permission.MANAGE_FIELDS, Permission.ADMIN]
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
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
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
    field_type = db.Column(db.String(32))  # text, number, date, image
    required = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer)  # 显示顺序
    is_default = db.Column(db.Boolean, default=False)  # 是否为默认字段

    @staticmethod
    def insert_default_fields():
        default_fields = [
            {'name': '微信名称', 'field_type': 'text', 'required': True, 'order': 1, 'is_default': True},
            {'name': '微信ID', 'field_type': 'text', 'required': False, 'order': 2, 'is_default': True},
            {'name': '手机号', 'field_type': 'text', 'required': True, 'order': 3, 'is_default': True},
            {'name': '订单信息', 'field_type': 'text', 'required': True, 'order': 4, 'is_default': True},
            {'name': '完成时间', 'field_type': 'date', 'required': False, 'order': 5, 'is_default': True},
            {'name': '数量', 'field_type': 'number', 'required': False, 'order': 6, 'is_default': True},
            {'name': '金额', 'field_type': 'number', 'required': False, 'order': 7, 'is_default': True},
            {'name': '备注', 'field_type': 'text', 'required': False, 'order': 8, 'is_default': True},
        ]
        
        for field_data in default_fields:
            field = OrderField.query.filter_by(name=field_data['name']).first()
            if field is None:
                field = OrderField(**field_data)
                db.session.add(field)
        db.session.commit()

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
            {'name': '普通订单', 'description': '标准订单类型'},
            {'name': '加急订单', 'description': '需要优先处理的订单'},
            {'name': '批量订单', 'description': '大批量订单'},
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
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), index=True)
    image_path = db.Column(db.String(256))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(64), unique=True, index=True)
    wechat_name = db.Column(db.String(64), index=True)  # 添加索引
    wechat_id = db.Column(db.String(64), index=True)    # 添加索引
    phone = db.Column(db.String(20), nullable=False, index=True)  # 添加索引
    order_info = db.Column(db.Text())
    completion_time = db.Column(db.DateTime, index=True)  # 添加索引
    quantity = db.Column(db.Integer)
    amount = db.Column(db.Float)
    notes = db.Column(db.Text())
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # 添加索引
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)  # 添加索引
    order_type_id = db.Column(db.Integer, db.ForeignKey('order_types.id'), index=True)  # 添加索引
    status = db.Column(db.String(20), default='未完成', index=True)  # 添加索引
    images = db.relationship('OrderImage', backref='order', lazy='dynamic')
    custom_fields = db.Column(db.Text())

    # 添加复合索引以优化常见查询
    __table_args__ = (
        db.Index('idx_user_completion_time', 'user_id', 'completion_time'),
        db.Index('idx_user_create_time', 'user_id', 'create_time'),
        db.Index('idx_status_completion_time', 'status', 'completion_time'),
        db.Index('idx_wechat_phone', 'wechat_name', 'phone'),
        db.Index('idx_amount_status', 'amount', 'status'),
    )

    def set_custom_field(self, field_name, value):
        fields = {}
        if self.custom_fields:
            fields = json.loads(self.custom_fields)
        fields[field_name] = value
        self.custom_fields = json.dumps(fields)
    
    def get_custom_field(self, field_name):
        if not self.custom_fields:
            return None
        fields = json.loads(self.custom_fields)
        return fields.get(field_name)
    
    def to_dict(self):
        data = {
            'id': self.id,
            'order_code': self.order_code,
            'wechat_name': self.wechat_name,
            'wechat_id': self.wechat_id,
            'order_info': self.order_info,
            'completion_time': self.completion_time.strftime('%Y-%m-%d %H:%M:%S') if self.completion_time else None,
            'quantity': self.quantity,
            'amount': self.amount,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': self.user_id,
            'username': self.creator.username if self.creator else None,
            'images': [{'id': img.id, 'path': img.image_path} for img in self.images]
        }
        
        if self.custom_fields:
            custom_data = json.loads(self.custom_fields)
            for key, value in custom_data.items():
                data[key] = value
                
        return data

    @classmethod
    def get_optimized_query(cls, user_id=None, start_date=None, end_date=None, 
                           search_type=None, search_value=None, include_relations=True):
        """
        优化的查询方法，支持预加载关联数据
        """
        query = cls.query
        
        # 用户筛选
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        
        # 日期筛选 - 优化版本
        if start_date:
            query = query.filter(cls.completion_time >= start_date)
        if end_date:
            query = query.filter(cls.completion_time <= end_date)
        
        # 搜索筛选
        if search_value and search_type:
            if search_type == 'order_code':
                query = query.filter(cls.order_code.contains(search_value))
            elif search_type == 'wechat_name':
                query = query.filter(cls.wechat_name.contains(search_value))
            elif search_type == 'wechat_id':
                query = query.filter(cls.wechat_id.contains(search_value))
            elif search_type == 'phone':
                query = query.filter(cls.phone.contains(search_value))
        
        # 预加载关联数据以减少N+1查询
        if include_relations:
            query = query.options(
                db.joinedload(cls.creator),
                db.joinedload(cls.order_type),
                db.joinedload(cls.images)
            )
        
        return query

    @classmethod
    def get_statistics(cls, user_id=None, start_date=None, end_date=None):
        """
        优化的统计查询方法
        """
        query = cls.query
        
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        if start_date:
            query = query.filter(cls.completion_time >= start_date)
        if end_date:
            query = query.filter(cls.completion_time <= end_date)
        
        # 使用单次查询获取多个统计值
        stats = query.with_entities(
            db.func.count(cls.id).label('total_orders'),
            db.func.sum(cls.amount).label('total_amount'),
            db.func.avg(cls.amount).label('avg_amount'),
            db.func.sum(cls.quantity).label('total_quantity')
        ).first()
        
        return {
            'total_orders': stats.total_orders or 0,
            'total_amount': stats.total_amount or 0,
            'avg_amount': stats.avg_amount or 0,
            'total_quantity': stats.total_quantity or 0
        }

class WechatUser(db.Model):
    __tablename__ = 'wechat_users'
    id = db.Column(db.Integer, primary_key=True)
    wechat_name = db.Column(db.String(64), nullable=False, index=True)  # 添加索引
    wechat_id = db.Column(db.String(64), nullable=True, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)  # 添加索引
    email = db.Column(db.String(64))
    address = db.Column(db.String(256))
    avatar = db.Column(db.String(200))
    payment_qr_code = db.Column(db.String(200))
    notes = db.Column(db.Text())
    create_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # 添加索引
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 添加复合索引
    __table_args__ = (
        db.Index('idx_wechat_phone_lookup', 'wechat_name', 'phone'),
    )
    
    def __repr__(self):
        return f'<WechatUser {self.wechat_name}({self.wechat_id})>'
    
    def get_orders(self, start_date=None, end_date=None, order_type_id=None):
        """优化的订单查询方法"""
        if not self.phone:
            return []
        
        query = Order.query.filter_by(phone=self.phone)
        
        if start_date:
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time >= start_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time >= start_date)
                )
            )
        if end_date:
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time <= end_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time <= end_date)
                )
            )
        if order_type_id:
            query = query.filter_by(order_type_id=order_type_id)
            
        return query.order_by(Order.create_time.desc())
    
    def get_order_stats(self, start_date=None, end_date=None):
        """优化的订单统计方法"""
        if not self.phone:
            return {
                'total_orders': 0,
                'total_amount': 0,
                'avg_amount': 0
            }
        
        query = Order.query.filter_by(phone=self.phone)
        
        if start_date:
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time >= start_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time >= start_date)
                )
            )
        if end_date:
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time <= end_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time <= end_date)
                )
            )
        
        # 使用单次查询获取统计值
        stats = query.with_entities(
            db.func.count(Order.id).label('total_orders'),
            db.func.sum(Order.amount).label('total_amount'),
            db.func.avg(Order.amount).label('avg_amount')
        ).first()
        
        return {
            'total_orders': stats.total_orders or 0,
            'total_amount': stats.total_amount or 0,
            'avg_amount': stats.avg_amount or 0
        } 