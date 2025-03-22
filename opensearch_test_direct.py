#!/usr/bin/env python3
"""
OpenSearch Direct Test Script
Used to verify connection to OpenSearch and retrieve index and cluster information
"""

import os
import sys
import json
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import warnings

# Disable SSL warnings
warnings.filterwarnings("ignore", message=".*SSL.*")

def get_opensearch_config():
    """Get OpenSearch configuration from environment variables"""
    # Load environment variables from .env file
    load_dotenv()
    
    host = os.getenv("OPENSEARCH_HOST", "https://localhost:9200")
    username = os.getenv("OPENSEARCH_USERNAME")
    password = os.getenv("OPENSEARCH_PASSWORD")
    
    # Validate required configuration
    if not username or not password:
        print("Error: Missing required OpenSearch configuration")
        print("Please ensure OPENSEARCH_USERNAME and OPENSEARCH_PASSWORD are set in environment variables")
        sys.exit(1)
    
    return {
        "host": host,
        "username": username,
        "password": password
    }

def create_client(config):
    """Create OpenSearch client"""
    print(f"Connecting to OpenSearch server: {config['host']}")
    
    return OpenSearch(
        hosts=[config['host']],
        http_auth=(config['username'], config['password']),
        verify_certs=False,
        ssl_show_warn=False
    )

def pretty_print_json(data):
    """Format and print JSON data"""
    if isinstance(data, str):
        try:
            # Try to parse JSON string
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except:
            # If not valid JSON, return as is
            return data
    else:
        # If it's a dictionary or list, format directly
        return json.dumps(data, indent=2, ensure_ascii=False)

def test_opensearch():
    """Execute OpenSearch tests"""
    try:
        # Get configuration and create client
        config = get_opensearch_config()
        client = create_client(config)
        
        # Test 1: Cluster health status
        print("\n===== Cluster Health Status =====")
        try:
            health = client.cluster.health()
            print(pretty_print_json(health))
            print("Cluster health status check: Success ✓")
        except Exception as e:
            print(f"Cluster health status check: Failed ✗ - {e}")
        
        # Test 2: Cluster statistics
        print("\n===== Cluster Statistics =====")
        try:
            stats = client.cluster.stats()
            # Only print key information, otherwise too much
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
            print("Cluster statistics check: Success ✓")
        except Exception as e:
            print(f"Cluster statistics check: Failed ✗ - {e}")
        
        # Test 3: Index list
        print("\n===== Index List =====")
        try:
            indices = client.cat.indices(format="json")
            print(pretty_print_json(indices))
            print("Index list check: Success ✓")
        except Exception as e:
            print(f"Index list check: Failed ✗ - {e}")
            
        # Connection test summary
        print("\n===== Test Summary =====")
        print("OpenSearch server: " + config['host'])
        print("Connection status: Successfully connected to OpenSearch server")
        
    except Exception as e:
        print("\n===== Test Failed =====")
        print(f"Unable to connect to OpenSearch server: {e}")
        print("\nPossible solutions:")
        print("1. Ensure OpenSearch server is running")
        print("2. Check connection configuration in .env file is correct")
        print("3. If server doesn't require SSL, try changing URL from https:// to http://")
        print("4. Verify username and password are correct")

if __name__ == "__main__":
    test_opensearch() 