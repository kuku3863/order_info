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
    field_type = db.Column(db.String(32))  # text, number, date, image
    required = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer)  # 显示顺序
    is_default = db.Column(db.Boolean, default=False)  # 是否为默认字段
    
    @staticmethod
    def insert_default_fields():
        default_fields = [
            {'name': '订单编码', 'field_type': 'text', 'required': True, 'order': 1, 'is_default': True},
            {'name': '微信名', 'field_type': 'text', 'required': True, 'order': 2, 'is_default': True},
            {'name': '微信号', 'field_type': 'text', 'required': True, 'order': 3, 'is_default': True},
            {'name': '订单信息', 'field_type': 'text', 'required': True, 'order': 4, 'is_default': True},
            {'name': '完成时间', 'field_type': 'date', 'required': True, 'order': 5, 'is_default': True},
            {'name': '数量', 'field_type': 'number', 'required': True, 'order': 6, 'is_default': True},
            {'name': '图片', 'field_type': 'image', 'required': False, 'order': 7, 'is_default': True},
            {'name': '金额', 'field_type': 'number', 'required': False, 'order': 8, 'is_default': True}
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
            {'name': '灯箱', 'description': '灯箱制作订单'},
            {'name': '海报', 'description': '海报设计制作订单'},
            {'name': '三折页', 'description': '三折页宣传册订单'},
            {'name': '详情页', 'description': '详情页设计订单'},
            {'name': '其他', 'description': '其他类型订单'}
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
        
        # 添加自定义字段
        if self.custom_fields:
            custom_data = json.loads(self.custom_fields)
            for key, value in custom_data.items():
                data[key] = value
                
        return data

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
        return f'<WechatUser {self.wechat_name}({self.wechat_id})>'
    
    def get_orders(self, start_date=None, end_date=None, order_type_id=None):
        """获取该微信用户的订单"""
        # 以手机号为主要标识查找订单
        if self.phone:
            query = Order.query.filter_by(phone=self.phone)
        else:
            # 如果没有手机号，返回空查询
            return []
        
        if start_date:
            # 优先按完成时间筛选，如果完成时间为空则按创建时间筛选
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time >= start_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time >= start_date)
                )
            )
        if end_date:
            # 优先按完成时间筛选，如果完成时间为空则按创建时间筛选
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time <= end_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time <= end_date)
                )
            )
        if order_type_id:
            query = query.filter_by(order_type_id=order_type_id)
            
        return query.order_by(Order.completion_time.desc().nullslast(), Order.create_time.desc()).all()
    
    def get_order_stats(self, start_date=None, end_date=None):
        """获取该微信用户的订单统计"""
        from sqlalchemy import func
        
        # 以手机号为主要标识查找订单
        if self.phone:
            query = Order.query.filter_by(phone=self.phone)
        else:
            # 如果没有手机号，返回空统计
            return {
                'total_orders': 0,
                'total_amount': 0,
                'avg_amount': 0
            }
        
        if start_date:
            # 优先按完成时间筛选，如果完成时间为空则按创建时间筛选
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time >= start_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time >= start_date)
                )
            )
        if end_date:
            # 优先按完成时间筛选，如果完成时间为空则按创建时间筛选
            query = query.filter(
                db.or_(
                    db.and_(Order.completion_time.isnot(None), Order.completion_time <= end_date),
                    db.and_(Order.completion_time.is_(None), Order.create_time <= end_date)
                )
            )
            
        total_orders = query.count()
        total_amount = query.filter(Order.amount.isnot(None)).with_entities(func.sum(Order.amount)).scalar() or 0
        avg_amount = query.filter(Order.amount.isnot(None)).with_entities(func.avg(Order.amount)).scalar() or 0
        
        return {
            'total_orders': total_orders,
            'total_amount': total_amount,
            'avg_amount': avg_amount
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))