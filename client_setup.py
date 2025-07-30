#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户端快速设置脚本 - 解决数据库初始化问题
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """检查Python环境"""
    print("检查Python环境...")
    if sys.version_info < (3, 8):
        print("❌ 错误：需要Python 3.8或更高版本")
        return False
    print(f"✓ Python版本: {sys.version.split()[0]}")
    return True

def install_requirements():
    """安装依赖包"""
    print("\n检查并安装依赖包...")
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt文件不存在")
        return False
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print("✓ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e.stderr.decode() if e.stderr else '未知错误'}")
        return False

def init_database():
    """初始化数据库"""
    print("\n初始化数据库...")
    if not os.path.exists('init_db.py'):
        print("❌ init_db.py文件不存在")
        return False
    
    try:
        result = subprocess.run([sys.executable, 'init_db.py'], 
                               capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print("✓ 数据库初始化成功")
            return True
        else:
            print(f"❌ 数据库初始化失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 数据库初始化异常: {e}")
        return False

def check_database_files():
    """检查数据库文件"""
    print("\n检查数据库文件...")
    db_files = ['data.sqlite', 'data-dev.sqlite']
    found_files = []
    
    for db_file in db_files:
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            print(f"✓ 找到数据库文件: {db_file} ({size} bytes)")
            found_files.append(db_file)
        else:
            print(f"⚠️  数据库文件不存在: {db_file}")
    
    return len(found_files) > 0

def test_database_connection():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    try:
        # 设置环境变量
        os.environ['FLASK_CONFIG'] = 'production'
        
        # 简单的数据库连接测试
        test_script = '''
import sys
sys.path.insert(0, '.')
from app import create_app
from app.models import User, Role

app = create_app()
with app.app_context():
    try:
        # 测试查询用户表
        users = User.query.all()
        roles = Role.query.all()
        print(f"用户数量: {len(users)}")
        print(f"角色数量: {len(roles)}")
        print("数据库连接测试成功")
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        sys.exit(1)
'''
        
        result = subprocess.run([sys.executable, '-c', test_script], 
                               capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✓ 数据库连接测试成功")
            print(result.stdout.strip())
            return True
        else:
            print(f"❌ 数据库连接测试失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接测试异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("订单查询系统 - 客户端快速设置")
    print("=" * 60)
    
    # 检查Python环境
    if not check_python():
        input("\n按回车键退出...")
        return False
    
    # 安装依赖
    if not install_requirements():
        input("\n按回车键退出...")
        return False
    
    # 初始化数据库
    if not init_database():
        input("\n按回车键退出...")
        return False
    
    # 检查数据库文件
    if not check_database_files():
        print("⚠️  警告：未找到数据库文件")
    
    # 测试数据库连接
    if not test_database_connection():
        input("\n按回车键退出...")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 客户端设置完成！")
    print("=" * 60)
    print("\n现在可以启动系统了:")
    print("  方式1: 双击 start.bat")
    print("  方式2: 在命令行运行 python manage.py runserver")
    print("\n访问地址: http://127.0.0.1:5000")
    print("\n默认管理员账户:")
    print("  邮箱: admin@example.com")
    print("  密码: admin123")
    print("\n如果仍有问题，请联系技术支持。")
    
    input("\n按回车键退出...")
    return True

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n设置被用户中断")
    except Exception as e:
        print(f"\n\n设置过程中发生错误: {e}")
        input("按回车键退出...")