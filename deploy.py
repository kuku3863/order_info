#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
部署脚本 - 自动化部署订单查询系统
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误：需要Python 3.8或更高版本")
        return False
    print(f"✓ Python版本: {sys.version}")
    return True

def install_dependencies():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依赖包安装失败")
        return False

def create_upload_folder():
    """创建上传文件夹"""
    base_path = Path('static/uploads')
    folders = ['orders', 'avatars', 'qr_codes']
    
    try:
        # 创建基础上传目录
        base_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建基础上传文件夹: {base_path}")
        
        # 创建各类型图片的子文件夹
        for folder in folders:
            folder_path = base_path / folder
            folder_path.mkdir(exist_ok=True)
            print(f"✓ 创建子文件夹: {folder_path}")
        
        return True
    except Exception as e:
        print(f"❌ 创建上传文件夹失败: {e}")
        return False

def check_config():
    """检查配置文件"""
    if not os.path.exists('config.py'):
        print("❌ 配置文件config.py不存在")
        return False
    
    if os.path.exists('config_example.py'):
        print("ℹ️  发现config_example.py，请参考此文件配置数据库连接")
    
    print("✓ 配置文件检查完成")
    return True

def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    try:
        subprocess.check_call([sys.executable, 'init_db.py'])
        print("✓ 数据库初始化完成")
        print("默认管理员账户:")
        print("  邮箱: admin@example.com")
        print("  密码: admin123")
        return True
    except subprocess.CalledProcessError:
        print("❌ 数据库初始化失败")
        print("请检查数据库连接配置")
        return False

def main():
    """主部署流程"""
    print("=" * 50)
    print("订单查询系统部署脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    # 安装依赖
    if not install_dependencies():
        return False
    
    # 创建上传文件夹
    if not create_upload_folder():
        return False
    
    # 检查配置
    if not check_config():
        return False
    
    # 初始化数据库
    if not init_database():
        return False
    
    print("\n" + "=" * 50)
    print("✓ 部署完成！")
    print("=" * 50)
    print("启动应用:")
    print("  python manage.py runserver")
    print("\n访问地址:")
    print("  http://localhost:5000")
    print("\n默认管理员账户:")
    print("  邮箱: admin@example.com")
    print("  密码: admin123")
    print("\n重要提醒:")
    print("  1. 生产环境请修改默认密码")
    print("  2. 请根据需要修改config.py中的数据库配置")
    print("  3. 详细说明请查看部署指南.md")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n部署被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n部署过程中发生错误: {e}")
        sys.exit(1)