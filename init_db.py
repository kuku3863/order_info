#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库表和默认数据
"""

import os
import sys

# 添加上级目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Role, User, OrderField, OrderType

def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    
    # 可能的数据库文件名
    db_files = ['data-dev.sqlite', 'data.sqlite', 'app.db']
    
    for config_name in ['development', 'production', 'default']:
        print(f"\n尝试使用配置: {config_name}")
        
        # 创建应用实例
        app = create_app(config_name)
        
        with app.app_context():
            try:
                # 创建所有表
                db.create_all()
                print(f"✓ 数据库表创建完成 (配置: {config_name})")
                
                # 插入角色数据
                Role.insert_roles()
                print("✓ 角色数据插入完成")
                
                # 插入默认订单字段
                try:
                    OrderField.insert_default_fields()
                    print("✓ 默认订单字段插入完成")
                except Exception as e:
                    print(f"⚠ 订单字段插入失败: {e}")
                
                # 插入默认订单类型
                try:
                    OrderType.insert_default_types()
                    print("✓ 默认订单类型插入完成")
                except Exception as e:
                    print(f"⚠ 订单类型插入失败: {e}")
                
                # 创建管理员账户
                admin = User.query.filter_by(email='admin@example.com').first()
                if admin is None:
                    admin = User(email='admin@example.com',
                               username='admin',
                               password='admin123')
                    db.session.add(admin)
                    db.session.commit()
                    print('✓ 管理员账户已创建')
                    print('  邮箱: admin@example.com')
                    print('  密码: admin123')
                else:
                    print('✓ 管理员账户已存在')
                
            except Exception as e:
                print(f"❌ 配置 {config_name} 初始化失败: {e}")
                continue
    
    # 额外创建可能需要的数据库文件
    for db_file in db_files:
        if not os.path.exists(db_file):
            print(f"\n创建额外数据库文件: {db_file}")
            try:
                # 临时修改数据库URI
                import tempfile
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                
                engine = create_engine(f'sqlite:///{db_file}')
                from app.models import Base
                Base.metadata.create_all(engine)
                print(f"✓ 数据库文件 {db_file} 创建完成")
            except Exception as e:
                print(f"❌ 创建 {db_file} 失败: {e}")
    
    print('\n数据库初始化完成！')
    print('现在可以启动服务了。')
    
    return True

if __name__ == '__main__':
    init_database()