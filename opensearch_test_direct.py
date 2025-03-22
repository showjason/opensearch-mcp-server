# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
OpenSearch 直接测试脚本
用于验证与OpenSearch的连接并获取索引和集群信息
"""

import os
import sys
import json
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import warnings

# 禁用SSL警告
warnings.filterwarnings("ignore", message=".*SSL.*")

def get_opensearch_config():
    """从环境变量获取OpenSearch配置"""
    # 加载.env文件中的环境变量
    load_dotenv()
    
    host = os.getenv("OPENSEARCH_HOST", "https://localhost:9200")
    username = os.getenv("OPENSEARCH_USERNAME")
    password = os.getenv("OPENSEARCH_PASSWORD")
    
    # 验证必要的配置
    if not username or not password:
        print("错误: 缺少必要的OpenSearch配置")
        print("请确保环境变量中设置了OPENSEARCH_USERNAME和OPENSEARCH_PASSWORD")
        sys.exit(1)
    
    return {
        "host": host,
        "username": username,
        "password": password
    }

def create_client(config):
    """创建OpenSearch客户端"""
    print(f"连接到OpenSearch服务器: {config['host']}")
    
    return OpenSearch(
        hosts=[config['host']],
        http_auth=(config['username'], config['password']),
        verify_certs=False,
        ssl_show_warn=False
    )

def pretty_print_json(data):
    """格式化打印JSON数据"""
    if isinstance(data, str):
        try:
            # 尝试解析JSON字符串
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except:
            # 如果不是有效的JSON，直接返回
            return data
    else:
        # 如果是字典或列表，直接格式化
        return json.dumps(data, indent=2, ensure_ascii=False)

def test_opensearch():
    """执行OpenSearch测试"""
    try:
        # 获取配置并创建客户端
        config = get_opensearch_config()
        client = create_client(config)
        
        # 测试1: 集群健康状态
        print("\n===== 集群健康状态 =====")
        try:
            health = client.cluster.health()
            print(pretty_print_json(health))
            print("集群健康状态检查: 成功 ✓")
        except Exception as e:
            print(f"集群健康状态检查: 失败 ✗ - {e}")
        
        # 测试2: 集群统计信息
        print("\n===== 集群统计信息 =====")
        try:
            stats = client.cluster.stats()
            # 只打印部分关键信息，否则太多
            if isinstance(stats, dict):
                summary = {
                    "cluster_name": stats.get("cluster_name"),
                    "status": stats.get("status"),
                    "indices_count": stats.get("indices", {}).get("count"),
                    "shards_total": stats.get("indices", {}).get("shards", {}).get("total"),
                    "nodes_count": stats.get("nodes", {}).get("count", {})
                }
                print(pretty_print_json(summary))
            else:
                print(pretty_print_json(stats))
            print("集群统计信息检查: 成功 ✓")
        except Exception as e:
            print(f"集群统计信息检查: 失败 ✗ - {e}")
        
        # 测试3: 索引列表
        print("\n===== 索引列表 =====")
        try:
            indices = client.cat.indices(format="json")
            print(pretty_print_json(indices))
            print("索引列表检查: 成功 ✓")
        except Exception as e:
            print(f"索引列表检查: 失败 ✗ - {e}")
            
        # 连接测试总结
        print("\n===== 测试总结 =====")
        print("OpenSearch服务器: " + config['host'])
        print("连接状态: 已成功连接到OpenSearch服务器")
        
    except Exception as e:
        print("\n===== 测试失败 =====")
        print(f"无法连接到OpenSearch服务器: {e}")
        print("\n可能的解决方案:")
        print("1. 确保OpenSearch服务器正在运行")
        print("2. 检查.env文件中的连接配置是否正确")
        print("3. 如果服务器不需要SSL，尝试将URL从https://改为http://")
        print("4. 验证用户名和密码是否正确")

if __name__ == "__main__":
    test_opensearch() 