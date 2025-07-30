#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

def test_page():
    """简单测试页面内容"""
    try:
        # 直接访问微信用户页面
        response = requests.get('http://127.0.0.1:5000/admin/wechat-users')
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 302:
            print("页面重定向到登录页面（需要登录）")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 检查是否包含收集按钮相关文本
        if '收集微信用户' in response.text:
            print("✓ 页面包含'收集微信用户'文本")
        else:
            print("✗ 页面不包含'收集微信用户'文本")
        
        # 检查是否包含刷新按钮相关文本
        if '刷新用户信息' in response.text:
            print("✓ 页面包含'刷新用户信息'文本")
        else:
            print("✗ 页面不包含'刷新用户信息'文本")
        
        # 检查uncollected_count
        if 'uncollected_count' in response.text:
            print("✓ 页面包含uncollected_count变量")
        else:
            print("✗ 页面不包含uncollected_count变量")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    test_page()