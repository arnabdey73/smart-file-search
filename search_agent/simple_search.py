"""Simple and fast search for Windows network folders."""
import sqlite3
from typing import List, Dict, Optional, Tuple
import re
import time
from pathlib import Path

from .config import config

class SimpleFileSearch:
    """Fast search optimized for Windows network folders."""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path or config.database_path)
        
    def search(self, query: str, 
               max_results: int = None,
               file_types: List[str] = None,
               network_paths: List[str] = None,
               modified_after: str = None) -> List[Dict]:
        """
        Simple search with focus on speed and relevance.
        
        Args:
            query: Search terms
            max_results: Maximum results to return
            file_types: Filter by extensions (.pdf, .docx, etc.)
            network_paths: Filter by specific network folders
            modified_after: ISO date string (YYYY-MM-DD)
            
        Returns:
            List of search results with relevance scoring
        """
        if not query or len(query.strip()) < 2:
            return []
            
        max_results = max_results or config.max_results
        
        # Clean and prepare query for FTS5
        clean_query = self._prepare_fts_query(query)
        
        # Build SQL query with filters
        sql_query = """
            SELECT 
                f.path,
                f.name,
                f.extension,
                f.size_bytes,
                f.modified_time,
                f.network_path,
                search_index.content,
                bm25(search_index) as relevance_score
            FROM search_index 
            JOIN files f ON search_index.file_id = f.id
            WHERE search_index MATCH ? AND f.is_accessible = 1
        """
        
        params = [clean_query]
        
        # Add filters
        if file_types:
            placeholders = ','.join('?' * len(file_types))
            sql_query += f" AND f.extension IN ({placeholders})"
            params.extend(file_types)
            
        if network_paths:
            path_conditions = ' OR '.join(['f.network_path = ?' for _ in network_paths])
            sql_query += f" AND ({path_conditions})"
            params.extend(network_paths)
            
        if modified_after:
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(modified_after).timestamp()
                sql_query += " AND f.modified_time > ?"
                params.append(timestamp)
            except ValueError:
                pass  # Skip invalid date
                
        # Order by relevance and limit
        sql_query += " ORDER BY relevance_score DESC LIMIT ?"
        params.append(max_results)
        
        # Execute search
        results = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(sql_query, params)
                
                for row in cursor:
                    # Extract snippet around matching terms
                    snippet = self._extract_snippet(row[6], query)
                    
                    results.append({
                        'path': row[0],
                        'name': row[1],
                        'extension': row[2],
                        'size_bytes': row[3],
                        'modified_time': row[4],
                        'network_path': row[5],
                        'snippet': snippet,
                        'relevance_score': round(row[7], 3),
                        'accessible': True
                    })
                    
        except sqlite3.Error as e:
            print(f"Search error: {e}")
            
        return results
        
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for SQLite FTS5."""
        # Remove special characters that can break FTS5
        clean_query = re.sub(r'[^\w\s.-]', ' ', query)
        
        # Split into terms and handle phrases
        terms = []
        words = clean_query.split()
        
        for word in words:
            if len(word) >= 2:  # Skip very short terms
                # Add wildcard for partial matching
                if len(word) >= 3:
                    terms.append(f"{word}*")
                else:
                    terms.append(word)
                    
        # Join with AND for more precise results
        return ' AND '.join(terms) if terms else query
        
    def _extract_snippet(self, content: str, query: str, 
                        max_length: int = 200) -> str:
        """Extract relevant snippet around search terms."""
        if not content:
            return ""
            
        # Find first occurrence of any query term
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        best_pos = 0
        for term in query_terms:
            pos = content_lower.find(term.lower())
            if pos != -1:
                best_pos = pos
                break
                
        # Extract snippet around the match
        start = max(0, best_pos - 50)
        end = min(len(content), start + max_length)
        
        snippet = content[start:end].strip()
        
        # Highlight search terms (simple version)
        for term in query_terms:
            if len(term) >= 3:  # Only highlight meaningful terms
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                snippet = pattern.sub(f"**{term}**", snippet)
                
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
            
        return snippet
        
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on indexed content."""
        if len(partial_query) < 2:
            return []
            
        suggestions = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get common terms that start with the partial query
                cursor = conn.execute("""
                    SELECT DISTINCT name FROM files 
                    WHERE name LIKE ? 
                    ORDER BY name 
                    LIMIT ?
                """, (f"%{partial_query}%", limit))
                
                suggestions = [row[0] for row in cursor]
                
        except sqlite3.Error:
            pass
            
        return suggestions
        
    def get_search_stats(self) -> Dict[str, any]:
        """Get search index statistics."""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'file_types': {},
            'network_folders': [],
            'last_updated': None
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total files and size
                cursor = conn.execute("""
                    SELECT COUNT(*), SUM(size_bytes), MAX(indexed_time)
                    FROM files WHERE is_accessible = 1
                """)
                row = cursor.fetchone()
                if row:
                    stats['total_files'] = row[0] or 0
                    stats['total_size_mb'] = round((row[1] or 0) / (1024 * 1024), 2)
                    if row[2]:
                        from datetime import datetime
                        stats['last_updated'] = datetime.fromtimestamp(row[2]).isoformat()
                
                # File types
                cursor = conn.execute("""
                    SELECT extension, COUNT(*) 
                    FROM files 
                    WHERE is_accessible = 1 
                    GROUP BY extension 
                    ORDER BY COUNT(*) DESC
                """)
                stats['file_types'] = dict(cursor.fetchall())
                
                # Network folders
                cursor = conn.execute("""
                    SELECT network_path, COUNT(*) 
                    FROM files 
                    WHERE is_accessible = 1 AND network_path IS NOT NULL
                    GROUP BY network_path
                """)
                stats['network_folders'] = [
                    {'path': row[0], 'files': row[1]} 
                    for row in cursor
                ]
                
        except sqlite3.Error:
            pass
            
        return stats
