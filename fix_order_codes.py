#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复订单编码问题
"""

import os
import sys
from datetime import datetime
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Order, User, OrderType

def generate_order_code():
    """生成唯一的订单编码"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_num = random.randint(1000, 9999)
    return f'ORD{timestamp}{random_num}'

def fix_order_codes():
    """修复订单编码问题"""
    app = create_app('default')
    
    with app.app_context():
        print("开始修复订单编码...")
        
        # 查找所有没有订单编码的订单
        orders_without_code = Order.query.filter(
            db.or_(Order.order_code.is_(None), Order.order_code == '')
        ).all()
        
        print(f"找到 {len(orders_without_code)} 个没有订单编码的订单")
        
        if orders_without_code:
            print("\n删除这些无效订单...")
            for order in orders_without_code:
                print(f"删除订单 ID: {order.id}, 微信名: {order.wechat_name}")
                db.session.delete(order)
            
            db.session.commit()
            print("✓ 无效订单已删除")
        
        # 重新创建测试订单
        print("\n重新创建测试订单...")
        
        # 获取管理员用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("✗ 未找到管理员用户")
            return
        
        # 获取订单类型
        order_types = OrderType.query.all()
        if not order_types:
            print("✗ 未找到订单类型")
            return
        
        # 测试订单数据
        test_orders = [
            {
                'wechat_name': '张三',
                'wechat_id': 'zhangsan123',
                'phone': '13800138001',
                'order_info': 'iPhone 15 Pro Max 256GB 深空黑色',
                'quantity': 1,
                'amount': 9999.00,
                'notes': '需要贴膜和手机壳',
                'order_type': '详情页'
            },
            {
                'wechat_name': '李四',
                'wechat_id': 'lisi456',
                'phone': '13800138002',
                'order_info': 'MacBook Pro 14英寸 M3 芯片',
                'quantity': 1,
                'amount': 15999.00,
                'notes': '银色版本，需要发票',
                'order_type': '海报'
            },
            {
                'wechat_name': '王五',
                'wechat_id': 'wangwu789',
                'phone': '13800138003',
                'order_info': 'iPad Air 第5代 64GB WiFi版',
                'quantity': 2,
                'amount': 3798.00,
                'notes': '白色版本，买二送一活动',
                'order_type': '详情页'
            },
            {
                'wechat_name': '赵六',
                'wechat_id': 'zhaoliu101',
                'phone': '13800138004',
                'order_info': 'Apple Watch Series 9 GPS 45mm',
                'quantity': 1,
                'amount': 2999.00,
                'notes': '午夜色铝金属表壳配午夜色运动表带',
                'order_type': '灯箱'
            },
            {
                'wechat_name': '孙七',
                'wechat_id': 'sunqi202',
                'phone': '13800138005',
                'order_info': 'Apple Watch Ultra 2',
                'quantity': 1,
                'amount': 6299.00,
                'notes': '钛金属表壳，橙色运动表带',
                'order_type': '其他'
            }
        ]
        
        created_count = 0
        
        for order_data in test_orders:
            try:
                # 查找订单类型
                order_type = OrderType.query.filter_by(name=order_data['order_type']).first()
                if not order_type:
                    print(f"✗ 未找到订单类型: {order_data['order_type']}")
                    continue
                
                # 生成唯一的订单编码
                order_code = generate_order_code()
                
                # 创建订单
                order = Order(
                    order_code=order_code,
                    wechat_name=order_data['wechat_name'],
                    wechat_id=order_data['wechat_id'],
                    phone=order_data['phone'],
                    order_info=order_data['order_info'],
                    quantity=order_data['quantity'],
                    amount=order_data['amount'],
                    notes=order_data['notes'],
                    user_id=admin_user.id,
                    order_type_id=order_type.id
                )
                
                db.session.add(order)
                created_count += 1
                print(f"✓ 创建订单: {order_code} - {order_data['wechat_name']}")
                
            except Exception as e:
                print(f"✗ 创建订单失败: {order_data['wechat_name']} - {str(e)}")
        
        # 提交所有更改
        try:
            db.session.commit()
            print(f"\n✓ 成功创建 {created_count} 个测试订单")
            
            # 验证结果
            total_orders = Order.query.count()
            print(f"✓ 数据库中总订单数: {total_orders}")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 提交失败: {str(e)}")

if __name__ == '__main__':
    fix_order_codes()