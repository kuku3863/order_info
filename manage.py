#!/usr/bin/env python
import os
import click
from app import create_app, db
from app.models import User, Role, OrderField, Order, OrderImage, Permission, OrderType, WechatUser
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, OrderField=OrderField, 
                Order=Order, OrderImage=OrderImage, Permission=Permission, OrderType=OrderType, WechatUser=WechatUser)

@app.cli.command()
def init():
    """初始化应用程序，创建角色和默认管理员账户"""
    db.create_all()
    Role.insert_roles()
    OrderField.insert_default_fields()
    OrderType.insert_default_types()
    
    # 创建管理员账户
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin is None:
        admin = User(email='admin@example.com',
                     username='admin',
                     password='admin123')
        db.session.add(admin)
        db.session.commit()
        print('管理员账户已创建，邮箱: admin@example.com, 密码: admin123')
    else:
        print('管理员账户已存在')
    
    print('应用程序初始化完成！')
    print('默认订单类型已创建：灯箱、海报、三折页、详情页、其他')
    print('图片存储路径：d:/订单查询系统/图片/')
    print('数据库：MySQL (localhost/d_order_info)')

@app.cli.command()
@click.option('--host', default='127.0.0.1', help='服务器地址')
@click.option('--port', default=5000, help='端口号')
def runserver(host, port):
    """启动开发服务器"""
    print(f'启动服务器: http://{host}:{port}')
    if host == '0.0.0.0':
        print('网络模式：局域网内其他电脑可以访问')
        print('请确保防火墙允许端口访问')
        print(f'局域网访问地址: http://你的IP:{port}')
    app.run(host=host, port=int(port), debug=True, threaded=True)

if __name__ == '__main__':
    app.run(debug=True)