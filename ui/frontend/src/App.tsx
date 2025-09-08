import React, { useState, useEffect } from 'react';
import NetworkFolderInput from './components/NetworkFolderInput';
import SearchInterface from './components/SearchInterface';
import './App.css';

interface SearchResult {
  file_path: string;
  snippet: string;
  score: number;
  last_modified?: string;
  file_size?: number;
}

const App: React.FC = () => {
  const [hasIndexedFolders, setHasIndexedFolders] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [aiEnhancement, setAiEnhancement] = useState<any>(null);

  // Check for indexed folders on component mount
  useEffect(() => {
    checkIndexedFolders();
  }, []);

  const checkIndexedFolders = async () => {
    try {
      const response = await fetch('/api/network-folders');
      const data = await response.json();
      setHasIndexedFolders(data.folders && data.folders.length > 0);
    } catch (error) {
      console.error('Error checking indexed folders:', error);
    }
  };

  const handleFolderIndexed = (folderPath: string) => {
    setHasIndexedFolders(true);
    console.log('Folder indexed:', folderPath);
  };

  const handleSearchResults = (results: SearchResult[], aiData?: any) => {
    setSearchResults(results);
    setAiEnhancement(aiData);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 Smart File Search</h1>
        <p>Search across Windows network folders with AI-powered insights</p>
        <p className="deployment-info">Web-hosted application • No installation required</p>
      </header>

      <main className="app-main">
        {/* Network Folder Configuration */}
        <section className="folder-section">
          <NetworkFolderInput onFolderIndexed={handleFolderIndexed} />
        </section>

        {/* Search Interface */}
        {hasIndexedFolders && (
          <section className="search-section">
            <SearchInterface 
              onSearchResults={handleSearchResults}
            />
          </section>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <section className="results-section">
            <h3>📋 Search Results</h3>
            <div className="results-list">
              {searchResults.map((result, index) => (
                <div key={index} className="result-item">
                  <div className="result-header">
                    <h4>{result.file_path.split('\\').pop()}</h4>
                    <span className="result-score">Score: {result.score.toFixed(2)}</span>
                  </div>
                  <div className="result-path">
                    <code>{result.file_path}</code>
                  </div>
                  <div className="result-snippet">
                    {result.snippet}
                  </div>
                  {(result.last_modified || result.file_size) && (
                    <div className="result-meta">
                      {result.last_modified && (
                        <span>Modified: {new Date(result.last_modified).toLocaleDateString()}</span>
                      )}
                      {result.file_size && (
                        <span>Size: {(result.file_size / 1024 / 1024).toFixed(2)} MB</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* AI Enhancement Results */}
        {aiEnhancement && (
          <section className="ai-enhancement-section">
            {aiEnhancement.enhanced_query && (
              <div className="enhanced-query">
                <h4>🤖 AI Enhanced Query</h4>
                <p>Original: <em>{aiEnhancement.original_query}</em></p>
                <p>Enhanced: <strong>{aiEnhancement.enhanced_query}</strong></p>
              </div>
            )}
            
            {aiEnhancement.summary && (
              <div className="ai-summary">
                <h4>📄 AI Summary</h4>
                <div className="summary-content" dangerouslySetInnerHTML={{ __html: aiEnhancement.summary }} />
              </div>
            )}
            
            {aiEnhancement.related_queries && aiEnhancement.related_queries.length > 0 && (
              <div className="related-queries">
                <h4>🔗 Related Searches</h4>
                <div className="query-suggestions">
                  {aiEnhancement.related_queries.map((query: string, index: number) => (
                    <button key={index} className="query-suggestion" onClick={() => {
                      // This would trigger a new search with the suggested query
                      console.log('Suggested query clicked:', query);
                    }}>
                      {query}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Empty State */}
        {!hasIndexedFolders && (
          <section className="empty-state">
            <div className="empty-content">
              <h3>🚀 Get Started</h3>
              <p>Add a Windows network folder above to start searching through your files.</p>
              <ul>
                <li>Enter a UNC path like <code>\\\\server\\share</code></li>
                <li>Wait for folder validation and indexing</li>
                <li>Start searching with natural language queries</li>
              </ul>
            </div>
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>Smart File Search v1.0 • Windows Network Folder Support</p>
      </footer>
    </div>
  );
};

export default App;
