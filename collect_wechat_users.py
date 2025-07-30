#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从订单中收集微信用户信息
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Order, WechatUser

def collect_wechat_users():
    """从订单中自动收集微信用户信息（按手机号去重）"""
    app = create_app('development')
    
    with app.app_context():
        print("开始从订单中收集微信用户信息...")
        
        try:
            # 获取所有有手机号的订单，按手机号分组
            orders_with_phone = Order.query.filter(
                Order.phone.isnot(None),
                Order.phone != ''
            ).all()
            
            print(f"找到 {len(orders_with_phone)} 个有手机号的订单")
            
            # 按手机号分组，每个手机号只处理一次
            phone_groups = {}
            for order in orders_with_phone:
                if order.phone not in phone_groups:
                    phone_groups[order.phone] = []
                phone_groups[order.phone].append(order)
            
            print(f"按手机号分组后，共有 {len(phone_groups)} 个不同的手机号")
            
            collected_count = 0
            updated_count = 0
            
            for phone, orders in phone_groups.items():
                # 根据手机号查找现有用户（手机号是唯一标识）
                existing_user = WechatUser.query.filter_by(phone=phone).first()
                
                # 从该手机号的所有订单中选择最新的信息
                latest_order = max(orders, key=lambda x: x.create_time)
                
                # 选择最好的微信名（非空且不是默认格式）
                best_wechat_name = None
                for order in orders:
                    if order.wechat_name and not order.wechat_name.startswith('用户_'):
                        best_wechat_name = order.wechat_name
                        break
                if not best_wechat_name:
                    best_wechat_name = latest_order.wechat_name or f'用户_{phone}'
                
                # 选择最好的微信号（非空）
                best_wechat_id = None
                for order in orders:
                    if order.wechat_id and order.wechat_id.strip():
                        best_wechat_id = order.wechat_id
                        break
                
                if not existing_user:
                    # 创建新的微信用户
                    wechat_user = WechatUser(
                        wechat_name=best_wechat_name,
                        wechat_id=best_wechat_id,
                        phone=phone,
                        create_time=datetime.utcnow(),
                        update_time=datetime.utcnow()
                    )
                    db.session.add(wechat_user)
                    collected_count += 1
                    print(f"✓ 创建用户: {best_wechat_name} ({phone})")
                else:
                    # 更新现有用户信息（如果新信息更好）
                    updated = False
                    if not existing_user.wechat_name or existing_user.wechat_name.startswith('用户_'):
                        if best_wechat_name and not best_wechat_name.startswith('用户_'):
                            existing_user.wechat_name = best_wechat_name
                            updated = True
                    
                    if not existing_user.wechat_id and best_wechat_id:
                        existing_user.wechat_id = best_wechat_id
                        updated = True
                    
                    if updated:
                        existing_user.update_time = datetime.utcnow()
                        updated_count += 1
                        print(f"✓ 更新用户: {existing_user.wechat_name} ({phone})")
                    else:
                        print(f"- 用户已存在，无需更新: {existing_user.wechat_name} ({phone})")
            
            # 提交数据库更改
            print(f"\n提交数据库更改...")
            db.session.commit()
            print(f"✅ 成功收集了 {collected_count} 个新微信用户，更新了 {updated_count} 个现有用户")
            
        except Exception as e:
            print(f"✗ 收集过程中出错: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
        
        print("\n=== 收集后的状态 ===")
        wechat_users_after = WechatUser.query.all()
        print(f"微信用户数量: {len(wechat_users_after)}")
        for user in wechat_users_after:
            print(f"  - {user.wechat_name}, 手机号: {user.phone}, 微信号: {user.wechat_id or '未设置'}")

if __name__ == '__main__':
    collect_wechat_users()