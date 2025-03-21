#!/usr/bin/env python3
"""
OpenSearch MCP Server
A server for exposing OpenSearch functionality through MCP
"""

from . import server


def main():
    """Main entry point for the package."""
    server.main()


# Optionally expose other important items at package level
__all__ = ["main", "server"]