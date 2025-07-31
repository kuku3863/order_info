#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库索引优化脚本
为现有数据库添加性能优化索引
"""

import os
import sys
from sqlalchemy import create_engine, text, Index
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateIndex

def add_database_indexes():
    """为数据库添加性能优化索引"""
    
    # 获取数据库路径
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'data.sqlite')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    # 创建数据库连接
    engine = create_engine(f'sqlite:///{db_path}')
    
    # 定义需要添加的索引
    indexes = [
        # Order表索引
        ("orders", "idx_wechat_name", ["wechat_name"]),
        ("orders", "idx_wechat_id", ["wechat_id"]),
        ("orders", "idx_phone", ["phone"]),
        ("orders", "idx_completion_time", ["completion_time"]),
        ("orders", "idx_create_time", ["create_time"]),
        ("orders", "idx_user_id", ["user_id"]),
        ("orders", "idx_order_type_id", ["order_type_id"]),
        ("orders", "idx_status", ["status"]),
        
        # 复合索引
        ("orders", "idx_user_completion_time", ["user_id", "completion_time"]),
        ("orders", "idx_user_create_time", ["user_id", "create_time"]),
        ("orders", "idx_status_completion_time", ["status", "completion_time"]),
        ("orders", "idx_wechat_phone", ["wechat_name", "phone"]),
        ("orders", "idx_amount_status", ["amount", "status"]),
        
        # WechatUser表索引
        ("wechat_users", "idx_wechat_name", ["wechat_name"]),
        ("wechat_users", "idx_phone", ["phone"]),
        ("wechat_users", "idx_create_time", ["create_time"]),
        ("wechat_users", "idx_wechat_phone_lookup", ["wechat_name", "phone"]),
        
        # OrderImage表索引
        ("order_images", "idx_order_id", ["order_id"]),
    ]
    
    try:
        with engine.connect() as conn:
            # 检查现有索引
            existing_indexes = []
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            for row in result:
                existing_indexes.append(row[0])
            
            print("现有索引:", existing_indexes)
            
            # 添加新索引
            added_count = 0
            for table_name, index_name, columns in indexes:
                if index_name not in existing_indexes:
                    try:
                        # 构建创建索引的SQL
                        columns_str = ", ".join(columns)
                        sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
                        
                        print(f"正在创建索引: {index_name} 在表 {table_name} 上")
                        conn.execute(text(sql))
                        conn.commit()
                        added_count += 1
                        print(f"✓ 成功创建索引: {index_name}")
                        
                    except Exception as e:
                        print(f"✗ 创建索引 {index_name} 失败: {e}")
                else:
                    print(f"- 索引 {index_name} 已存在，跳过")
            
            print(f"\n索引优化完成！共添加了 {added_count} 个新索引")
            
            # 显示优化建议
            print("\n=== 数据库优化建议 ===")
            print("1. 定期运行 ANALYZE 命令更新统计信息:")
            print("   ANALYZE;")
            print("2. 监控查询性能:")
            print("   EXPLAIN QUERY PLAN SELECT * FROM orders WHERE user_id = 1;")
            print("3. 考虑定期清理旧数据以提高性能")
            
            return True
            
    except Exception as e:
        print(f"数据库索引优化失败: {e}")
        return False

def analyze_database():
    """分析数据库性能"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'data.sqlite')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    try:
        with engine.connect() as conn:
            # 获取表信息
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            
            print("=== 数据库表信息 ===")
            for table in tables:
                if table != 'sqlite_sequence':
                    # 获取表行数
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    
                    # 获取索引信息
                    index_result = conn.execute(text(f"PRAGMA index_list({table})"))
                    indexes = [row[1] for row in index_result]
                    
                    print(f"表: {table}")
                    print(f"  行数: {count}")
                    print(f"  索引: {', '.join(indexes) if indexes else '无'}")
                    print()
            
            # 运行ANALYZE更新统计信息
            print("正在更新数据库统计信息...")
            conn.execute(text("ANALYZE"))
            print("✓ 统计信息更新完成")
            
    except Exception as e:
        print(f"数据库分析失败: {e}")

def create_performance_test_queries():
    """创建性能测试查询"""
    test_queries = [
        {
            "name": "按用户查询订单",
            "sql": "SELECT * FROM orders WHERE user_id = 1 ORDER BY create_time DESC LIMIT 10;",
            "description": "测试用户订单查询性能"
        },
        {
            "name": "按日期范围查询",
            "sql": "SELECT * FROM orders WHERE completion_time BETWEEN '2024-01-01' AND '2024-12-31';",
            "description": "测试日期范围查询性能"
        },
        {
            "name": "按状态查询",
            "sql": "SELECT * FROM orders WHERE status = '未完成';",
            "description": "测试状态查询性能"
        },
        {
            "name": "统计查询",
            "sql": "SELECT COUNT(*), SUM(amount), AVG(amount) FROM orders WHERE user_id = 1;",
            "description": "测试统计查询性能"
        },
        {
            "name": "微信用户查询",
            "sql": "SELECT * FROM wechat_users WHERE phone = '13800138000';",
            "description": "测试微信用户查询性能"
        }
    ]
    
    print("=== 性能测试查询 ===")
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. {query['name']}")
        print(f"   描述: {query['description']}")
        print(f"   SQL: {query['sql']}")
        print()

if __name__ == '__main__':
    print("=== 数据库索引优化工具 ===")
    print()
    
    # 添加索引
    print("1. 添加数据库索引...")
    if add_database_indexes():
        print("✓ 索引优化完成")
    else:
        print("✗ 索引优化失败")
    
    print()
    
    # 分析数据库
    print("2. 分析数据库性能...")
    analyze_database()
    
    print()
    
    # 显示测试查询
    create_performance_test_queries()
    
    print("=== 优化完成 ===")
    print("建议重启应用程序以应用新的索引优化") 