from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, FloatField, DateField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError, Optional, NumberRange
from .models import User, OrderField, OrderType

class LoginForm(FlaskForm):
    account = StringField('邮箱或用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名只能包含字母、数字、下划线和点')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2', message='两次输入的密码必须匹配')
    ])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2', message='两次输入的密码必须匹配')
    ])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('更改密码')

class OrderForm(FlaskForm):
    order_code = StringField('订单编码', validators=[DataRequired(), Length(1, 64)])
    wechat_name = StringField('微信名', validators=[DataRequired(), Length(1, 64)])
    wechat_id = StringField('微信号', validators=[Optional(), Length(0, 64)])  # 微信号改为非必填
    phone = StringField('手机号', validators=[Optional(), Length(0, 20)])  # 手机号必填
    order_info = TextAreaField('订单信息', validators=[DataRequired()])
    completion_time = DateField('完成时间', validators=[DataRequired()], format='%Y-%m-%d')
    quantity = IntegerField('数量', validators=[DataRequired(), NumberRange(min=1)])
    amount = FloatField('金额', validators=[Optional(), NumberRange(min=0.01)])
    notes = TextAreaField('备注', validators=[Optional()])  # 备注字段
    order_type_id = SelectField('订单类型', coerce=int, validators=[DataRequired()])
    images = FileField('图片', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片')])
    submit = SubmitField('提交订单')
    
    def __init__(self, order=None, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.order = order  # 用于编辑时的订单对象
        # 设置订单类型选择项
        active_types = OrderType.query.filter_by(is_active=True).all()
        self.order_type_id.choices = [(0, '请选择订单类型')] + [(t.id, t.name) for t in active_types]
        
        # 动态添加自定义字段
        custom_fields = OrderField.query.filter_by(is_default=False).all()
        for field in custom_fields:
            if field.field_type == 'text':
                setattr(self, field.name, StringField(field.name, 
                        validators=[DataRequired() if field.required else Optional()]))
            elif field.field_type == 'number':
                setattr(self, field.name, FloatField(field.name, 
                        validators=[DataRequired() if field.required else Optional()]))
            elif field.field_type == 'date':
                setattr(self, field.name, DateField(field.name, format='%Y-%m-%d',
                        validators=[DataRequired() if field.required else Optional()]))
    
    def validate(self, extra_validators=None):
        """重写validate方法，确保validate_phone被调用"""
        rv = super(OrderForm, self).validate(extra_validators)
        
        # 手动调用validate_phone，即使phone字段是Optional的
        if self.phone.data:
            try:
                self.validate_phone(self.phone)
            except ValidationError as e:
                self.phone.errors.append(str(e))
                rv = False
        
        return rv
    
    def validate_order_code(self, field):
        from .models import Order
        # 如果是编辑模式且订单编码没有改变，则跳过验证
        if self.order and field.data == self.order.order_code:
            return
        # 检查订单编码是否已存在
        if Order.query.filter_by(order_code=field.data).first():
            raise ValidationError('该订单编码已存在，请使用其他编码')
    
    def validate_order_type_id(self, field):
        if field.data == 0:
            raise ValidationError('请选择订单类型')
    
    def validate_phone(self, field):
        import re
        from .models import Order, WechatUser
        if not field.data:
            return
        
        # 验证手机号格式
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, field.data):
            raise ValidationError('请输入正确的手机号格式')
        
        # 如果是编辑模式且手机号没有改变，跳过重复性检查
        if self.order and field.data == self.order.phone:
            return
        
        # 检查是否有其他微信用户使用了这个手机号
        existing_wechat_user = WechatUser.query.filter_by(phone=field.data).first()
        if existing_wechat_user:
            # 如果是编辑模式，检查是否是同一个微信用户
            if self.order:
                if self.order.wechat_id != existing_wechat_user.wechat_id:
                    raise ValidationError(f'该手机号已被微信用户 "{existing_wechat_user.wechat_name}({existing_wechat_user.wechat_id})" 使用')
            else:
                # 新建订单时，检查微信号是否匹配
                wechat_id = self.wechat_id.data if hasattr(self, 'wechat_id') and self.wechat_id.data else None
                if wechat_id != existing_wechat_user.wechat_id:
                    raise ValidationError(f'该手机号已被微信用户 "{existing_wechat_user.wechat_name}({existing_wechat_user.wechat_id})" 使用')
        
        # 检查是否有其他订单使用了这个手机号（但微信号不同）
        if self.order:
            # 编辑模式：排除当前订单
            existing_order = Order.query.filter(
                Order.phone == field.data,
                Order.id != self.order.id
            ).first()
        else:
            # 新建模式
            existing_order = Order.query.filter_by(phone=field.data).first()
        
        if existing_order:
            wechat_id = self.wechat_id.data if hasattr(self, 'wechat_id') and self.wechat_id.data else None
            if existing_order.wechat_id != wechat_id:
                raise ValidationError(f'该手机号已被微信用户 "{existing_order.wechat_name}({existing_order.wechat_id})" 使用')

class OrderFieldForm(FlaskForm):
    name = StringField('字段名称', validators=[DataRequired(), Length(1, 64)])
    field_type = SelectField('字段类型', choices=[
        ('text', '文本'),
        ('number', '数字'),
        ('date', '日期'),
        ('image', '图片')
    ], validators=[DataRequired()])
    required = BooleanField('是否必填')
    order = IntegerField('显示顺序', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('保存字段')
    
    def validate_name(self, field):
        # 检查是否与默认字段冲突
        default_fields = ['order_code', 'wechat_name', 'wechat_id', 'order_info', 
                         'completion_time', 'quantity', 'amount', 'images']
        if field.data.lower() in default_fields:
            raise ValidationError('该字段名称已被系统使用')

class UserForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名只能包含字母、数字、下划线和点')
    ])
    role = SelectField('角色', coerce=int)
    password = PasswordField('密码', validators=[
        Optional(), Length(8, 128), EqualTo('password2', message='两次输入的密码必须匹配')
    ])
    password2 = PasswordField('确认密码', validators=[Optional()])
    submit = SubmitField('保存用户')
    
    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        from .models import Role
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user
    
    def validate_email(self, field):
        if self.user and field.data == self.user.email:
            return
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')
    
    def validate_username(self, field):
        if self.user and field.data == self.user.username:
            return
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

