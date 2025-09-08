"""
File indexing module.
Handles scanning, extracting, and indexing file content into SQLite FTS5.
"""

import os
import sqlite3
import asyncio
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

from .extractor import ContentExtractor
from .config import get_config

logger = logging.getLogger(__name__)


class FileIndexer:
    """Handles file indexing operations with SQLite FTS5."""
    
    def __init__(self, db_path: str = None):
        """Initialize the indexer with database path."""
        self.config = get_config()
        self.db_path = db_path or self.config['database_path']
        self.extractor = ContentExtractor()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Read schema from file
                schema_path = Path(__file__).parent / 'schema.sql'
                with open(schema_path, 'r') as f:
                    schema = f.read()
                
                conn.executescript(schema)
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def index_folder(self, root_path: str, full_reindex: bool = False, 
                          priority: str = "normal") -> Dict[str, Any]:
        """
        Index all files in a folder recursively.
        
        Args:
            root_path: Root directory to index
            full_reindex: Force full reindex ignoring mtime
            priority: Indexing priority (low/normal/high)
            
        Returns:
            Dictionary with indexing statistics
        """
        start_time = time.time()
        stats = {"indexed": 0, "skipped": 0, "removed": 0, "errors": 0}
        
        # Validate root path
        if not self._is_allowed_root(root_path):
            raise ValueError(f"Root path not in allowed list: {root_path}")
        
        if not os.path.exists(root_path):
            raise ValueError(f"Root path does not exist: {root_path}")
        
        logger.info(f"Starting indexing of {root_path} (full={full_reindex}, priority={priority})")
        
        try:
            # Get existing files in database for this root
            existing_files = self._get_existing_files(root_path)
            
            # Scan filesystem
            current_files = set()
            
            for file_path in self._scan_files(root_path):
                current_files.add(file_path)
                
                try:
                    if await self._should_index_file(file_path, existing_files, full_reindex):
                        await self._index_file(file_path)
                        stats["indexed"] += 1
                    else:
                        stats["skipped"] += 1
                        
                    # Add delay for low priority
                    if priority == "low":
                        await asyncio.sleep(0.01)
                        
                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")
                    stats["errors"] += 1
            
            # Remove files that no longer exist
            removed_files = set(existing_files.keys()) - current_files
            for file_path in removed_files:
                self._remove_file_from_index(file_path)
                stats["removed"] += 1
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Indexing completed: {stats}, duration: {duration_ms}ms")
            
            return {**stats, "duration_ms": duration_ms}
            
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise
    
    def _is_allowed_root(self, root_path: str) -> bool:
        """Check if root path is in allowed list."""
        allowed_roots = self.config.get('allowed_roots', [])
        if not allowed_roots:
            return True
        
        abs_root = os.path.abspath(root_path)
        return any(abs_root.startswith(os.path.abspath(allowed)) 
                  for allowed in allowed_roots)
    
    def _get_existing_files(self, root_path: str) -> Dict[str, Tuple[int, float]]:
        """Get existing files from database with size and mtime."""
        existing = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT path, size, mtime FROM files WHERE path LIKE ?",
                    (f"{root_path}%",)
                )
                
                for row in cursor:
                    existing[row[0]] = (row[1], row[2])
                    
        except Exception as e:
            logger.error(f"Error getting existing files: {e}")
            
        return existing
    
    def _scan_files(self, root_path: str) -> List[str]:
        """Scan directory for supported files."""
        supported_extensions = self.config.get('supported_extensions', [])
        max_file_size = self.config.get('max_file_size', 10 * 1024 * 1024)
        
        files = []
        
        for root, dirs, filenames in os.walk(root_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                file_path = os.path.join(root, filename)
                
                # Check extension
                if supported_extensions:
                    ext = Path(filename).suffix.lower()
                    if ext not in supported_extensions:
                        continue
                
                # Check file size
                try:
                    if os.path.getsize(file_path) > max_file_size:
                        logger.debug(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue
                
                files.append(file_path)
        
        return files
    
    async def _should_index_file(self, file_path: str, existing_files: Dict, 
                                full_reindex: bool) -> bool:
        """Check if file should be indexed based on mtime and size."""
        if full_reindex:
            return True
        
        if file_path not in existing_files:
            return True
        
        try:
            stat = os.stat(file_path)
            existing_size, existing_mtime = existing_files[file_path]
            
            # Check if file changed
            if stat.st_size != existing_size or stat.st_mtime != existing_mtime:
                return True
                
        except OSError:
            return True
        
        return False
    
    async def _index_file(self, file_path: str):
        """Index a single file."""
        try:
            stat = os.stat(file_path)
            
            # Extract content
            content_chunks = await self.extractor.extract_content(file_path)
            
            if not content_chunks:
                logger.debug(f"No content extracted from {file_path}")
                return
            
            with sqlite3.connect(self.db_path) as conn:
                # Insert/update file record
                conn.execute("""
                    INSERT OR REPLACE INTO files (path, size, mtime, ext)
                    VALUES (?, ?, ?, ?)
                """, (
                    file_path,
                    stat.st_size,
                    stat.st_mtime,
                    Path(file_path).suffix.lower()
                ))
                
                file_id = conn.lastrowid or conn.execute(
                    "SELECT id FROM files WHERE path = ?", (file_path,)
                ).fetchone()[0]
                
                # Remove old documents for this file
                conn.execute("DELETE FROM docs WHERE file_id = ?", (file_id,))
                
                # Insert new document chunks
                for i, chunk in enumerate(content_chunks):
                    conn.execute("""
                        INSERT INTO docs (file_id, pointer, content)
                        VALUES (?, ?, ?)
                    """, (file_id, f"chunk_{i}", chunk))
                
                conn.commit()
                logger.debug(f"Indexed {file_path} with {len(content_chunks)} chunks")
                
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            raise
    
    def _remove_file_from_index(self, file_path: str):
        """Remove file from index."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get file ID
                cursor = conn.execute("SELECT id FROM files WHERE path = ?", (file_path,))
                row = cursor.fetchone()
                
                if row:
                    file_id = row[0]
                    
                    # Remove documents and file record
                    conn.execute("DELETE FROM docs WHERE file_id = ?", (file_id,))
                    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    conn.commit()
                    
                    logger.debug(f"Removed {file_path} from index")
                    
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")
