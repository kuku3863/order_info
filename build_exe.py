#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 将Flask应用打包成exe文件
"""

import os
import subprocess
import shutil
from pathlib import Path

def build_exe():
    """打包应用为exe文件"""
    print("开始打包应用...")
    
    # 获取Flask-Bootstrap模板路径
    import flask_bootstrap
    bootstrap_templates = os.path.join(os.path.dirname(flask_bootstrap.__file__), 'templates')
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',
        '--add-data', 'app;app',
        '--add-data', 'migrations;migrations',
        '--add-data', 'config.py;.',
        '--add-data', 'init_db.py;.',
        '--add-data', f'{bootstrap_templates};flask_bootstrap/templates',
        '--hidden-import', 'pymysql',
        '--hidden-import', 'flask',
        '--hidden-import', 'flask_sqlalchemy',
        '--hidden-import', 'flask_login',
        '--hidden-import', 'flask_wtf',
        '--hidden-import', 'flask_migrate',
        '--hidden-import', 'flask_bootstrap',
        '--hidden-import', 'wtforms',
        '--hidden-import', 'email_validator',
        '--hidden-import', 'PIL',
        '--hidden-import', 'openpyxl',
        '--hidden-import', 'sqlalchemy',
        '--hidden-import', 'jinja2',
        '--hidden-import', 'werkzeug',
        '--name', '订单查询系统',
        'manage.py'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ 打包完成！")
        print("exe文件位置：dist/订单查询系统.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败：{e}")
        return False

def create_portable_package():
    """创建便携式部署包"""
    print("创建便携式部署包...")
    
    # 创建部署文件夹
    deploy_dir = Path('portable_deploy')
    deploy_dir.mkdir(exist_ok=True)
    
    # 复制必要文件
    files_to_copy = [
        'dist/订单查询系统.exe',
        'data-dev.sqlite',
        'data.sqlite',
        'init_db.py',
        'config.py',
        'requirements.txt',
        '部署指南.md',
        '网络部署指南.md'
    ]
    
    for file_path in files_to_copy:
        if os.path.exists(file_path):
            shutil.copy2(file_path, deploy_dir)
    
    # 创建启动脚本
    start_script = deploy_dir / 'start.bat'
    with open(start_script, 'w', encoding='utf-8') as f:
        f.write('''
@echo off
chcp 65001 >nul
echo ====================================
echo 订单查询系统（便携版）
echo ====================================
echo.

echo 正在初始化数据库...
python "%~dp0init_db.py"
echo.
echo 正在启动应用...
set FLASK_ENV=production
set DATABASE_URL=sqlite:///%~dp0data.sqlite
订单查询系统.exe runserver

echo.
echo 应用已停止
pause
''')
    
    # 创建网络启动脚本
    network_script = deploy_dir / 'start_network.bat'
    with open(network_script, 'w', encoding='utf-8') as f:
        f.write('''
@echo off
chcp 65001 >nul
echo ====================================
echo 订单查询系统网络版（便携版）
echo ====================================
echo.

echo 正在初始化数据库...
python "%~dp0init_db.py"
echo.
echo 正在启动网络服务...
echo 其他电脑可通过局域网IP:5000访问
echo.
set FLASK_ENV=production
set DATABASE_URL=sqlite:///%~dp0data.sqlite
订单查询系统.exe runserver --host=0.0.0.0 --port=5000

echo.
echo 服务已停止
pause
''')
    
    print(f"✓ 便携式部署包创建完成：{deploy_dir}")
    print("包含文件：")
    for file in deploy_dir.iterdir():
        print(f"  - {file.name}")

if __name__ == '__main__':
    print("=" * 50)
    print("订单查询系统打包工具")
    print("=" * 50)
    
    if build_exe():
        create_portable_package()
        print("\n" + "=" * 50)
        print("✓ 打包完成！")
        print("=" * 50)
        print("便携式部署包位置：portable_deploy/")
        print("\n使用说明：")
        print("1. 将portable_deploy文件夹复制到目标电脑")
        print("2. 双击start.bat启动本地服务")
        print("3. 双击start_network.bat启动网络服务")
        print("4. 无需安装Python环境")
    else:
        print("打包失败，请检查错误信息")