#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网络访问故障排除脚本
帮助诊断局域网访问问题
"""

import socket
import subprocess
import sys
import os

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个远程地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def check_port_listening(port=5000):
    """检查端口是否在监听"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except Exception:
        return False

def check_firewall_rule(port=5000):
    """检查防火墙规则"""
    try:
        # 检查入站规则
        cmd = f'netsh advfirewall firewall show rule name="Python {port}" dir=in'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return "Python" in result.stdout
    except Exception:
        return False

def add_firewall_rule(port=5000):
    """添加防火墙规则"""
    try:
        # 删除可能存在的旧规则
        cmd_delete = f'netsh advfirewall firewall delete rule name="Python {port}" dir=in'
        subprocess.run(cmd_delete, shell=True, capture_output=True)
        
        # 添加新规则
        cmd_add = f'netsh advfirewall firewall add rule name="Python {port}" dir=in action=allow protocol=TCP localport={port}'
        result = subprocess.run(cmd_add, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"添加防火墙规则失败: {e}")
        return False

def ping_test(ip):
    """测试网络连通性"""
    try:
        result = subprocess.run(f'ping -n 1 {ip}', shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def main():
    print("=== 网络访问故障排除工具 ===")
    print()
    
    # 1. 获取本机IP
    local_ip = get_local_ip()
    if local_ip:
        print(f"✓ 本机IP地址: {local_ip}")
    else:
        print("❌ 无法获取本机IP地址")
        return
    
    # 2. 检查服务端口
    port = 5000
    if check_port_listening(port):
        print(f"✓ 端口 {port} 正在监听")
    else:
        print(f"❌ 端口 {port} 未在监听，请先启动服务")
        print("   运行命令: python manage.py runserver --host=0.0.0.0 --port=5000")
        return
    
    # 3. 检查防火墙规则
    print(f"\n检查防火墙规则...")
    if check_firewall_rule(port):
        print(f"✓ 防火墙规则已存在")
    else:
        print(f"❌ 防火墙规则不存在")
        print(f"正在尝试添加防火墙规则...")
        
        if add_firewall_rule(port):
            print(f"✓ 防火墙规则添加成功")
        else:
            print(f"❌ 防火墙规则添加失败")
            print(f"请以管理员身份运行此脚本，或手动添加防火墙规则：")
            print(f"   1. 打开 Windows Defender 防火墙")
            print(f"   2. 点击 '高级设置'")
            print(f"   3. 选择 '入站规则' -> '新建规则'")
            print(f"   4. 选择 '端口' -> 'TCP' -> '特定本地端口' -> '{port}'")
            print(f"   5. 选择 '允许连接'")
            print(f"   6. 应用到所有配置文件")
            print(f"   7. 命名规则为 'Python {port}'")
    
    # 4. 网络连通性测试
    print(f"\n网络连通性测试...")
    if ping_test(local_ip):
        print(f"✓ 本机网络连通正常")
    else:
        print(f"❌ 本机网络连通异常")
    
    # 5. 提供访问地址
    print(f"\n=== 访问地址 ===")
    print(f"本地访问: http://127.0.0.1:{port}")
    print(f"局域网访问: http://{local_ip}:{port}")
    
    # 6. 故障排除建议
    print(f"\n=== 故障排除建议 ===")
    print(f"如果仍然无法访问，请检查：")
    print(f"1. 确保服务器正在运行 (python manage.py runserver --host=0.0.0.0 --port={port})")
    print(f"2. 确保防火墙允许端口 {port}")
    print(f"3. 确保客户端和服务器在同一局域网")
    print(f"4. 尝试关闭杀毒软件的网络保护")
    print(f"5. 检查路由器是否阻止了内网通信")
    print(f"6. 尝试使用其他端口 (如 8000, 8080)")
    
    # 7. 手动防火墙命令
    print(f"\n=== 手动防火墙命令 ===")
    print(f"如需手动配置防火墙，请以管理员身份运行：")
    print(f"netsh advfirewall firewall add rule name=\"Python {port}\" dir=in action=allow protocol=TCP localport={port}")
    
    print(f"\n按任意键退出...")
    input()

if __name__ == '__main__':
    main()