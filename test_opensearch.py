#!/usr/bin/env python3
import logging
import os
import pytest
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import warnings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("opensearch-test")

def get_os_config():
    """从环境变量获取OpenSearch配置"""
    # 加载.env文件中的环境变量
    load_dotenv()
    config = {
        "host": os.getenv("OPENSEARCH_HOST", "https://localhost:9200"),
        "username": os.getenv("OPENSEARCH_USERNAME"),
        "password": os.getenv("OPENSEARCH_PASSWORD")
    }
    
    if not all([config["username"], config["password"]]):
        logger.error("缺少必要的OpenSearch配置。请检查环境变量：")
        logger.error("OPENSEARCH_USERNAME和OPENSEARCH_PASSWORD是必需的")
        raise ValueError("缺少必要的OpenSearch配置")
    
    return config

@pytest.fixture
def client():
    """创建并返回一个OpenSearch客户端"""
    config = get_os_config()
    logger.info(f"使用以下配置连接OpenSearch: {config['host']}")

    # 禁用SSL警告
    warnings.filterwarnings("ignore", message=".*SSL.*")

    return OpenSearch(
        hosts=[config["host"]],
        http_auth=(config["username"], config["password"]),
        verify_certs=False,
        ssl_show_warn=False
    )

@pytest.mark.asyncio
async def test_list_indices(client):
    """测试列出所有索引"""
    logger.info("测试 list_indices...")
    try:
        indices = client.cat.indices(format="json")
        logger.info(f"索引列表: {indices}")
        assert True
    except Exception as e:
        logger.error(f"列出索引时出错: {e}")
        assert False

@pytest.mark.asyncio
async def test_get_cluster_health(client):
    """测试获取集群健康状态"""
    logger.info("测试 get_cluster_health...")
    try:
        response = client.cluster.health()
        logger.info(f"集群健康状态: {response}")
        assert True
    except Exception as e:
        logger.error(f"获取集群健康状态时出错: {e}")
        assert False

@pytest.mark.asyncio
async def test_get_cluster_stats(client):
    """测试获取集群统计信息"""
    logger.info("测试 get_cluster_stats...")
    try:
        response = client.cluster.stats()
        logger.info(f"集群统计信息: {response}")
        assert True
    except Exception as e:
        logger.error(f"获取集群统计信息时出错: {e}")
        assert False

async def run_tests():
    """运行所有测试"""
    try:
        # 创建OpenSearch客户端
        client = create_opensearch_client()
        
        # 运行所有测试
        results = []
        results.append(await test_list_indices(client))
        results.append(await test_get_cluster_health(client))
        results.append(await test_get_cluster_stats(client))
        
        # 输出测试结果摘要
        tests = ["list_indices", "get_cluster_health", "get_cluster_stats"]
        logger.info("测试结果摘要:")
        for i, test in enumerate(tests):
            status = "成功" if results[i] else "失败"
            logger.info(f"{test}: {status}")
        
        # 检查SSL配置
        if not any(results):
            logger.warning("所有测试都失败。如果看到SSL错误，可能需要检查以下几点:")
            logger.warning("1. 确保OpenSearch服务器正在运行")
            logger.warning("2. 检查.env文件中的OPENSEARCH_HOST配置是否正确")
            logger.warning("3. 如果服务器不需要SSL，尝试将URL从https://改为http://")
            
    except Exception as e:
        logger.error(f"运行测试时出错: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_tests()) 