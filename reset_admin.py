#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重置管理员密码脚本
"""

import os
import sys

# 添加上级目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """重置管理员密码"""
    print("正在重置管理员密码...")
    
    # 创建应用实例
    app = create_app('development')
    
    with app.app_context():
        try:
            # 查找管理员账户
            admin = User.query.filter_by(email='admin@example.com').first()
            
            if admin is None:
                # 如果没有管理员账户，创建一个
                print("未找到管理员账户，正在创建...")
                admin = User(
                    email='admin@example.com',
                    username='admin',
                    password='admin123'
                )
                db.session.add(admin)
                db.session.commit()
                print("✓ 管理员账户已创建")
            else:
                # 重置密码
                admin.password = 'admin123'
                db.session.commit()
                print("✓ 管理员密码已重置")
            
            print("\n=== 登录信息 ===")
            print("邮箱: admin@example.com")
            print("用户名: admin")
            print("密码: admin123")
            print("\n请使用以上信息登录系统")
            
        except Exception as e:
            print(f"❌ 重置密码失败: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    reset_admin_password()