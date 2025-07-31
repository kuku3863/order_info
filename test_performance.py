#!/usr/bin/env python3
"""
性能测试脚本
用于测试前端性能优化效果
"""

import time
import requests
import json
from datetime import datetime
import statistics

class PerformanceTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
        
    def test_page_load(self, endpoint="/"):
        """测试页面加载性能"""
        print(f"测试页面加载: {endpoint}")
        
        times = []
        for i in range(5):  # 测试5次取平均值
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                if response.status_code == 200:
                    load_time = (end_time - start_time) * 1000  # 转换为毫秒
                    times.append(load_time)
                    print(f"  第{i+1}次: {load_time:.2f}ms")
                else:
                    print(f"  第{i+1}次: 错误 - HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  第{i+1}次: 错误 - {e}")
                
            time.sleep(1)  # 等待1秒再进行下一次测试
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            self.results[endpoint] = {
                'average': avg_time,
                'minimum': min_time,
                'maximum': max_time,
                'count': len(times)
            }
            
            print(f"  平均加载时间: {avg_time:.2f}ms")
            print(f"  最快: {min_time:.2f}ms")
            print(f"  最慢: {max_time:.2f}ms")
        else:
            print("  所有测试都失败了")
    
    def test_resource_loading(self):
        """测试资源加载性能"""
        print("测试资源加载性能...")
        
        resources = [
            "/static/styles.css",
            "/static/js/main.js",
            "/static/css/performance.css",
            "/static/js/performance.js"
        ]
        
        for resource in resources:
            times = []
            for i in range(3):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{resource}")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        load_time = (end_time - start_time) * 1000
                        times.append(load_time)
                        
                except Exception as e:
                    print(f"  资源 {resource} 加载失败: {e}")
                    
                time.sleep(0.5)
            
            if times:
                avg_time = statistics.mean(times)
                print(f"  {resource}: {avg_time:.2f}ms")
    
    def test_api_endpoints(self):
        """测试API端点性能"""
        print("测试API端点性能...")
        
        endpoints = [
            "/orders",
            "/order/new",
            "/orders/statistics"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                if response.status_code == 200:
                    load_time = (end_time - start_time) * 1000
                    print(f"  {endpoint}: {load_time:.2f}ms")
                else:
                    print(f"  {endpoint}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  {endpoint}: 错误 - {e}")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        print("测试内存使用情况...")
        
        import psutil
        process = psutil.Process()
        
        # 获取内存信息
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        print(f"  内存使用: {memory_info.rss / 1024 / 1024:.2f}MB")
        print(f"  内存使用率: {memory_percent:.2f}%")
    
    def generate_report(self):
        """生成性能报告"""
        print("\n" + "="*50)
        print("性能测试报告")
        print("="*50)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试URL: {self.base_url}")
        print()
        
        if self.results:
            print("页面加载性能:")
            for endpoint, result in self.results.items():
                print(f"  {endpoint}:")
                print(f"    平均时间: {result['average']:.2f}ms")
                print(f"    最快时间: {result['minimum']:.2f}ms")
                print(f"    最慢时间: {result['maximum']:.2f}ms")
                print()
        
        # 保存报告到文件
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'results': self.results
        }
        
        with open('performance_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print("报告已保存到 performance_report.json")
    
    def compare_with_baseline(self, baseline_file="baseline_performance.json"):
        """与基准性能进行比较"""
        try:
            with open(baseline_file, 'r', encoding='utf-8') as f:
                baseline = json.load(f)
            
            print("\n性能对比:")
            print("-" * 30)
            
            for endpoint, current_result in self.results.items():
                if endpoint in baseline['results']:
                    baseline_result = baseline['results'][endpoint]
                    
                    improvement = baseline_result['average'] - current_result['average']
                    improvement_percent = (improvement / baseline_result['average']) * 100
                    
                    print(f"{endpoint}:")
                    print(f"  基准: {baseline_result['average']:.2f}ms")
                    print(f"  当前: {current_result['average']:.2f}ms")
                    print(f"  改进: {improvement:.2f}ms ({improvement_percent:+.1f}%)")
                    print()
                    
        except FileNotFoundError:
            print(f"基准文件 {baseline_file} 不存在")
        except Exception as e:
            print(f"比较基准时出错: {e}")
    
    def run_full_test(self):
        """运行完整性能测试"""
        print("开始性能测试...")
        print("="*50)
        
        # 测试首页加载
        self.test_page_load("/")
        
        # 测试订单列表页
        self.test_page_load("/orders")
        
        # 测试资源加载
        self.test_resource_loading()
        
        # 测试API端点
        self.test_api_endpoints()
        
        # 测试内存使用
        self.test_memory_usage()
        
        # 生成报告
        self.generate_report()
        
        # 与基准比较
        self.compare_with_baseline()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='性能测试工具')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='测试的URL (默认: http://localhost:5000)')
    parser.add_argument('--baseline', action='store_true',
                       help='保存当前结果为基准')
    
    args = parser.parse_args()
    
    tester = PerformanceTester(args.url)
    tester.run_full_test()
    
    if args.baseline:
        # 保存为基准
        baseline_data = {
            'timestamp': datetime.now().isoformat(),
            'base_url': args.url,
            'results': tester.results
        }
        
        with open('baseline_performance.json', 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)
        
        print("\n当前结果已保存为基准")

if __name__ == '__main__':
    main() 