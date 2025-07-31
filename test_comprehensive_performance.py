#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合性能测试脚本
测试所有优化功能的效果
"""

import time
import requests
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class ComprehensivePerformanceTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
        
    def test_page_load_performance(self):
        """测试页面加载性能"""
        print("=== 测试页面加载性能 ===")
        
        endpoints = [
            "/",
            "/orders",
            "/orders/statistics",
            "/admin/wechat-users"
        ]
        
        results = {}
        for endpoint in endpoints:
            times = []
            for i in range(5):  # 每个页面测试5次
                start_time = time.time()
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    load_time = time.time() - start_time
                    times.append(load_time)
                    print(f"  {endpoint}: {load_time:.3f}s (状态码: {response.status_code})")
                except Exception as e:
                    print(f"  {endpoint}: 错误 - {e}")
                    times.append(None)
            
            # 计算统计信息
            valid_times = [t for t in times if t is not None]
            if valid_times:
                results[endpoint] = {
                    'avg_time': sum(valid_times) / len(valid_times),
                    'min_time': min(valid_times),
                    'max_time': max(valid_times),
                    'success_rate': len(valid_times) / len(times)
                }
        
        self.results['page_load'] = results
        return results
    
    def test_api_performance(self):
        """测试API性能"""
        print("\n=== 测试API性能 ===")
        
        api_endpoints = [
            "/api/orders",
            "/api/statistics",
            "/api/cache/stats"
        ]
        
        results = {}
        for endpoint in api_endpoints:
            times = []
            for i in range(10):  # 每个API测试10次
                start_time = time.time()
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    api_time = time.time() - start_time
                    times.append(api_time)
                    print(f"  {endpoint}: {api_time:.3f}s (状态码: {response.status_code})")
                except Exception as e:
                    print(f"  {endpoint}: 错误 - {e}")
                    times.append(None)
            
            valid_times = [t for t in times if t is not None]
            if valid_times:
                results[endpoint] = {
                    'avg_time': sum(valid_times) / len(valid_times),
                    'min_time': min(valid_times),
                    'max_time': max(valid_times),
                    'success_rate': len(valid_times) / len(times)
                }
        
        self.results['api_performance'] = results
        return results
    
    def test_cache_effectiveness(self):
        """测试缓存效果"""
        print("\n=== 测试缓存效果 ===")
        
        # 测试订单列表页面的缓存效果
        endpoint = "/orders"
        times_without_cache = []
        times_with_cache = []
        
        # 第一次访问（无缓存）
        for i in range(3):
            start_time = time.time()
            response = self.session.get(f"{self.base_url}{endpoint}")
            load_time = time.time() - start_time
            times_without_cache.append(load_time)
            print(f"  无缓存访问 {i+1}: {load_time:.3f}s")
        
        # 等待一下让缓存生效
        time.sleep(2)
        
        # 第二次访问（有缓存）
        for i in range(3):
            start_time = time.time()
            response = self.session.get(f"{self.base_url}{endpoint}")
            load_time = time.time() - start_time
            times_with_cache.append(load_time)
            print(f"  有缓存访问 {i+1}: {load_time:.3f}s")
        
        avg_without_cache = sum(times_without_cache) / len(times_without_cache)
        avg_with_cache = sum(times_with_cache) / len(times_with_cache)
        
        improvement = ((avg_without_cache - avg_with_cache) / avg_without_cache) * 100
        
        results = {
            'avg_without_cache': avg_without_cache,
            'avg_with_cache': avg_with_cache,
            'improvement_percent': improvement,
            'times_without_cache': times_without_cache,
            'times_with_cache': times_with_cache
        }
        
        self.results['cache_effectiveness'] = results
        print(f"  缓存效果: 平均提升 {improvement:.1f}%")
        return results
    
    def test_concurrent_requests(self):
        """测试并发请求性能"""
        print("\n=== 测试并发请求性能 ===")
        
        def make_request(endpoint):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                duration = time.time() - start_time
                return {
                    'endpoint': endpoint,
                    'duration': duration,
                    'status_code': response.status_code,
                    'success': True
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    'endpoint': endpoint,
                    'duration': duration,
                    'error': str(e),
                    'success': False
                }
        
        endpoints = ["/orders", "/api/orders", "/orders/statistics"]
        concurrent_levels = [5, 10, 20]
        
        results = {}
        for level in concurrent_levels:
            print(f"  测试 {level} 个并发请求...")
            
            all_results = []
            with ThreadPoolExecutor(max_workers=level) as executor:
                # 为每个并发级别创建多个请求
                futures = []
                for _ in range(level):
                    for endpoint in endpoints:
                        futures.append(executor.submit(make_request, endpoint))
                
                for future in as_completed(futures):
                    all_results.append(future.result())
            
            # 计算统计信息
            successful_requests = [r for r in all_results if r['success']]
            failed_requests = [r for r in all_results if not r['success']]
            
            if successful_requests:
                durations = [r['duration'] for r in successful_requests]
                results[level] = {
                    'total_requests': len(all_results),
                    'successful_requests': len(successful_requests),
                    'failed_requests': len(failed_requests),
                    'success_rate': len(successful_requests) / len(all_results),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations)
                }
                
                print(f"    {level}并发: 成功率 {results[level]['success_rate']:.1%}, "
                      f"平均时间 {results[level]['avg_duration']:.3f}s")
        
        self.results['concurrent_performance'] = results
        return results
    
    def test_image_optimization(self):
        """测试图片优化功能"""
        print("\n=== 测试图片优化功能 ===")
        
        # 测试图片优化API
        test_images = [
            "test.jpg",
            "sample.png"
        ]
        
        optimization_params = [
            {'width': 100, 'height': 100},
            {'width': 300, 'height': 300},
            {'quality': 50},
            {'quality': 90}
        ]
        
        results = {}
        for image in test_images:
            results[image] = {}
            for params in optimization_params:
                param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                url = f"{self.base_url}/optimized-image/{image}?{param_str}"
                
                start_time = time.time()
                try:
                    response = self.session.get(url)
                    duration = time.time() - start_time
                    
                    results[image][param_str] = {
                        'duration': duration,
                        'status_code': response.status_code,
                        'content_length': len(response.content) if response.status_code == 200 else 0
                    }
                    
                    print(f"  {image} ({param_str}): {duration:.3f}s, "
                          f"状态码: {response.status_code}")
                    
                except Exception as e:
                    results[image][param_str] = {
                        'duration': time.time() - start_time,
                        'error': str(e)
                    }
                    print(f"  {image} ({param_str}): 错误 - {e}")
        
        self.results['image_optimization'] = results
        return results
    
    def test_database_query_performance(self):
        """测试数据库查询性能"""
        print("\n=== 测试数据库查询性能 ===")
        
        # 测试不同的查询参数
        test_cases = [
            {'page': 1, 'per_page': 10},
            {'page': 1, 'per_page': 20},
            {'page': 2, 'per_page': 10},
            {'start_date': '2025-07-01', 'end_date': '2025-07-31'},
            {'search_type': 'wechat_name', 'search_value': 'test'}
        ]
        
        results = {}
        for i, params in enumerate(test_cases):
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.base_url}/api/orders?{param_str}"
            
            times = []
            for j in range(5):  # 每个查询测试5次
                start_time = time.time()
                try:
                    response = self.session.get(url)
                    query_time = time.time() - start_time
                    times.append(query_time)
                except Exception as e:
                    times.append(None)
            
            valid_times = [t for t in times if t is not None]
            if valid_times:
                results[f"case_{i+1}"] = {
                    'params': params,
                    'avg_time': sum(valid_times) / len(valid_times),
                    'min_time': min(valid_times),
                    'max_time': max(valid_times),
                    'success_rate': len(valid_times) / len(times)
                }
                
                print(f"  查询 {i+1} ({param_str}): 平均 {results[f'case_{i+1}']['avg_time']:.3f}s")
        
        self.results['database_performance'] = results
        return results
    
    def generate_report(self):
        """生成综合性能报告"""
        print("\n" + "="*60)
        print("综合性能测试报告")
        print("="*60)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'results': self.results
        }
        
        # 页面加载性能总结
        if 'page_load' in self.results:
            print("\n📊 页面加载性能:")
            for endpoint, data in self.results['page_load'].items():
                print(f"  {endpoint}: 平均 {data['avg_time']:.3f}s, "
                      f"成功率 {data['success_rate']:.1%}")
        
        # API性能总结
        if 'api_performance' in self.results:
            print("\n🔌 API性能:")
            for endpoint, data in self.results['api_performance'].items():
                print(f"  {endpoint}: 平均 {data['avg_time']:.3f}s, "
                      f"成功率 {data['success_rate']:.1%}")
        
        # 缓存效果总结
        if 'cache_effectiveness' in self.results:
            data = self.results['cache_effectiveness']
            print(f"\n💾 缓存效果: 平均提升 {data['improvement_percent']:.1f}%")
        
        # 并发性能总结
        if 'concurrent_performance' in self.results:
            print("\n⚡ 并发性能:")
            for level, data in self.results['concurrent_performance'].items():
                print(f"  {level}并发: 成功率 {data['success_rate']:.1%}, "
                      f"平均时间 {data['avg_duration']:.3f}s")
        
        # 数据库性能总结
        if 'database_performance' in self.results:
            print("\n🗄️ 数据库查询性能:")
            for case, data in self.results['database_performance'].items():
                print(f"  {case}: 平均 {data['avg_time']:.3f}s, "
                      f"成功率 {data['success_rate']:.1%}")
        
        # 保存详细报告
        with open('comprehensive_performance_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: comprehensive_performance_report.json")
        
        return report

def main():
    """主函数"""
    print("🚀 开始综合性能测试...")
    
    tester = ComprehensivePerformanceTester()
    
    try:
        # 执行各项测试
        tester.test_page_load_performance()
        tester.test_api_performance()
        tester.test_cache_effectiveness()
        tester.test_concurrent_requests()
        tester.test_image_optimization()
        tester.test_database_query_performance()
        
        # 生成报告
        tester.generate_report()
        
        print("\n✅ 综合性能测试完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 