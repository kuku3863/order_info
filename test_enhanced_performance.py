#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版性能测试脚本
测试缓存、API优化和静态资源优化
"""

import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class EnhancedPerformanceTester:
    """增强版性能测试器"""
    
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_page_load(self, endpoint="/"):
        """测试页面加载性能"""
        print(f"测试页面加载: {endpoint}")
        
        times = []
        for i in range(5):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                if response.status_code == 200:
                    load_time = (end_time - start_time) * 1000
                    times.append(load_time)
                    print(f"  第{i+1}次: {load_time:.2f}ms")
                else:
                    print(f"  第{i+1}次: 错误 {response.status_code}")
            except Exception as e:
                print(f"  第{i+1}次: 连接失败 - {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"  平均加载时间: {avg_time:.2f}ms")
            return avg_time
        return None
    
    def test_api_performance(self, endpoint="/api/orders"):
        """测试API性能"""
        print(f"测试API性能: {endpoint}")
        
        times = []
        for i in range(10):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                if response.status_code == 200:
                    api_time = (end_time - start_time) * 1000
                    times.append(api_time)
                    print(f"  第{i+1}次: {api_time:.2f}ms")
                else:
                    print(f"  第{i+1}次: API错误 {response.status_code}")
            except Exception as e:
                print(f"  第{i+1}次: API连接失败 - {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"  API平均响应时间: {avg_time:.2f}ms")
            return avg_time
        return None
    
    def test_cache_performance(self):
        """测试缓存性能"""
        print("测试缓存性能")
        
        # 第一次请求（无缓存）
        start_time = time.time()
        response1 = self.session.get(f"{self.base_url}/orders")
        first_load = (time.time() - start_time) * 1000
        
        # 第二次请求（有缓存）
        start_time = time.time()
        response2 = self.session.get(f"{self.base_url}/orders")
        cached_load = (time.time() - start_time) * 1000
        
        print(f"  首次加载: {first_load:.2f}ms")
        print(f"  缓存加载: {cached_load:.2f}ms")
        
        if first_load > 0 and cached_load > 0:
            improvement = ((first_load - cached_load) / first_load) * 100
            print(f"  缓存提升: {improvement:.1f}%")
        
        return first_load, cached_load
    
    def test_concurrent_requests(self, endpoint="/orders", num_requests=10):
        """测试并发请求性能"""
        print(f"测试并发请求: {num_requests}个请求到{endpoint}")
        
        def make_request():
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                return (end_time - start_time) * 1000, response.status_code
            except Exception as e:
                return None, str(e)
        
        times = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                if result[0] is not None:
                    times.append(result[0])
                    print(f"  请求完成: {result[0]:.2f}ms (状态: {result[1]})")
        
        if times:
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"  并发测试结果:")
            print(f"    平均时间: {avg_time:.2f}ms")
            print(f"    最快时间: {min_time:.2f}ms")
            print(f"    最慢时间: {max_time:.2f}ms")
            print(f"    完成请求: {len(times)}/{num_requests}")
        
        return times
    
    def test_image_optimization(self):
        """测试图片优化"""
        print("测试图片优化功能")
        
        # 测试不同尺寸的图片请求
        test_images = [
            "/optimized-image/test.jpg?width=100&height=100",
            "/optimized-image/test.jpg?width=300&height=300",
            "/optimized-image/test.jpg?quality=50",
            "/optimized-image/test.jpg?quality=90"
        ]
        
        for img_url in test_images:
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{img_url}")
                end_time = time.time()
                
                if response.status_code == 200:
                    load_time = (end_time - start_time) * 1000
                    print(f"  {img_url}: {load_time:.2f}ms")
                else:
                    print(f"  {img_url}: 错误 {response.status_code}")
            except Exception as e:
                print(f"  {img_url}: 连接失败 - {e}")
    
    def generate_performance_report(self):
        """生成性能报告"""
        print("=== 增强版性能测试报告 ===")
        print()
        
        # 测试页面加载
        page_load_time = self.test_page_load("/orders")
        print()
        
        # 测试API性能
        api_time = self.test_api_performance()
        print()
        
        # 测试缓存性能
        first_load, cached_load = self.test_cache_performance()
        print()
        
        # 测试并发性能
        concurrent_times = self.test_concurrent_requests()
        print()
        
        # 测试图片优化
        self.test_image_optimization()
        print()
        
        # 生成总结报告
        print("=== 性能测试总结 ===")
        
        if page_load_time:
            if page_load_time < 500:
                page_rating = "优秀"
            elif page_load_time < 1000:
                page_rating = "良好"
            elif page_load_time < 2000:
                page_rating = "一般"
            else:
                page_rating = "需要优化"
            
            print(f"页面加载性能: {page_rating} ({page_load_time:.2f}ms)")
        
        if api_time:
            if api_time < 100:
                api_rating = "优秀"
            elif api_time < 300:
                api_rating = "良好"
            elif api_time < 500:
                api_rating = "一般"
            else:
                api_rating = "需要优化"
            
            print(f"API响应性能: {api_rating} ({api_time:.2f}ms)")
        
        if first_load and cached_load:
            cache_improvement = ((first_load - cached_load) / first_load) * 100
            print(f"缓存效果: 提升 {cache_improvement:.1f}%")
        
        if concurrent_times:
            avg_concurrent = sum(concurrent_times) / len(concurrent_times)
            print(f"并发性能: 平均 {avg_concurrent:.2f}ms")
        
        print()
        print("=== 优化建议 ===")
        print("1. 如果页面加载时间 > 1000ms，考虑启用CDN")
        print("2. 如果API响应时间 > 300ms，检查数据库查询")
        print("3. 如果缓存提升 < 50%，检查缓存配置")
        print("4. 如果并发性能差，考虑增加服务器资源")

def main():
    """主函数"""
    print("=== 增强版性能测试工具 ===")
    print()
    
    # 检查服务是否运行
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        if response.status_code != 200:
            print("警告: 服务可能未正常运行")
    except:
        print("错误: 无法连接到服务，请确保服务正在运行")
        return
    
    # 创建测试器
    tester = EnhancedPerformanceTester()
    
    # 运行测试
    tester.generate_performance_report()
    
    print("=== 测试完成 ===")

if __name__ == '__main__':
    main() 