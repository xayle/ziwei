#!/usr/bin/env python3
"""
性能基准测试脚本
测试应用在不同并发级别下的性能表现
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict, Any
import aiohttp  # type: ignore[import]
from datetime import datetime

# 测试配置
API_BASE_URL = "http://127.0.0.1:8000"
ENDPOINTS = {
    "health": "/health",
    "metrics": "/metrics",
    "docs": "/docs",
}

# 测试数据
TEST_EVENT_PAYLOAD = {
    "user_id": "test_user_123",
    "bazi_json": {
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "正", "branch": "寅"},
        "day": {"stem": "甲", "branch": "子"},
        "hour": {"stem": "甲", "branch": "子"}
    },
    "location": {"longitude": 120.5, "latitude": 30.5},
    "timestamp": datetime.now().isoformat()
}


class PerformanceBenchmark:
    def __init__(self):
        self.results: Dict[str, List[float]] = {endpoint: [] for endpoint in ENDPOINTS.keys()}
        self.errors: Dict[str, int] = {endpoint: 0 for endpoint in ENDPOINTS.keys()}
        self.start_time = None
        self.end_time = None

    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint_name: str, url: str) -> None:
        """测试单个端点"""
        try:
            start = time.time()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                await response.read()
                duration = (time.time() - start) * 1000  # 转换为毫秒
                if response.status == 200:
                    self.results[endpoint_name].append(duration)
                else:
                    self.errors[endpoint_name] += 1
        except asyncio.TimeoutError:
            self.errors[endpoint_name] += 1
        except Exception as e:
            self.errors[endpoint_name] += 1

    async def run_concurrent_tests(self, concurrency: int, requests_per_endpoint: int) -> None:
        """运行并发测试"""
        connector = aiohttp.TCPConnector(limit=concurrency)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []

            # 为每个端点创建多个请求任务
            for endpoint_name, endpoint_path in ENDPOINTS.items():
                url = f"{API_BASE_URL}{endpoint_path}"
                for _ in range(requests_per_endpoint):
                    tasks.append(self.test_endpoint(session, endpoint_name, url))

            # 执行所有任务
            self.start_time = time.time()
            await asyncio.gather(*tasks)
            self.end_time = time.time()

    def calculate_statistics(self) -> Dict[str, Any]:
        """计算统计数据"""
        stats = {}

        for endpoint_name, times in self.results.items():
            if times:
                stats[endpoint_name] = {
                    "requests": len(times),
                    "errors": self.errors[endpoint_name],
                    "min_ms": round(min(times), 2),
                    "max_ms": round(max(times), 2),
                    "mean_ms": round(statistics.mean(times), 2),
                    "median_ms": round(statistics.median(times), 2),
                    "stdev_ms": round(statistics.stdev(times), 2) if len(times) > 1 else 0,
                    "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 2) if times else 0,
                    "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 2) if times else 0,
                }
            else:
                stats[endpoint_name] = {
                    "requests": 0,
                    "errors": self.errors[endpoint_name],
                    "min_ms": 0,
                    "max_ms": 0,
                    "mean_ms": 0,
                    "median_ms": 0,
                    "stdev_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                }

        # 添加总体统计
        all_times = [t for times in self.results.values() for t in times]
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        total_requests = sum(len(times) for times in self.results.values())
        total_errors = sum(self.errors.values())

        stats["overall"] = {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "success_rate": round(100 * (total_requests - total_errors) / total_requests, 2) if total_requests > 0 else 0,
            "total_duration_sec": round(total_time, 2),
            "throughput_req_sec": round(total_requests / total_time, 2) if total_time > 0 else 0,
            "overall_mean_ms": round(statistics.mean(all_times), 2) if all_times else 0,
            "overall_p95_ms": round(sorted(all_times)[int(len(all_times) * 0.95)], 2) if all_times else 0,
            "overall_p99_ms": round(sorted(all_times)[int(len(all_times) * 0.99)], 2) if all_times else 0,
        }

        return stats

    async def run_benchmark(self) -> Dict[str, Any]:
        """运行完整的基准测试"""
        print("\n" + "="*70)
        print("🚀 BaZi Service 性能基准测试")
        print("="*70)

        benchmark_results = {}

        # 测试不同并发级别
        concurrency_levels = [1, 5, 10, 25, 50]  # 串行，5个，10个，25个，50个并发
        requests_per_endpoint = 20

        for concurrency in concurrency_levels:
            print(f"\n📊 测试并发级别: {concurrency} 并发用户")
            print(f"   每个端点请求数: {requests_per_endpoint}")
            print("-" * 70)

            # 重置结果
            self.results = {endpoint: [] for endpoint in ENDPOINTS.keys()}
            self.errors = {endpoint: 0 for endpoint in ENDPOINTS.keys()}

            # 运行测试
            await self.run_concurrent_tests(concurrency, requests_per_endpoint)

            # 获取统计信息
            stats = self.calculate_statistics()
            benchmark_results[f"concurrency_{concurrency}"] = {
                "concurrency": concurrency,
                "stats": stats
            }

            # 打印结果
            print(f"\n✅ 结果统计:")
            print(f"   总请求数: {stats['overall']['total_requests']}")
            print(f"   总错误数: {stats['overall']['total_errors']}")
            print(f"   成功率: {stats['overall']['success_rate']}%")
            print(f"   持续时间: {stats['overall']['total_duration_sec']}s")
            print(f"   吞吐量: {stats['overall']['throughput_req_sec']} req/s")
            print(f"   平均延迟: {stats['overall']['overall_mean_ms']}ms")
            print(f"   P95延迟: {stats['overall']['overall_p95_ms']}ms")
            print(f"   P99延迟: {stats['overall']['overall_p99_ms']}ms")

            # 按端点显示详情
            print(f"\n   📈 端点详情:")
            for endpoint_name, endpoint_stats in stats.items():
                if endpoint_name != "overall":
                    print(f"      {endpoint_name}:")
                    print(f"        - 请求: {endpoint_stats['requests']}, 错误: {endpoint_stats['errors']}")
                    print(f"        - 延迟: min={endpoint_stats['min_ms']}ms, " +
                          f"mean={endpoint_stats['mean_ms']}ms, max={endpoint_stats['max_ms']}ms")

        return benchmark_results


async def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_benchmark()

    # 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "api_base_url": API_BASE_URL,
        "test_summary": {
            "total_concurrency_levels": len(results),
            "endpoints_tested": len(ENDPOINTS),
            "total_test_duration": sum(
                r["stats"]["overall"]["total_duration_sec"] for r in results.values()
            )
        },
        "detailed_results": results
    }

    # 保存到文件
    report_file = "performance_benchmark_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print(f"✅ 性能测试完成！")
    print(f"📄 详细报告已保存到: {report_file}")
    print("="*70 + "\n")

    # 打印关键指标总结
    print("\n📊 关键性能指标汇总:")
    print("-" * 70)
    for concurrency_key, data in results.items():
        concurrency = data["concurrency"]
        stats = data["stats"]["overall"]
        print(f"\n🔹 {concurrency} 并发用户:")
        print(f"   吞吐量: {stats['throughput_req_sec']} req/s")
        print(f"   平均延迟: {stats['overall_mean_ms']}ms")
        print(f"   P95延迟: {stats['overall_p95_ms']}ms")
        print(f"   成功率: {stats['success_rate']}%")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())
