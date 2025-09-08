#!/usr/bin/env python3
"""
Command-line interface for the search agent.
Provides indexing and search functionality via CLI.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .config import get_config
from .indexer import FileIndexer
from .search import SearchEngine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def index_command(args):
    """Handle index command."""
    config = get_config()
    indexer = FileIndexer(config['database_path'])
    
    try:
        result = await indexer.index_folder(
            args.path, 
            full_reindex=args.full,
            priority=args.priority
        )
        
        print(json.dumps({
            "indexed": result["indexed"],
            "skipped": result["skipped"], 
            "removed": result["removed"],
            "duration_ms": result["duration_ms"]
        }, indent=2))
        
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        sys.exit(1)


async def search_command(args):
    """Handle search command."""
    config = get_config()
    search_engine = SearchEngine(config['database_path'])
    
    try:
        results = await search_engine.search(
            query=args.query,
            k=args.limit,
            offset=args.offset,
            file_extensions=args.extensions.split(',') if args.extensions else None,
            years=args.years.split(',') if args.years else None,
            roots=args.roots.split(',') if args.roots else None
        )
        
        print(json.dumps(results, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Smart File Search CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index files in a folder')
    index_parser.add_argument('path', help='Path to folder to index')
    index_parser.add_argument('--full', action='store_true', help='Force full reindex')
    index_parser.add_argument('--priority', choices=['low', 'normal', 'high'], 
                             default='normal', help='Indexing priority')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search indexed files')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Number of results')
    search_parser.add_argument('--offset', type=int, default=0, help='Results offset')
    search_parser.add_argument('--extensions', help='Comma-separated file extensions')
    search_parser.add_argument('--years', help='Comma-separated years')
    search_parser.add_argument('--roots', help='Comma-separated root paths')
    
    args = parser.parse_args()
    
    if args.command == 'index':
        asyncio.run(index_command(args))
    elif args.command == 'search':
        asyncio.run(search_command(args))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
