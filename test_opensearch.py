#!/usr/bin/env python3
import logging
import os
import pytest
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("opensearch-test")

def get_os_config():
    """Get OpenSearch configuration from environment variables"""
    # Load environment variables from .env file
    load_dotenv()
    config = {
        "host": os.getenv("OPENSEARCH_HOST", "https://localhost:9200"),
        "username": os.getenv("OPENSEARCH_USERNAME"),
        "password": os.getenv("OPENSEARCH_PASSWORD")
    }
    
    if not all([config["username"], config["password"]]):
        logger.error("Missing required OpenSearch configuration. Please check environment variables:")
        logger.error("OPENSEARCH_USERNAME and OPENSEARCH_PASSWORD are required")
        raise ValueError("Missing required OpenSearch configuration")
    
    return config

@pytest.fixture
def client():
    """Create and return an OpenSearch client"""
    config = get_os_config()
    logger.info(f"Connecting to OpenSearch with configuration: {config['host']}")

    # Disable SSL warnings
    warnings.filterwarnings("ignore", message=".*SSL.*")

    return OpenSearch(
        hosts=[config["host"]],
        http_auth=(config["username"], config["password"]),
        verify_certs=False,
        ssl_show_warn=False
    )

@pytest.mark.asyncio
async def test_list_indices(client):
    """Test listing all indices"""
    logger.info("Testing list_indices...")
    try:
        indices = client.cat.indices(format="json")
        logger.info(f"Indices list: {indices}")
        assert True
    except Exception as e:
        logger.error(f"Error listing indices: {e}")
        assert False

@pytest.mark.asyncio
async def test_get_cluster_health(client):
    """Test getting cluster health status"""
    logger.info("Testing get_cluster_health...")
    try:
        response = client.cluster.health()
        logger.info(f"Cluster health status: {response}")
        assert True
    except Exception as e:
        logger.error(f"Error getting cluster health: {e}")
        assert False

@pytest.mark.asyncio
async def test_get_cluster_stats(client):
    """Test getting cluster statistics"""
    logger.info("Testing get_cluster_stats...")
    try:
        response = client.cluster.stats()
        logger.info(f"Cluster statistics: {response}")
        assert True
    except Exception as e:
        logger.error(f"Error getting cluster statistics: {e}")
        assert False

async def run_tests():
    """Run all tests"""
    try:
        # Create OpenSearch client
        client = create_opensearch_client()
        
        # Run all tests
        results = []
        results.append(await test_list_indices(client))
        results.append(await test_get_cluster_health(client))
        results.append(await test_get_cluster_stats(client))
        
        # Output test results summary
        tests = ["list_indices", "get_cluster_health", "get_cluster_stats"]
        logger.info("Test results summary:")
        for i, test in enumerate(tests):
            status = "Success" if results[i] else "Failed"
            logger.info(f"{test}: {status}")
        
        # Check SSL configuration
        if not any(results):
            logger.warning("All tests failed. If you see SSL errors, you may need to check the following:")
            logger.warning("1. Ensure OpenSearch server is running")
            logger.warning("2. Check OPENSEARCH_HOST configuration in .env file")
            logger.warning("3. If server doesn't require SSL, try changing URL from https:// to http://")
            
    except Exception as e:
        logger.error(f"Error running tests: {e}")

if __name__ == "__main__":
    # Run tests
    asyncio.run(run_tests()) 