"""Fast indexer for Windows network folders."""
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
import hashlib
from datetime import datetime
import logging

from .config import config
from .extractor import ContentExtractor

logger = logging.getLogger(__name__)

class NetworkFolderIndexer:
    """Fast indexer optimized for Windows network folders."""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path or config.database_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.extractor = ContentExtractor()
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with FTS5 for fast search."""
        with sqlite3.connect(self.db_path) as conn:
            # Files table with Windows-specific fields
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    extension TEXT,
                    size_bytes INTEGER,
                    modified_time REAL,
                    indexed_time REAL,
                    file_hash TEXT,
                    network_path TEXT,  -- Track which network share
                    is_accessible INTEGER DEFAULT 1
                )
            """)
            
            # Simple FTS5 table for fast text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    file_id,
                    content,
                    content='',
                    contentless_delete=1
                )
            """)
            
            # Index for fast lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_time)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_network ON files(network_path)
            """)
            
    def index_network_folder(self, network_path: str, quick_scan: bool = True) -> Dict[str, int]:
        """
        Index a Windows network folder with focus on speed.
        
        Args:
            network_path: UNC path like \\\\server\\share\\folder
            quick_scan: If True, only index modified files
            
        Returns:
            Statistics dict with counts
        """
        start_time = time.time()
        stats = {'indexed': 0, 'skipped': 0, 'errors': 0, 'updated': 0}
        
        # Add to allowed paths if not already there
        config.add_network_path(network_path)
        
        # Normalize Windows path
        network_path = os.path.normpath(network_path)
        
        logger.info(f"Starting {'quick' if quick_scan else 'full'} scan of {network_path}")
        
        try:
            # Check if network path is accessible
            if not os.path.exists(network_path):
                logger.error(f"Network path not accessible: {network_path}")
                return stats
                
            # Get existing files for quick scan comparison
            existing_files = {}
            if quick_scan:
                existing_files = self._get_existing_files(network_path)
                
            # Walk through network folder
            for root, dirs, files in os.walk(network_path):
                # Skip hidden and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$')]
                
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        
                        # Skip if file extension not supported
                        ext = Path(file).suffix.lower()
                        if ext not in config.supported_extensions:
                            stats['skipped'] += 1
                            continue
                            
                        # Get file info
                        try:
                            stat_info = os.stat(file_path)
                            file_size = stat_info.st_size
                            modified_time = stat_info.st_mtime
                        except (OSError, PermissionError):
                            stats['errors'] += 1
                            continue
                            
                        # Skip large files for speed
                        if file_size > config.max_file_size_mb * 1024 * 1024:
                            stats['skipped'] += 1
                            continue
                            
                        # Quick scan: skip if file hasn't changed
                        if quick_scan and file_path in existing_files:
                            if existing_files[file_path]['modified_time'] == modified_time:
                                stats['skipped'] += 1
                                continue
                                
                        # Extract content
                        content = self.extractor.extract_text(file_path)
                        if not content or len(content.strip()) < 10:
                            stats['skipped'] += 1
                            continue
                            
                        # Store in database
                        self._store_file(file_path, file, ext, file_size, 
                                       modified_time, content, network_path)
                        
                        if file_path in existing_files:
                            stats['updated'] += 1
                        else:
                            stats['indexed'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        stats['errors'] += 1
                        
        except Exception as e:
            logger.error(f"Error scanning network folder: {e}")
            stats['errors'] += 1
            
        # Cleanup: remove files that no longer exist
        if quick_scan:
            removed = self._cleanup_missing_files(network_path)
            stats['removed'] = removed
            
        duration = time.time() - start_time
        logger.info(f"Indexing completed in {duration:.2f}s: {stats}")
        
        return stats
        
    def _get_existing_files(self, network_path: str) -> Dict[str, Dict]:
        """Get existing files from database for quick comparison."""
        existing = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT path, modified_time, size_bytes 
                FROM files 
                WHERE network_path = ? OR path LIKE ?
            """, (network_path, f"{network_path}%"))
            
            for row in cursor:
                existing[row[0]] = {
                    'modified_time': row[1],
                    'size_bytes': row[2]
                }
        return existing
        
    def _store_file(self, file_path: str, name: str, extension: str, 
                   size: int, modified_time: float, content: str, network_path: str):
        """Store file and content in database."""
        # Create file hash for duplicate detection
        file_hash = hashlib.md5(f"{file_path}{size}{modified_time}".encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert or update file record
            cursor = conn.execute("""
                INSERT OR REPLACE INTO files 
                (path, name, extension, size_bytes, modified_time, indexed_time, 
                 file_hash, network_path, is_accessible)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (file_path, name, extension, size, modified_time, 
                  time.time(), file_hash, network_path))
            
            file_id = cursor.lastrowid
            
            # Update search index
            conn.execute("DELETE FROM search_index WHERE file_id = ?", (file_id,))
            conn.execute("""
                INSERT INTO search_index (file_id, content) 
                VALUES (?, ?)
            """, (file_id, content))
            
    def _cleanup_missing_files(self, network_path: str) -> int:
        """Remove files from index that no longer exist on network."""
        removed = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, path FROM files 
                WHERE network_path = ? OR path LIKE ?
            """, (network_path, f"{network_path}%"))
            
            for file_id, file_path in cursor:
                if not os.path.exists(file_path):
                    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    conn.execute("DELETE FROM search_index WHERE file_id = ?", (file_id,))
                    removed += 1
                    
        return removed
        
    def get_network_folders(self) -> List[Dict[str, any]]:
        """Get list of indexed network folders with stats."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT network_path, COUNT(*) as file_count,
                       MAX(indexed_time) as last_indexed,
                       SUM(size_bytes) as total_size
                FROM files 
                WHERE network_path IS NOT NULL 
                GROUP BY network_path
                ORDER BY last_indexed DESC
            """)
            
            folders = []
            for row in cursor:
                folders.append({
                    'path': row[0],
                    'file_count': row[1],
                    'last_indexed': datetime.fromtimestamp(row[2]).isoformat() if row[2] else None,
                    'total_size_mb': round(row[3] / (1024 * 1024), 2) if row[3] else 0
                })
                
        return folders
