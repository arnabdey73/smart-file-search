"""
Search module.
Handles searching indexed content using SQLite FTS5 with optional semantic reranking.
"""

import sqlite3
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Optional semantic search imports
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False

from .config import get_config
from .ai_enhancer import AISearchEnhancer


class SearchEngine:
    """Handles file searching with FTS5 and optional semantic reranking."""
    
    def __init__(self, db_path: str = None):
        """Initialize the search engine."""
        self.config = get_config()
        self.db_path = db_path or self.config['database_path']
        self.semantic_model = None
        
        # Initialize AI enhancer
        self.ai_enhancer = AISearchEnhancer(self.config)
        
        # Initialize semantic model if available and enabled
        if HAS_SEMANTIC and self.config.get('enable_semantic_search', False):
            try:
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic search enabled")
            except Exception as e:
                logger.warning(f"Failed to load semantic model: {e}")
    
    async def search(self, query: str, k: int = 10, offset: int = 0,
                    file_extensions: Optional[List[str]] = None,
                    years: Optional[List[str]] = None,
                    roots: Optional[List[str]] = None,
                    enable_ai: bool = True) -> Dict[str, Any]:
        """
        Search indexed files.
        
        Args:
            query: Search query
            k: Number of results to return
            offset: Results offset for pagination
            file_extensions: Filter by file extensions
            years: Filter by modification years
            roots: Filter by root paths
            enable_ai: Whether to use AI enhancement
            
        Returns:
            Dictionary with search results and pagination info
        """
        try:
            # Enhance query with AI if enabled
            original_query = query
            if enable_ai and self.ai_enhancer.is_available():
                query = self.ai_enhancer.enhance_query(query)
                logger.info(f"AI enhanced query: '{original_query}' -> '{query}'")
            
            # Build FTS query
            fts_query = self._build_fts_query(query)
            
            # Build filters
            where_clauses, params = self._build_filters(
                file_extensions, years, roots
            )
            
            # Execute search
            results = await self._execute_search(
                fts_query, where_clauses, params, k + offset
            )
            
            # Apply semantic reranking if available
            if self.semantic_model and results:
                results = await self._semantic_rerank(query, results)
            
            # Apply pagination
            total_estimate = len(results)
            paginated_results = results[offset:offset + k]
            
            # Generate AI summary if enabled and results exist
            ai_summary = None
            related_queries = []
            if enable_ai and paginated_results and self.ai_enhancer.is_available():
                ai_summary = self.ai_enhancer.summarize_results(original_query, paginated_results)
                related_queries = self.ai_enhancer.suggest_related_queries(original_query, paginated_results)
            
            return {
                "items": [self._format_result(r) for r in paginated_results],
                "pagination": {
                    "offset": offset,
                    "returned": len(paginated_results),
                    "total_estimate": total_estimate
                },
                "ai_enhancement": {
                    "enhanced_query": query if query != original_query else None,
                    "summary": ai_summary,
                    "related_queries": related_queries
                }
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query from user query."""
        # Clean and escape query
        query = query.strip()
        if not query:
            return "*"
        
        # Handle phrases in quotes
        phrases = re.findall(r'"([^"]*)"', query)
        for phrase in phrases:
            query = query.replace(f'"{phrase}"', f'"{phrase}"')
        
        # Remove quotes from remaining text and split into terms
        remaining = re.sub(r'"[^"]*"', '', query)
        terms = [term.strip() for term in remaining.split() if term.strip()]
        
        # Build FTS query
        query_parts = []
        
        # Add phrases
        for phrase in phrases:
            if phrase.strip():
                query_parts.append(f'"{phrase}"')
        
        # Add individual terms with OR
        if terms:
            escaped_terms = []
            for term in terms:
                # Escape FTS special characters
                escaped_term = re.sub(r'[^\w\s]', '', term)
                if escaped_term:
                    escaped_terms.append(escaped_term)
            
            if escaped_terms:
                query_parts.append(' OR '.join(escaped_terms))
        
        return ' '.join(query_parts) if query_parts else query
    
    def _build_filters(self, file_extensions: Optional[List[str]], 
                      years: Optional[List[str]], 
                      roots: Optional[List[str]]) -> tuple:
        """Build WHERE clauses and parameters for filters."""
        where_clauses = []
        params = []
        
        # File extension filter
        if file_extensions:
            placeholders = ','.join('?' * len(file_extensions))
            where_clauses.append(f"f.ext IN ({placeholders})")
            params.extend(file_extensions)
        
        # Year filter (based on modification time)
        if years:
            year_conditions = []
            for year in years:
                try:
                    year_int = int(year)
                    # Unix timestamp for start and end of year
                    start_ts = int(f"{year_int}0101000000")  # Simplified
                    end_ts = int(f"{year_int}1231235959")
                    year_conditions.append("(f.mtime >= ? AND f.mtime <= ?)")
                    params.extend([start_ts, end_ts])
                except ValueError:
                    continue
            
            if year_conditions:
                where_clauses.append(f"({' OR '.join(year_conditions)})")
        
        # Root path filter
        if roots:
            root_conditions = []
            for root in roots:
                root_conditions.append("f.path LIKE ?")
                params.append(f"{root}%")
            
            if root_conditions:
                where_clauses.append(f"({' OR '.join(root_conditions)})")
        
        return where_clauses, params
    
    async def _execute_search(self, fts_query: str, where_clauses: List[str],
                             params: List[Any], limit: int) -> List[Dict]:
        """Execute the search query against the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build SQL query
                sql = """
                    SELECT 
                        f.path,
                        d.pointer,
                        snippet(docs, 2, '<mark>', '</mark>', '...', 64) as snippet,
                        rank as score,
                        f.ext,
                        f.mtime
                    FROM docs d
                    JOIN files f ON d.file_id = f.id
                    WHERE docs MATCH ?
                """
                
                query_params = [fts_query]
                
                # Add filter clauses
                if where_clauses:
                    sql += " AND " + " AND ".join(where_clauses)
                    query_params.extend(params)
                
                sql += " ORDER BY rank LIMIT ?"
                query_params.append(limit)
                
                cursor = conn.execute(sql, query_params)
                
                results = []
                for row in cursor:
                    results.append({
                        'path': row[0],
                        'pointer': row[1],
                        'snippet': row[2],
                        'score': row[3],
                        'ext': row[4],
                        'modified': row[5]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            raise
    
    async def _semantic_rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        """Rerank results using semantic similarity."""
        if not self.semantic_model or len(results) <= 1:
            return results
        
        try:
            # Extract snippets for embedding
            snippets = [r['snippet'] for r in results]
            
            # Generate embeddings
            query_embedding = self.semantic_model.encode([query])
            snippet_embeddings = self.semantic_model.encode(snippets)
            
            # Calculate similarities
            similarities = np.dot(query_embedding, snippet_embeddings.T)[0]
            
            # Combine FTS score with semantic similarity
            for i, result in enumerate(results):
                fts_score = float(result['score'])
                semantic_score = float(similarities[i])
                
                # Weighted combination (adjust weights as needed)
                combined_score = 0.7 * fts_score + 0.3 * semantic_score
                result['score'] = combined_score
            
            # Re-sort by combined score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            logger.debug(f"Semantic reranking applied to {len(results)} results")
            
        except Exception as e:
            logger.warning(f"Semantic reranking failed: {e}")
        
        return results
    
    def _format_result(self, result: Dict) -> Dict:
        """Format search result for API response."""
        return {
            'path': result['path'],
            'pointer': result['pointer'],
            'snippet': result['snippet'],
            'score': float(result['score']),
            'ext': result['ext'],
            'modified': result['modified']
        }
    
    async def get_file_preview(self, file_path: str, pointer: Optional[str] = None,
                              before: int = 200, after: int = 200) -> Dict[str, Any]:
        """
        Get file preview with context around the matched content.
        
        Args:
            file_path: Path to the file
            pointer: Document pointer (chunk identifier)
            before: Characters before the match
            after: Characters after the match
            
        Returns:
            Dictionary with preview information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if pointer:
                    # Get specific document chunk
                    cursor = conn.execute("""
                        SELECT d.content, f.path, f.size
                        FROM docs d
                        JOIN files f ON d.file_id = f.id
                        WHERE f.path = ? AND d.pointer = ?
                    """, (file_path, pointer))
                else:
                    # Get first chunk
                    cursor = conn.execute("""
                        SELECT d.content, f.path, f.size
                        FROM docs d
                        JOIN files f ON d.file_id = f.id
                        WHERE f.path = ?
                        ORDER BY d.rowid
                        LIMIT 1
                    """, (file_path,))
                
                row = cursor.fetchone()
                
                if not row:
                    raise ValueError(f"File not found in index: {file_path}")
                
                content = row[0]
                file_size = row[2]
                
                # Apply before/after limits
                if len(content) > before + after:
                    start = max(0, len(content) // 2 - before // 2)
                    end = min(len(content), start + before + after)
                    preview = content[start:end]
                    truncated = True
                else:
                    preview = content
                    truncated = False
                
                return {
                    'path': file_path,
                    'pointer': pointer,
                    'preview': preview,
                    'truncated': truncated,
                    'file_size': file_size
                }
                
        except Exception as e:
            logger.error(f"Error getting file preview: {e}")
            raise
