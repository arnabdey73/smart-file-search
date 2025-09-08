import React, { useState, useEffect } from 'react';
import './NetworkFolderInput.css';

interface NetworkFolder {
  path: string;
  file_count: number;
  last_indexed: string | null;
  total_size_mb: number;
  accessible: boolean;
}

interface NetworkFolderInputProps {
  onFolderIndexed: (folder: string) => void;
}

const NetworkFolderInput: React.FC<NetworkFolderInputProps> = ({ onFolderIndexed }) => {
  const [networkPath, setNetworkPath] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [pathValidation, setPathValidation] = useState<any>(null);
  const [indexedFolders, setIndexedFolders] = useState<NetworkFolder[]>([]);
  const [quickScan, setQuickScan] = useState(true);

  // Load indexed folders on component mount
  useEffect(() => {
    loadIndexedFolders();
  }, []);

  const loadIndexedFolders = async () => {
    try {
      const response = await fetch('/api/network-folders');
      const data = await response.json();
      setIndexedFolders(data.folders || []);
    } catch (error) {
      console.error('Error loading indexed folders:', error);
    }
  };

  const validateNetworkPath = async (path: string) => {
    if (!path.trim()) {
      setPathValidation(null);
      return;
    }

    setIsValidating(true);
    try {
      const response = await fetch('/api/validate-path', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: path.trim() }),
      });

      const validation = await response.json();
      setPathValidation(validation);
    } catch (error) {
      console.error('Error validating path:', error);
      setPathValidation({
        accessible: false,
        error: 'Failed to validate path'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handlePathChange = (value: string) => {
    setNetworkPath(value);
    // Debounce validation
    setTimeout(() => validateNetworkPath(value), 500);
  };

  const handleIndexFolder = async () => {
    if (!pathValidation?.accessible) return;

    setIsIndexing(true);
    try {
      const response = await fetch('/api/index', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          network_path: networkPath.trim(),
          quick_scan: quickScan
        }),
      });

      const result = await response.json();
      
      if (response.ok) {
        // Success
        onFolderIndexed(networkPath.trim());
        loadIndexedFolders(); // Refresh the list
        setNetworkPath(''); // Clear input
        setPathValidation(null);
      } else {
        console.error('Indexing error:', result.detail);
      }
    } catch (error) {
      console.error('Error indexing folder:', error);
    } finally {
      setIsIndexing(false);
    }
  };

  const getValidationIcon = () => {
    if (isValidating) return '⏳';
    if (!pathValidation) return '';
    if (pathValidation.accessible) return '✅';
    return '❌';
  };

  const getValidationMessage = () => {
    if (isValidating) return 'Validating path...';
    if (!pathValidation) return '';
    if (pathValidation.accessible) {
      return `✓ Accessible (${pathValidation.file_count || 0} files)`;
    }
    return `✗ ${pathValidation.error || 'Not accessible'}`;
  };

  return (
    <div className="network-folder-input">
      <h3>🗂️ Windows Network Folder Search</h3>
      
      {/* Network Path Input */}
      <div className="input-section">
        <label htmlFor="network-path">Network Folder Path:</label>
        <div className="path-input-container">
          <input
            id="network-path"
            type="text"
            value={networkPath}
            onChange={(e) => handlePathChange(e.target.value)}
            placeholder="\\\\server\\share\\folder"
            className={`path-input ${pathValidation?.accessible ? 'valid' : pathValidation ? 'invalid' : ''}`}
          />
          <span className="validation-icon">{getValidationIcon()}</span>
        </div>
        <div className="validation-message">
          {getValidationMessage()}
        </div>
        
        {/* Example paths */}
        <div className="example-paths">
          <small>Examples:</small>
          <ul>
            <li><code>\\\\fileserver\\documents</code></li>
            <li><code>\\\\nas\\projects\\active</code></li>
            <li><code>C:\\Shared\\Folders</code></li>
          </ul>
        </div>
      </div>

      {/* Scan Options */}
      <div className="scan-options">
        <label>
          <input
            type="checkbox"
            checked={quickScan}
            onChange={(e) => setQuickScan(e.target.checked)}
          />
          Quick scan (only index new/modified files)
        </label>
      </div>

      {/* Index Button */}
      <button
        onClick={handleIndexFolder}
        disabled={!pathValidation?.accessible || isIndexing}
        className="index-button"
      >
        {isIndexing ? '⏳ Indexing...' : '📁 Index Folder'}
      </button>

      {/* Indexed Folders List */}
      {indexedFolders.length > 0 && (
        <div className="indexed-folders">
          <h4>📚 Indexed Network Folders</h4>
          <div className="folders-list">
            {indexedFolders.map((folder, index) => (
              <div key={index} className={`folder-item ${folder.accessible ? 'accessible' : 'inaccessible'}`}>
                <div className="folder-path">
                  <span className="status-icon">{folder.accessible ? '🟢' : '🔴'}</span>
                  <code>{folder.path}</code>
                </div>
                <div className="folder-stats">
                  <span>{folder.file_count} files</span>
                  <span>{folder.total_size_mb} MB</span>
                  {folder.last_indexed && (
                    <span>Updated: {new Date(folder.last_indexed).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NetworkFolderInput;
