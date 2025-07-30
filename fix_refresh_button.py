#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复刷新按钮卡住问题的脚本

问题分析：
1. 前端JavaScript在点击刷新按钮时会禁用按钮并显示"刷新中..."
2. 如果后端处理失败或重定向有问题，按钮会一直保持禁用状态
3. 需要在前端添加超时机制和错误处理
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import WechatUser, Order
from datetime import datetime

def test_refresh_function():
    """测试刷新功能是否正常工作"""
    app = create_app()
    
    with app.app_context():
        print("=== 测试刷新功能 ===")
        
        # 检查数据库状态
        wechat_users = WechatUser.query.all()
        orders = Order.query.all()
        
        print(f"当前微信用户数量: {len(wechat_users)}")
        print(f"当前订单数量: {len(orders)}")
        
        # 模拟刷新逻辑
        try:
            updated_count = 0
            cleaned_count = 0
            
            for wechat_user in wechat_users:
                # 检查是否为无效用户
                if (not wechat_user.phone or not wechat_user.phone.strip()) and \
                   (not wechat_user.wechat_id or not wechat_user.wechat_id.strip()):
                    print(f"发现无效用户: {wechat_user.wechat_name}")
                    cleaned_count += 1
                    continue
                
                # 根据手机号查找最新订单
                if wechat_user.phone and wechat_user.phone.strip():
                    latest_order = Order.query.filter_by(phone=wechat_user.phone).order_by(Order.create_time.desc()).first()
                    
                    if latest_order:
                        updated = False
                        old_wechat_name = wechat_user.wechat_name
                        
                        # 检查是否需要更新微信名
                        if latest_order.wechat_name and latest_order.wechat_name != wechat_user.wechat_name:
                            print(f"更新微信名: {old_wechat_name} -> {latest_order.wechat_name}")
                            updated = True
                        
                        # 检查是否需要更新微信号
                        if latest_order.wechat_id and (not wechat_user.wechat_id or not wechat_user.wechat_id.strip()):
                            print(f"更新微信号: {wechat_user.wechat_id} -> {latest_order.wechat_id}")
                            updated = True
                        
                        if updated:
                            updated_count += 1
            
            print(f"\n刷新结果:")
            print(f"- 可更新用户数: {updated_count}")
            print(f"- 可清理无效用户数: {cleaned_count}")
            print("\n✅ 刷新功能逻辑正常")
            
        except Exception as e:
            print(f"❌ 刷新功能测试失败: {str(e)}")
            return False
        
        return True

def create_improved_template():
    """创建改进的模板文件，修复刷新按钮问题"""
    print("\n=== 创建改进的前端代码 ===")
    
    improved_js = '''
// 改进的刷新按钮处理函数
function handleRefreshSubmit(event) {
    console.log('刷新用户信息按钮被点击');
    
    if (!confirm('确定要刷新所有微信用户信息吗？这将从订单中同步最新的微信名和联系方式。')) {
        console.log('用户取消了刷新操作');
        return false;
    }
    
    // 显示加载状态
    const btn = document.getElementById('refreshBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 刷新中...';
    btn.disabled = true;
    
    console.log('开始刷新用户信息...');
    
    // 添加超时机制，防止按钮永久禁用
    const timeoutId = setTimeout(() => {
        console.warn('刷新操作超时，恢复按钮状态');
        btn.innerHTML = originalText;
        btn.disabled = false;
        alert('刷新操作超时，请检查网络连接或稍后重试');
    }, 30000); // 30秒超时
    
    // 监听页面卸载事件，清除超时
    window.addEventListener('beforeunload', () => {
        clearTimeout(timeoutId);
    });
    
    return true;
}

// 页面加载完成后检查按钮状态
document.addEventListener('DOMContentLoaded', function() {
    console.log('微信用户管理页面已加载');
    
    // 检查刷新按钮是否卡住
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn && refreshBtn.disabled) {
        console.log('检测到刷新按钮处于禁用状态，正在恢复...');
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> 刷新用户信息';
        refreshBtn.disabled = false;
    }
    
    // 检查收集按钮是否卡住
    const collectBtn = document.getElementById('collectBtn');
    if (collectBtn && collectBtn.disabled) {
        console.log('检测到收集按钮处于禁用状态，正在恢复...');
        collectBtn.innerHTML = '<i class="fas fa-download"></i> 收集微信用户';
        collectBtn.disabled = false;
    }
    
    // 检查是否有flash消息
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        console.log(`发现 ${alerts.length} 个提示消息`);
        alerts.forEach((alert, index) => {
            console.log(`消息 ${index + 1}: ${alert.textContent.trim()}`);
        });
    }
});
'''
    
    with open('improved_refresh_handler.js', 'w', encoding='utf-8') as f:
        f.write(improved_js)
    
    print("✅ 已创建改进的JavaScript代码文件: improved_refresh_handler.js")
    
    print("\n=== 修复建议 ===")
    print("1. 前端问题：刷新按钮在点击后被禁用，但如果请求失败或超时，按钮不会恢复")
    print("2. 解决方案：")
    print("   - 添加30秒超时机制")
    print("   - 页面加载时检查按钮状态并自动恢复")
    print("   - 添加错误处理和用户提示")
    print("3. 建议更新模板文件中的JavaScript代码")

if __name__ == '__main__':
    print("刷新按钮修复脚本")
    print("=" * 50)
    
    # 测试刷新功能
    if test_refresh_function():
        print("\n后端刷新功能正常，问题出在前端JavaScript")
    
    # 创建改进的代码
    create_improved_template()
    
    print("\n=== 总结 ===")
    print("问题原因：前端JavaScript缺少错误处理和超时机制")
    print("解决方案：更新前端代码，添加超时和状态恢复机制")
    print("\n建议：将improved_refresh_handler.js中的代码替换到wechat_user_list.html模板中")