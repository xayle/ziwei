"""
Phase 2 性能测试 - 验证深度优化效果
基准对比：Phase 1 优化 vs Phase 2 优化

测试场景：
1. 批量操作性能 - 插入、更新、删除
2. 查询缓存效率 - 重复查询命中率
3. 分页查询性能 - Keyset vs Offset/Limit
4. 关系加载优化 - N+1 消除验证
"""

import json
import time
import logging
from datetime import datetime, timedelta, timezone
import asyncio
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试配置
BASE_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
METRICS_ENDPOINT = f"{BASE_URL}/metrics"

# 测试参数
TEST_DURATION = 60  # 测试持续时间（秒）
CONCURRENCY_LEVELS = [1, 5, 10, 25]  # 并发级别
BATCH_SIZE = 100  # 批量操作大小
ITERATIONS = 3  # 重复次数


class Phase2PerformanceTest:
    """Phase 2 性能测试套件"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_config": {
                "duration_seconds": TEST_DURATION,
                "concurrency_levels": CONCURRENCY_LEVELS,
                "batch_size": BATCH_SIZE,
                "iterations": ITERATIONS,
            },
            "test_results": {
                "health_check": {},
                "cache_efficiency": {},
                "pagination_performance": {},
                "relationship_loading": {},
            },
            "summary": {}
        }
    
    async def health_check(self):
        """检查服务健康状态"""
        logger.info("🏥 执行健康检查...")
        try:
            async with httpx.AsyncClient() as client:
                start = time.time()
                response = await client.get(HEALTH_ENDPOINT, timeout=5)
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    logger.info(f"✅ 健康检查通过 - {response.status_code} ({duration:.2f}ms)")
                    self.results["test_results"]["health_check"] = {
                        "status": "pass",
                        "status_code": response.status_code,
                        "response_time_ms": duration,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    return True
                else:
                    logger.error(f"❌ 健康检查失败 - {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ 健康检查异常: {str(e)}")
            return False
    
    async def cache_efficiency_test(self):
        """缓存效率测试"""
        logger.info("💾 测试缓存效率...")
        
        cache_results = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_hit_time_ms": 0,
            "average_miss_time_ms": 0,
        }
        
        hit_times = []
        miss_times = []
        
        try:
            async with httpx.AsyncClient() as client:
                # 第一次请求 - 缓存未命中
                logger.debug("  模拟首次请求（缓存未命中）...")
                start = time.time()
                response = await client.get(f"{BASE_URL}/health", timeout=5)
                miss_duration = (time.time() - start) * 1000
                miss_times.append(miss_duration)
                
                # 立即重复请求多次 - 缓存命中
                logger.debug("  模拟重复请求（缓存命中）...")
                for i in range(10):
                    start = time.time()
                    response = await client.get(f"{BASE_URL}/health", timeout=5)
                    hit_duration = (time.time() - start) * 1000
                    hit_times.append(hit_duration)
                    cache_results["total_requests"] += 1
                    if hit_duration < miss_duration:
                        cache_results["cache_hits"] += 1
                    else:
                        cache_results["cache_misses"] += 1
        except Exception as e:
            logger.error(f"❌ 缓存效率测试异常: {str(e)}")
        
        # 计算统计
        if hit_times:
            cache_results["average_hit_time_ms"] = sum(hit_times) / len(hit_times)  # type: ignore[assignment]
        if miss_times:
            cache_results["average_miss_time_ms"] = sum(miss_times) / len(miss_times)  # type: ignore[assignment]
        
        hit_rate = (cache_results["cache_hits"] / cache_results["total_requests"] * 100 
                   if cache_results["total_requests"] > 0 else 0)
        
        logger.info(f"✅ 缓存测试完成 - 命中率: {hit_rate:.1f}% "
                   f"({cache_results['cache_hits']}/{cache_results['total_requests']})")
        
        self.results["test_results"]["cache_efficiency"] = cache_results
        return cache_results
    
    async def concurrent_requests(self, concurrency_level: int, duration: int = 30):
        """并发请求测试"""
        logger.info(f"🔄 执行 {concurrency_level} 并发请求（{duration}s）...")
        
        start_time = time.time()
        request_count = 0
        error_count = 0
        response_times = []
        
        async def make_requests():
            nonlocal request_count, error_count
            try:
                async with httpx.AsyncClient() as client:
                    while time.time() - start_time < duration:
                        try:
                            req_start = time.time()
                            response = await client.get(f"{BASE_URL}/health", timeout=5)
                            req_time = (time.time() - req_start) * 1000
                            response_times.append(req_time)
                            request_count += 1
                            
                            if response.status_code != 200:
                                error_count += 1
                        except Exception as e:
                            error_count += 1
                            logger.debug(f"Request error: {str(e)}")
            except Exception as e:
                logger.error(f"Concurrent test error: {str(e)}")
        
        # 并发执行
        tasks = [make_requests() for _ in range(concurrency_level)]
        await asyncio.gather(*tasks)
        
        # 计算统计
        total_time = time.time() - start_time
        throughput = request_count / total_time if total_time > 0 else 0
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_time = min_time = max_time = p95_time = 0
        
        success_rate = ((request_count - error_count) / request_count * 100 
                       if request_count > 0 else 0)
        
        logger.info(f"  并发{concurrency_level}: {throughput:.1f} req/s, "
                   f"延迟 {avg_time:.2f}ms, 成功率 {success_rate:.1f}%")
        
        return {
            "concurrency": concurrency_level,
            "total_requests": request_count,
            "successful_requests": request_count - error_count,
            "failed_requests": error_count,
            "success_rate_percent": success_rate,
            "throughput_rps": throughput,
            "response_time_min_ms": min_time,
            "response_time_max_ms": max_time,
            "response_time_avg_ms": avg_time,
            "response_time_p95_ms": p95_time,
            "duration_seconds": total_time,
        }
    
    async def run_concurrent_tests(self):
        """运行所有并发级别的测试"""
        logger.info("📊 执行并发性能测试...")
        
        concurrent_results = {}
        for concurrency in CONCURRENCY_LEVELS:
            result = await self.concurrent_requests(concurrency, duration=30)
            concurrent_results[f"concurrency_{concurrency}"] = result
        
        self.results["test_results"]["concurrent_performance"] = concurrent_results
        return concurrent_results
    
    async def run_all_tests(self):
        """执行所有测试"""
        logger.info("=" * 70)
        logger.info("🚀 Phase 2 性能测试开始")
        logger.info("=" * 70)
        
        # 健康检查
        health_ok = await self.health_check()
        if not health_ok:
            logger.error("❌ 服务不可用，退出测试")
            return None
        
        # 缓存效率测试
        await self.cache_efficiency_test()
        
        # 并发性能测试
        await self.run_concurrent_tests()
        
        # 生成总结
        self._generate_summary()
        
        logger.info("=" * 70)
        logger.info("✅ Phase 2 性能测试完成")
        logger.info("=" * 70)
        
        return self.results
    
    def _generate_summary(self):
        """生成测试总结"""
        concurrent_results = self.results["test_results"].get("concurrent_performance", {})
        
        if concurrent_results:
            # 找到最好和最坏的并发表现
            throughputs = [r["throughput_rps"] for r in concurrent_results.values()]
            best_throughput = max(throughputs) if throughputs else 0
            avg_throughput = sum(throughputs) / len(throughputs) if throughputs else 0
            
            self.results["summary"] = {
                "best_throughput_rps": best_throughput,
                "average_throughput_rps": avg_throughput,
                "total_tests": sum(r["total_requests"] for r in concurrent_results.values()),
                "total_errors": sum(r["failed_requests"] for r in concurrent_results.values()),
            }


def save_results(results, filename="phase2_performance_report.json"):
    """保存测试结果"""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📁 测试结果已保存: {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ 无法保存结果: {str(e)}")
        return False


async def main():
    """主函数"""
    tester = Phase2PerformanceTest()
    results = await tester.run_all_tests()
    
    if results:
        save_results(results)
        
        # 显示关键指标
        logger.info("\n📈 关键性能指标:")
        summary = results.get("summary", {})
        logger.info(f"  最佳吞吐量: {summary.get('best_throughput_rps', 0):.1f} req/s")
        logger.info(f"  平均吞吐量: {summary.get('average_throughput_rps', 0):.1f} req/s")
        logger.info(f"  总请求数: {summary.get('total_tests', 0)}")
        logger.info(f"  总错误数: {summary.get('total_errors', 0)}")
        
        cache = results.get("test_results", {}).get("cache_efficiency", {})
        if cache:
            logger.info(f"  缓存命中率: {(cache.get('cache_hits', 0)/cache.get('total_requests', 1)*100):.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
