import logging
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch
import warnings

class OpenSearchClient:
    
    def __init__(self, logger=None):         
        self.logger = logger
        self.os_client = self._create_opensearch_client()
        
    def _get_os_config(self):
        """Get OpenSearch configuration from environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        config = {
            "host": os.getenv("OPENSEARCH_HOST"),
            "username": os.getenv("OPENSEARCH_USERNAME"),
            "password": os.getenv("OPENSEARCH_PASSWORD")
        }
        
        if not all([config["username"], config["password"]]):
            self.logger.error("Missing required OpenSearch configuration. Please check environment variables:")
            self.logger.error("OPENSEARCH_USERNAME and OPENSEARCH_PASSWORD are required")
            raise ValueError("Missing required OpenSearch configuration")
        
        return config

    def _create_opensearch_client(self) -> OpenSearch:
        """Create and return an OpenSearch client using configuration from environment."""
        config = self._get_os_config()

        # Disable SSL warnings
        warnings.filterwarnings("ignore", message=".*SSL.*",)

        return OpenSearch(
            hosts=[config["host"]],
            http_auth=(config["username"], config["password"]),
            verify_certs=False,
            ssl_show_warn=False
        ) 