#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库优化脚本
修复性能问题和添加必要的索引
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

def optimize_database():
    """优化数据库性能"""
    
    # 获取数据库路径
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'data.sqlite')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    # 创建数据库连接
    engine = create_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)
    
    print("=== 数据库优化开始 ===")
    
    # 检查现有索引
    existing_indexes = {}
    for table_name in inspector.get_table_names():
        existing_indexes[table_name] = [idx['name'] for idx in inspector.get_indexes(table_name)]
        print(f"表 {table_name} 现有索引: {existing_indexes[table_name]}")
    
    # 需要添加的索引
    indexes_to_add = [
        # Order表索引 - 提高查询性能
        ("orders", "idx_orders_wechat_name", "CREATE INDEX IF NOT EXISTS idx_orders_wechat_name ON orders(wechat_name)"),
        ("orders", "idx_orders_wechat_id", "CREATE INDEX IF NOT EXISTS idx_orders_wechat_id ON orders(wechat_id)"),
        ("orders", "idx_orders_phone", "CREATE INDEX IF NOT EXISTS idx_orders_phone ON orders(phone)"),
        ("orders", "idx_orders_completion_time", "CREATE INDEX IF NOT EXISTS idx_orders_completion_time ON orders(completion_time)"),
        ("orders", "idx_orders_create_time", "CREATE INDEX IF NOT EXISTS idx_orders_create_time ON orders(create_time)"),
        ("orders", "idx_orders_user_id", "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)"),
        ("orders", "idx_orders_order_type_id", "CREATE INDEX IF NOT EXISTS idx_orders_order_type_id ON orders(order_type_id)"),
        ("orders", "idx_orders_status", "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)"),
        ("orders", "idx_orders_amount", "CREATE INDEX IF NOT EXISTS idx_orders_amount ON orders(amount)"),
        
        # 复合索引 - 提高复杂查询性能
        ("orders", "idx_orders_user_completion", "CREATE INDEX IF NOT EXISTS idx_orders_user_completion ON orders(user_id, completion_time)"),
        ("orders", "idx_orders_user_create", "CREATE INDEX IF NOT EXISTS idx_orders_user_create ON orders(user_id, create_time)"),
        ("orders", "idx_orders_status_completion", "CREATE INDEX IF NOT EXISTS idx_orders_status_completion ON orders(status, completion_time)"),
        ("orders", "idx_orders_wechat_phone", "CREATE INDEX IF NOT EXISTS idx_orders_wechat_phone ON orders(wechat_name, phone)"),
        ("orders", "idx_orders_amount_status", "CREATE INDEX IF NOT EXISTS idx_orders_amount_status ON orders(amount, status)"),
        
        # WechatUser表索引
        ("wechat_users", "idx_wechat_users_wechat_name", "CREATE INDEX IF NOT EXISTS idx_wechat_users_wechat_name ON wechat_users(wechat_name)"),
        ("wechat_users", "idx_wechat_users_phone", "CREATE INDEX IF NOT EXISTS idx_wechat_users_phone ON wechat_users(phone)"),
        ("wechat_users", "idx_wechat_users_create_time", "CREATE INDEX IF NOT EXISTS idx_wechat_users_create_time ON wechat_users(create_time)"),
        
        # OrderImage表索引
        ("order_images", "idx_order_images_order_id", "CREATE INDEX IF NOT EXISTS idx_order_images_order_id ON order_images(order_id)"),
        ("order_images", "idx_order_images_upload_time", "CREATE INDEX IF NOT EXISTS idx_order_images_upload_time ON order_images(upload_time)"),
        
        # User表索引
        ("users", "idx_users_role_id", "CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id)"),
        
        # OrderField表索引
        ("order_fields", "idx_order_fields_order", "CREATE INDEX IF NOT EXISTS idx_order_fields_order ON order_fields(`order`)"),
        ("order_fields", "idx_order_fields_is_default", "CREATE INDEX IF NOT EXISTS idx_order_fields_is_default ON order_fields(is_default)"),
        
        # OrderType表索引
        ("order_types", "idx_order_types_is_active", "CREATE INDEX IF NOT EXISTS idx_order_types_is_active ON order_types(is_active)"),
        ("order_types", "idx_order_types_create_time", "CREATE INDEX IF NOT EXISTS idx_order_types_create_time ON order_types(create_time)"),
    ]
    
    # 执行索引创建
    with engine.connect() as conn:
        for table_name, index_name, sql in indexes_to_add:
            try:
                if index_name not in existing_indexes.get(table_name, []):
                    conn.execute(text(sql))
                    print(f"✓ 创建索引: {index_name}")
                else:
                    print(f"- 索引已存在: {index_name}")
            except Exception as e:
                print(f"✗ 创建索引失败 {index_name}: {e}")
        
        # 优化SQLite设置
        optimization_queries = [
            "PRAGMA journal_mode = WAL",  # 启用WAL模式提高并发性能
            "PRAGMA synchronous = NORMAL",  # 平衡性能和安全性
            "PRAGMA cache_size = 10000",  # 增加缓存大小
            "PRAGMA temp_store = MEMORY",  # 临时表存储在内存中
            "PRAGMA mmap_size = 268435456",  # 启用内存映射(256MB)
        ]
        
        for query in optimization_queries:
            try:
                conn.execute(text(query))
                print(f"✓ 执行优化: {query}")
            except Exception as e:
                print(f"✗ 优化失败: {query} - {e}")
        
        # 分析表统计信息
        try:
            conn.execute(text("ANALYZE"))
            print("✓ 更新表统计信息")
        except Exception as e:
            print(f"✗ 更新统计信息失败: {e}")
        
        conn.commit()
    
    print("=== 数据库优化完成 ===")
    return True

