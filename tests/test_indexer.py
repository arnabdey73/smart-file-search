"""
Test file indexing functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sqlite3

from search_agent.indexer import FileIndexer
from search_agent.config import get_config


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_content_dir():
    """Create a temporary directory with test content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = {
            "test.txt": "This is a test text file with some content.",
            "document.md": "# Test Document\n\nThis is a markdown document with **bold** text.",
            "data.json": '{"key": "value", "number": 42}',
            "script.py": "#!/usr/bin/env python\nprint('Hello, world!')",
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        yield temp_dir


@pytest.mark.asyncio
async def test_indexer_initialization(temp_db):
    """Test that indexer initializes correctly."""
    indexer = FileIndexer(temp_db)
    
    # Check that database tables exist
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'files' in tables
        assert 'docs' in tables


@pytest.mark.asyncio
async def test_index_folder(temp_db, temp_content_dir):
    """Test indexing a folder with multiple files."""
    indexer = FileIndexer(temp_db)
    
    # Mock allowed roots for testing
    original_config = get_config
    
    def mock_config():
        config = original_config()
        config['allowed_roots'] = [temp_content_dir]
        return config
    
    import search_agent.indexer
    search_agent.indexer.get_config = mock_config
    
    try:
        result = await indexer.index_folder(temp_content_dir)
        
        # Check results
        assert result['indexed'] > 0
        assert result['skipped'] >= 0
        assert result['removed'] == 0
        assert result['duration_ms'] > 0
        
        # Verify files were indexed
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            file_count = cursor.fetchone()[0]
            assert file_count > 0
            
            cursor = conn.execute("SELECT COUNT(*) FROM docs")
            doc_count = cursor.fetchone()[0]
            assert doc_count > 0
            
    finally:
        # Restore original config
        search_agent.indexer.get_config = original_config


@pytest.mark.asyncio
async def test_incremental_indexing(temp_db, temp_content_dir):
    """Test that incremental indexing works correctly."""
    indexer = FileIndexer(temp_db)
    
    # Mock config
    original_config = get_config
    
    def mock_config():
        config = original_config()
        config['allowed_roots'] = [temp_content_dir]
        return config
    
    import search_agent.indexer
    search_agent.indexer.get_config = mock_config
    
    try:
        # First indexing
        result1 = await indexer.index_folder(temp_content_dir)
        assert result1['indexed'] > 0
        
        # Second indexing (should skip unchanged files)
        result2 = await indexer.index_folder(temp_content_dir)
        assert result2['skipped'] > 0
        assert result2['indexed'] == 0
        
        # Add a new file
        new_file = Path(temp_content_dir) / "new_file.txt"
        with open(new_file, 'w') as f:
            f.write("This is a new file")
        
        # Third indexing (should index the new file)
        result3 = await indexer.index_folder(temp_content_dir)
        assert result3['indexed'] > 0
        
    finally:
        search_agent.indexer.get_config = original_config


@pytest.mark.asyncio 
async def test_file_removal_detection(temp_db, temp_content_dir):
    """Test that removed files are detected and cleaned up."""
    indexer = FileIndexer(temp_db)
    
    # Mock config
    original_config = get_config
    
    def mock_config():
        config = original_config()
        config['allowed_roots'] = [temp_content_dir]
        return config
    
    import search_agent.indexer
    search_agent.indexer.get_config = mock_config
    
    try:
        # Index initial files
        result1 = await indexer.index_folder(temp_content_dir)
        initial_count = result1['indexed']
        
        # Remove a file
        test_file = Path(temp_content_dir) / "test.txt"
        if test_file.exists():
            os.unlink(test_file)
        
        # Re-index
        result2 = await indexer.index_folder(temp_content_dir)
        assert result2['removed'] > 0
        
        # Verify file was removed from database
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM files WHERE path LIKE ?",
                (f"%{test_file.name}%",)
            )
            count = cursor.fetchone()[0]
            assert count == 0
            
    finally:
        search_agent.indexer.get_config = original_config


def test_allowed_roots_validation(temp_db):
    """Test that allowed roots validation works."""
    indexer = FileIndexer(temp_db)
    
    # Mock config with restricted roots
    original_config = get_config
    
    def mock_config():
        config = original_config()
        config['allowed_roots'] = ['/allowed/path']
        return config
    
    import search_agent.indexer
    search_agent.indexer.get_config = mock_config
    
    try:
        # Should reject paths not in allowed list
        assert not indexer._is_allowed_root('/forbidden/path')
        assert indexer._is_allowed_root('/allowed/path')
        assert indexer._is_allowed_root('/allowed/path/subdir')
        
    finally:
        search_agent.indexer.get_config = original_config
