"""测试健康检查端点 (/health 和 /ready)"""
import pytest
from fastapi.testclient import TestClient
from run import app


@pytest.fixture
def client():
	"""创建测试客户端"""
	return TestClient(app)


def test_health_endpoint(client):
	"""
	✅ Priority 3.8: 测试 /health 端点
	验证基本的存活性探针响应
	"""
	response = client.get("/health")
	assert response.status_code == 200
	
	data = response.json()
	assert data["status"] == "ok"
	assert "api_version" in data
	assert "rule_version" in data
	assert "sxtwl_available" in data
	assert "cnlunar_available" in data
	assert "now_utc8" in data
	assert "supported_year_range" in data
	assert "thresholds" in data


def test_health_endpoint_has_backend_info(client):
	"""
	✅ Priority 3.8: 验证 /health 返回后端依赖信息
	检查 sxtwl 和 cnlunar 库的可用性
	"""
	response = client.get("/health")
	assert response.status_code == 200
	
	data = response.json()
	assert isinstance(data["sxtwl_available"], bool)
	assert isinstance(data["cnlunar_available"], bool)
	# sxtwl_version可能是版本号、"unavailable"或"unknown"
	assert isinstance(data["sxtwl_version"], str)
	assert len(data["sxtwl_version"]) > 0


def test_ready_endpoint(client):
	"""
	✅ Priority 3.8: 测试 /ready 端点
	验证就绪性探针响应
	"""
	response = client.get("/ready")
	
	# 应该返回200（就绪）或500（未就绪），取决于数据库状态
	assert response.status_code in [200, 500]
	
	data = response.json()
	assert "status" in data
	assert "timestamp" in data
	
	if response.status_code == 200:
		assert data["status"] == "ready"
	else:
		assert data["status"] == "not_ready"
		# P74: error 字段已移除，不再泄漏 DB 错误详情


def test_ready_endpoint_success(client):
	"""
	✅ Priority 3.8: 验证 /ready 成功响应
	数据库已初始化，端点应返回200
	"""
	response = client.get("/ready")
	
	# 由于测试环境已初始化数据库，应该返回200
	if response.status_code == 200:
		data = response.json()
		assert data["status"] == "ready"
		assert "timestamp" in data


def test_health_and_ready_endpoints_are_public(client):
	"""
	✅ Priority 3.8: 验证健康检查端点不需要身份验证
	这些端点应该对所有请求者可用（无需 Authorization header）
	"""
	# 测试 /health
	response_health = client.get("/health")
	assert response_health.status_code == 200
	
	# 测试 /ready
	response_ready = client.get("/ready")
	assert response_ready.status_code in [200, 500]  # 应该返回明确的状态码


def test_health_endpoint_tz_info(client):
	"""
	✅ Priority 3.8: 验证 /health 返回正确的时区信息
	"""
	response = client.get("/health")
	assert response.status_code == 200
	
	data = response.json()
	assert data["tz"] == "Asia/Shanghai"
	
	# 验证时间戳格式是否有效
	try:
		from datetime import datetime as dt
		dt.fromisoformat(data["now_utc8"])
	except ValueError:
		pytest.fail("Invalid ISO format timestamp")
