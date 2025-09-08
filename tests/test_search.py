"""
Test search functionality.
"""

import pytest
import tempfile
import os
import sqlite3
from pathlib import Path

from search_agent.search import SearchEngine
from search_agent.indexer import FileIndexer
from search_agent.config import get_config


@pytest.fixture
async def indexed_db():
    """Create a database with indexed test content."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test content
        test_files = {
            "python_guide.md": """
            # Python Programming Guide
            
            Python is a powerful programming language used for:
            - Web development
            - Data analysis  
            - Machine learning
            - Automation scripts
            """,
            "javascript_intro.txt": """
            JavaScript Introduction
            
            JavaScript is a versatile language for web development.
            It runs in browsers and can also run on servers with Node.js.
            """,
            "data_analysis.py": """
            # Data Analysis Script
            import pandas as pd
            import numpy as np
            
            def analyze_data(df):
                return df.describe()
            """,
            "config.json": """
            {
                "database": {
                    "host": "localhost",
                    "port": 5432
                },
                "features": ["search", "analysis"]
            }
            """
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
        
        # Index the content
        indexer = FileIndexer(db_path)
        
        # Mock config
        original_config = get_config
        
        def mock_config():
            config = original_config()
            config['allowed_roots'] = [temp_dir]
            return config
        
        import search_agent.indexer
        search_agent.indexer.get_config = mock_config
        
        try:
            await indexer.index_folder(temp_dir)
        finally:
            search_agent.indexer.get_config = original_config
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.mark.asyncio
async def test_basic_search(indexed_db):
    """Test basic search functionality."""
    search_engine = SearchEngine(indexed_db)
    
    # Search for Python content
    results = await search_engine.search("Python programming")
    
    assert len(results['items']) > 0
    assert results['pagination']['total_estimate'] > 0
    
    # Check that Python-related content is returned
    found_python = any('python' in item['snippet'].lower() 
                      for item in results['items'])
    assert found_python


@pytest.mark.asyncio
async def test_search_with_filters(indexed_db):
    """Test search with file extension filters."""
    search_engine = SearchEngine(indexed_db)
    
    # Search only in Python files
    results = await search_engine.search(
        "data analysis", 
        file_extensions=[".py"]
    )
    
    # Should only return .py files
    for item in results['items']:
        assert item['path'].endswith('.py')


@pytest.mark.asyncio
async def test_search_pagination(indexed_db):
    """Test search pagination."""
    search_engine = SearchEngine(indexed_db)
    
    # Get first page
    page1 = await search_engine.search("development", k=2, offset=0)
    
    # Get second page  
    page2 = await search_engine.search("development", k=2, offset=2)
    
    # Pages should be different
    if len(page1['items']) > 0 and len(page2['items']) > 0:
        assert page1['items'][0]['path'] != page2['items'][0]['path']


@pytest.mark.asyncio
async def test_empty_query(indexed_db):
    """Test handling of empty query."""
    search_engine = SearchEngine(indexed_db)
    
    results = await search_engine.search("")
    
    # Should handle gracefully
    assert 'items' in results
    assert 'pagination' in results


@pytest.mark.asyncio
async def test_special_characters_query(indexed_db):
    """Test search with special characters."""
    search_engine = SearchEngine(indexed_db)
    
    # Test query with quotes and special chars
    results = await search_engine.search('"web development"')
    
    assert 'items' in results
    assert results['pagination']['total_estimate'] >= 0


@pytest.mark.asyncio
async def test_file_preview(indexed_db):
    """Test file preview functionality."""
    search_engine = SearchEngine(indexed_db)
    
    # First, find a file to preview
    results = await search_engine.search("Python")
    
    if len(results['items']) > 0:
        item = results['items'][0]
        
        preview = await search_engine.get_file_preview(
            item['path'], 
            item.get('pointer'),
            before=100,
            after=100
        )
        
        assert 'path' in preview
        assert 'preview' in preview
        assert len(preview['preview']) > 0


@pytest.mark.asyncio
async def test_search_no_results(indexed_db):
    """Test search with no matching results."""
    search_engine = SearchEngine(indexed_db)
    
    results = await search_engine.search("nonexistentterms12345")
    
    assert results['items'] == []
    assert results['pagination']['total_estimate'] == 0


@pytest.mark.asyncio
async def test_build_fts_query():
    """Test FTS query building."""
    search_engine = SearchEngine()
    
    # Test phrase handling
    query1 = search_engine._build_fts_query('"exact phrase"')
    assert '"exact phrase"' in query1
    
    # Test multiple terms
    query2 = search_engine._build_fts_query('python data analysis')
    assert 'python' in query2 or 'data' in query2 or 'analysis' in query2
    
    # Test empty query
    query3 = search_engine._build_fts_query('')
    assert query3 == '*'


def test_build_filters():
    """Test filter building functionality."""
    search_engine = SearchEngine()
    
    # Test extension filter
    where_clauses, params = search_engine._build_filters(
        file_extensions=['.py', '.js'],
        years=None,
        roots=None
    )
    
    assert len(where_clauses) > 0
    assert '.py' in params
    assert '.js' in params
    
    # Test year filter
    where_clauses, params = search_engine._build_filters(
        file_extensions=None,
        years=['2024'],
        roots=None
    )
    
    assert len(where_clauses) > 0
    
    # Test root filter
    where_clauses, params = search_engine._build_filters(
        file_extensions=None,
        years=None,
        roots=['/path/to/docs']
    )
    
    assert len(where_clauses) > 0
    assert '/path/to/docs%' in params
