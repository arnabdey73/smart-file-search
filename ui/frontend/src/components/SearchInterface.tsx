import React, { useState } from 'react';
import './SearchInterface.css';

interface SearchResult {
  file_path: string;
  snippet: string;
  score: number;
  last_modified?: string;
  file_size?: number;
}

interface SearchInterfaceProps {
  onSearchResults: (results: SearchResult[], aiData?: any) => void;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({ onSearchResults }) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [maxResults, setMaxResults] = useState(10);
  const [fileTypes, setFileTypes] = useState<string[]>([]);
  const [useAI, setUseAI] = useState(false);

  const commonFileTypes = [
    { ext: '.pdf', label: 'PDF' },
    { ext: '.docx', label: 'Word' },
    { ext: '.xlsx', label: 'Excel' },
    { ext: '.pptx', label: 'PowerPoint' },
    { ext: '.txt', label: 'Text' },
    { ext: '.md', label: 'Markdown' },
    { ext: '.html', label: 'HTML' },
    { ext: '.xml', label: 'XML' }
  ];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) return;

    setIsSearching(true);
    
    try {
      const searchParams = {
        query: query.trim(),
        max_results: maxResults,
        file_extensions: fileTypes.length > 0 ? fileTypes : undefined,
        use_ai: useAI
      };

      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchParams),
      });

      const data = await response.json();
      
      if (response.ok) {
        onSearchResults(data.results || [], data.ai_enhancement);
      } else {
        console.error('Search error:', data.detail);
        onSearchResults([]);
      }
    } catch (error) {
      console.error('Error searching:', error);
      onSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleFileType = (ext: string) => {
    setFileTypes(prev => 
      prev.includes(ext) 
        ? prev.filter(t => t !== ext)
        : [...prev, ext]
    );
  };

  return (
    <div className="search-interface">
      <h3>🔍 Search Your Files</h3>
      
      <form onSubmit={handleSearch} className="search-form">
        {/* Main Search Input */}
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for documents, content, or ask a question..."
            className="search-input"
            disabled={isSearching}
          />
          <button 
            type="submit" 
            disabled={!query.trim() || isSearching}
            className="search-button"
          >
            {isSearching ? '⏳' : '🔍'}
          </button>
        </div>

        {/* Search Options */}
        <div className="search-options">
          {/* File Type Filters */}
          <div className="option-group">
            <label>File Types:</label>
            <div className="file-type-chips">
              {commonFileTypes.map((type) => (
                <button
                  key={type.ext}
                  type="button"
                  onClick={() => toggleFileType(type.ext)}
                  className={`file-type-chip ${fileTypes.includes(type.ext) ? 'active' : ''}`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Max Results */}
          <div className="option-group">
            <label htmlFor="max-results">Max Results:</label>
            <select
              id="max-results"
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="max-results-select"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>

          {/* AI Enhancement */}
          <div className="option-group">
            <label className="ai-toggle">
              <input
                type="checkbox"
                checked={useAI}
                onChange={(e) => setUseAI(e.target.checked)}
              />
              🤖 AI-Enhanced Search
              <small>Use AI to improve query understanding and results</small>
            </label>
          </div>
        </div>

        {/* Quick Search Examples */}
        <div className="search-examples">
          <small>Try:</small>
          <button type="button" onClick={() => setQuery('meeting notes from last week')}>
            "meeting notes from last week"
          </button>
          <button type="button" onClick={() => setQuery('budget spreadsheets')}>
            "budget spreadsheets"
          </button>
          <button type="button" onClick={() => setQuery('project proposal')}>
            "project proposal"
          </button>
        </div>
      </form>
    </div>
  );
};

export default SearchInterface;