def check_database_health():
    """检查数据库健康状况"""
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'data.sqlite')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("=== 数据库健康检查 ===")
    
    with engine.connect() as conn:
        # 检查数据库完整性
        try:
            result = conn.execute(text("PRAGMA integrity_check"))
            integrity_result = result.fetchone()[0]
            if integrity_result == 'ok':
                print("✓ 数据库完整性检查通过")
            else:
                print(f"✗ 数据库完整性问题: {integrity_result}")
        except Exception as e:
            print(f"✗ 完整性检查失败: {e}")
        
        # 检查表统计信息
        try:
            tables = ['orders', 'wechat_users', 'order_images', 'users']
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"表 {table}: {count} 条记录")
        except Exception as e:
            print(f"✗ 统计信息获取失败: {e}")
        
        # 检查数据库大小
        try:
            db_size = os.path.getsize(db_path)
            print(f"数据库文件大小: {db_size / (1024*1024):.2f} MB")
        except Exception as e:
            print(f"✗ 获取文件大小失败: {e}")
    
    print("=== 健康检查完成 ===")

def vacuum_database():
    """清理数据库，回收空间"""
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'data.sqlite')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("=== 数据库清理开始 ===")
    
    # 获取清理前的大小
    size_before = os.path.getsize(db_path)
    
    with engine.connect() as conn:
        try:
            conn.execute(text("VACUUM"))
            print("✓ 数据库清理完成")
        except Exception as e:
            print(f"✗ 数据库清理失败: {e}")
            return
    
    # 获取清理后的大小
    size_after = os.path.getsize(db_path)
    saved_space = size_before - size_after
    
    print(f"清理前大小: {size_before / (1024*1024):.2f} MB")
    print(f"清理后大小: {size_after / (1024*1024):.2f} MB")
    print(f"节省空间: {saved_space / (1024*1024):.2f} MB")
    
    print("=== 数据库清理完成 ===")

if __name__ == '__main__':
    print("数据库优化工具")
    print("1. 优化数据库")
    print("2. 健康检查")
    print("3. 清理数据库")
    print("4. 全部执行")
    
    choice = input("请选择操作 (1-4): ").strip()
    
    if choice == '1':
        optimize_database()
    elif choice == '2':
        check_database_health()
    elif choice == '3':
        vacuum_database()
    elif choice == '4':
        optimize_database()
        check_database_health()
        vacuum_database()
    else:
        print("无效选择")