class DateRangeForm(FlaskForm):
    start_date = DateField('开始日期', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('结束日期', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('查询')
    
    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('结束日期不能早于开始日期')

class WechatUserForm(FlaskForm):
    wechat_name = StringField('微信名', validators=[DataRequired(), Length(1, 50)])
    wechat_id = StringField('微信号', validators=[Optional(), Length(0, 50)])
    phone = StringField('手机号', validators=[DataRequired(), Length(1, 20)])
    email = StringField('邮箱', validators=[Optional(), Email(), Length(0, 100)])
    address = StringField('地址', validators=[Optional(), Length(0, 200)])
    avatar = FileField('头像', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片')])
    payment_qr_code = FileField('微信付款码', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片')])
    notes = TextAreaField('备注', validators=[Optional(), Length(0, 500)])
    submit = SubmitField('保存')
    
    def __init__(self, wechat_user=None, *args, **kwargs):
        super(WechatUserForm, self).__init__(*args, **kwargs)
        self.wechat_user = wechat_user
    
    def validate(self, extra_validators=None):
        """重写validate方法，确保validate_phone被调用"""
        rv = super(WechatUserForm, self).validate(extra_validators)
        
        # 手动调用validate_phone，即使phone字段是Optional的
        if self.phone.data:
            try:
                self.validate_phone(self.phone)
            except ValidationError as e:
                self.phone.errors.append(str(e))
                rv = False
        
        return rv
    
    def validate_wechat_id(self, field):
        from .models import WechatUser
        # 如果微信号为空，跳过验证
        if not field.data:
            return
        if self.wechat_user and field.data == self.wechat_user.wechat_id:
            return
        if WechatUser.query.filter_by(wechat_id=field.data).first():
            raise ValidationError('该微信号已存在')
    
    def validate_phone(self, field):
        from .models import WechatUser, Order
        if not field.data:
            return
        
        # 检查是否有其他微信用户使用了这个手机号
        existing_wechat_user = WechatUser.query.filter_by(phone=field.data).first()
        if existing_wechat_user:
            # 如果是编辑模式且是同一个用户，允许
            if self.wechat_user and existing_wechat_user.id == self.wechat_user.id:
                return
            # 否则抛出错误
            raise ValidationError(f'该手机号已被微信用户 "{existing_wechat_user.wechat_name}({existing_wechat_user.wechat_id})" 使用')
        
        # 检查是否有订单使用了这个手机号（但微信号不同）
        existing_order = Order.query.filter_by(phone=field.data).first()
        if existing_order:
            # 获取当前表单中的微信号
            current_wechat_id = self.wechat_id.data if self.wechat_id.data else None
            # 如果当前微信号为空，允许使用任何手机号
            if current_wechat_id and existing_order.wechat_id != current_wechat_id:
                raise ValidationError(f'该手机号已被微信用户 "{existing_order.wechat_name}({existing_order.wechat_id})" 使用')