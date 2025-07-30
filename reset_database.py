#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完全重置数据库脚本
警告：此操作将删除所有数据！
"""

import os
import sys

# 添加上级目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Role, User, OrderField, OrderType

def reset_database():
    """完全重置数据库"""
    print("⚠️  警告：此操作将删除所有数据！")
    confirm = input("确定要继续吗？请输入 'YES' 确认: ")
    
    if confirm != 'YES':
        print("操作已取消")
        return False
    
    print("\n正在重置数据库...")
    
    # 数据库文件列表
    db_files = ['data-dev.sqlite', 'data.sqlite']
    
    # 删除现有数据库文件
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"✓ 已删除数据库文件: {db_file}")
            except Exception as e:
                print(f"❌ 删除 {db_file} 失败: {e}")
    
    # 重新创建数据库
    for config_name in ['development', 'production']:
        print(f"\n创建数据库 (配置: {config_name})")
        
        app = create_app(config_name)
        
        with app.app_context():
            try:
                # 创建所有表
                db.create_all()
                print(f"✓ 数据库表创建完成")
                
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
                admin = User(
                    email='admin@example.com',
                    username='admin',
                    password='admin123'
                )
                db.session.add(admin)
                db.session.commit()
                print('✓ 管理员账户已创建')
                
            except Exception as e:
                print(f"❌ 配置 {config_name} 创建失败: {e}")
                continue
    
    print('\n🎉 数据库重置完成！')
    print('\n=== 默认登录信息 ===')
    print('邮箱: admin@example.com')
    print('用户名: admin')
    print('密码: admin123')
    print('\n现在可以重新启动服务了。')
    
    return True

if __name__ == '__main__':
    reset_database()